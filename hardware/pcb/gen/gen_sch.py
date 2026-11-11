"""Generate handheld/handheld.kicad_sch (+ .kicad_pro, project symbol library and
library tables) from design.py.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" gen_sch.py

Style: every pin gets a short wire stub and a net label (global label when the
net is used in more than one functional block, local label otherwise, a GND
power symbol for GND).  Nothing is routed with long wires.
"""
import json
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402

KICAD_SYMBOLS = os.environ.get("KICAD9_SYMBOL_DIR", r"C:\Program Files\KiCad\9.0\share\kicad\symbols")
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "handheld"))
PROJECT = design.PROJECT
NS = uuid.UUID("6f0e3a52-5d0b-4d0f-9a55-68616e646865")
G = 1.27  # schematic grid


def uid(key):
    return str(uuid.uuid5(NS, key))


ROOT_UUID = uid("root-sheet")


# ------------------------------------------------------------ s-expressions --
_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()"]+')


def parse(text):
    stack = [[]]
    for tok in _TOKEN.findall(text):
        if tok == "(":
            new = []
            stack[-1].append(new)
            stack.append(new)
        elif tok == ")":
            stack.pop()
        else:
            stack[-1].append(tok)
    return stack[0][0]


def dump(node, ind=0):
    if isinstance(node, str):
        return node
    if all(isinstance(c, str) for c in node):
        return "(" + " ".join(node) + ")"
    pad = "\t" * (ind + 1)
    i = 0
    while i < len(node) and isinstance(node[i], str):
        i += 1
    out = "(" + " ".join(node[:i])
    for c in node[i:]:
        out += "\n" + pad + dump(c, ind + 1)
    return out + "\n" + "\t" * ind + ")"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def unq(tok):
    if tok.startswith('"'):
        return tok[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return tok


def child(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def num(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------ library symbols --
_lib_text = {}


def _find_block(text, start):
    depth, i, in_str = 0, start, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    raise ValueError("unbalanced")


def _raw_symbol(lib, name):
    if lib not in _lib_text:
        with open(os.path.join(KICAD_SYMBOLS, lib + ".kicad_sym"), encoding="utf-8") as f:
            _lib_text[lib] = f.read()
    text = _lib_text[lib]
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + '"', text)
    if not m:
        raise KeyError("%s:%s not found" % (lib, name))
    return parse(_find_block(text, m.start() + 2))


def kicad_symbol(lib, name):
    """Library symbol with `extends` resolved; top-level name is the bare name."""
    sym = _raw_symbol(lib, name)
    ext = child(sym, "extends")
    if ext is None:
        return sym
    pname = unq(ext[1])
    parent = kicad_symbol(lib, pname)
    out = ["symbol", q(name)]
    for c in parent[2:]:
        if isinstance(c, list) and c[0] in ("property", "symbol"):
            continue
        out.append(c)
    out += children(sym, "property")
    for sub in children(parent, "symbol"):
        sub = list(sub)
        sub[1] = q(name + unq(sub[1])[len(pname):])
        out.append(sub)
    return out


def renamed(sym, new_name, props=None):
    old = unq(sym[1])
    out = ["symbol", q(new_name)]
    for c in sym[2:]:
        if isinstance(c, list) and c[0] == "symbol":
            c = list(c)
            c[1] = q(new_name + unq(c[1])[len(old):])
        elif isinstance(c, list) and c[0] == "property" and props and unq(c[1]) in props:
            c = list(c)
            c[2] = q(props[unq(c[1])])
        out.append(c)
    return out


_FONT = "(effects (font (size 1.27 1.27)))"


def _prop(name, value, x, y, hide=False, justify=None):
    eff = "(effects (font (size 1.27 1.27))%s%s)" % (
        " (justify %s)" % justify if justify else "", " (hide yes)" if hide else "")
    return "(property %s %s (at %s %s 0) %s)" % (q(name), q(value), num(x), num(y), eff)


def box_symbol(name, ref, footprint, desc, half_w, top, bottom, pins):
    """Simple rectangular symbol.  pins: (number, name, type, side, coordinate)."""
    s = ['(symbol %s (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)' % q(name)]
    s.append(_prop("Reference", ref, -half_w, top + 1.27, justify="left"))
    s.append(_prop("Value", name, -half_w + 5.08, top + 1.27, justify="left"))
    s.append(_prop("Footprint", footprint, 0, 0, hide=True))
    s.append(_prop("Datasheet", "", 0, 0, hide=True))
    s.append(_prop("Description", desc, 0, 0, hide=True))
    s.append('(symbol %s (rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) '
             '(fill (type background))))' % (q(name + "_0_1"), num(-half_w), num(top), num(half_w), num(bottom)))
    s.append('(symbol %s' % q(name + "_1_1"))
    for number, pname, ptype, side, c in pins:
        if side == "L":
            at = (-half_w - 2.54, c, 0)
        elif side == "R":
            at = (half_w + 2.54, c, 180)
        elif side == "B":
            at = (c, bottom - 2.54, 90)
        else:
            at = (c, top + 2.54, 270)
        s.append('(pin %s line (at %s %s %d) (length 2.54) (name %s %s) (number %s %s))' % (
            ptype, num(at[0]), num(at[1]), at[2], q(pname), _FONT, q(number), _FONT))
    s.append('))')
    return parse("\n".join(s))


def custom_symbols():
    """Symbols of the project library 'handheld' (bare names)."""
    syms = {}
    syms["TPS63020DSJ"] = box_symbol(
        "TPS63020DSJ", "U", "handheld:TPS63020_DSJ",
        "TPS63020 4 A switch buck-boost converter, adjustable, VSON-14 (DSJ)", 10.16, 10.16, -15.24, [
            ("10", "VIN", "power_in", "L", 7.62), ("11", "VIN", "power_in", "L", 5.08),
            ("1", "VINA", "power_in", "L", 2.54), ("12", "EN", "input", "L", -2.54),
            ("13", "PS/SYNC", "input", "L", -7.62),
            ("8", "L1", "passive", "R", 7.62), ("9", "L1", "passive", "R", 5.08),
            ("6", "L2", "passive", "R", 2.54), ("7", "L2", "passive", "R", 0),
            ("4", "VOUT", "power_out", "R", -2.54), ("5", "VOUT", "passive", "R", -5.08),
            ("3", "FB", "input", "R", -7.62), ("14", "PG", "open_collector", "R", -10.16),
            ("2", "GND", "power_in", "B", -2.54), ("15", "PGND", "power_in", "B", 2.54),
        ])
    syms["MAX17048"] = box_symbol(
        "MAX17048", "U", "Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm",
        "MAX17048 1-cell ModelGauge fuel gauge, I2C, TDFN-8", 7.62, 7.62, -10.16, [
            ("3", "VDD", "power_in", "L", 5.08), ("2", "CELL", "passive", "L", 2.54),
            ("6", "QSTRT", "input", "L", -2.54), ("1", "CTG", "passive", "L", -5.08),
            ("8", "SDA", "bidirectional", "R", 5.08), ("7", "SCL", "input", "R", 2.54),
            ("5", "~{ALRT}", "open_collector", "R", -2.54),
            ("4", "GND", "power_in", "B", -2.54), ("9", "EP", "passive", "B", 2.54),
        ])
    syms["Q_8205_Dual_NMOS"] = box_symbol(
        "Q_8205_Dual_NMOS", "Q", "Package_TO_SOT_SMD:SOT-23-6",
        "8205-type dual N-MOSFET, common drain, SOT-23-6 (1 S1, 2 D12, 3 S2, 4 G2, 5 D12, 6 G1)",
        7.62, 7.62, -7.62, [
            ("6", "G1", "input", "L", 5.08), ("4", "G2", "input", "L", -5.08),
            ("1", "S1", "passive", "R", 5.08), ("2", "D12", "passive", "R", 2.54),
            ("5", "D12", "passive", "R", -2.54), ("3", "S2", "passive", "R", -5.08),
        ])
    # single BAT54 in SOT-23 has the same pinout as the library BAT54W (SOT-323)
    syms["BAT54"] = renamed(kicad_symbol("Diode", "BAT54W"), "BAT54", {
        "Value": "BAT54", "Footprint": "Package_TO_SOT_SMD:SOT-23",
        "Description": "BAT54 single Schottky diode, SOT-23 (1 A, 2 NC, 3 K)"})
    return syms


_CUSTOM = None
_sym_cache = {}


def get_symbol(lib_id):
    """Parsed symbol named by its bare name, plus derived geometry."""
    global _CUSTOM
    if lib_id in _sym_cache:
        return _sym_cache[lib_id]
    lib, name = lib_id.split(":")
    if lib == "handheld":
        if _CUSTOM is None:
            _CUSTOM = custom_symbols()
        sym = _CUSTOM[name]
    else:
        sym = kicad_symbol(lib, name)
    pins, box = [], [1e9, 1e9, -1e9, -1e9]

    def grow(x, y):
        box[0], box[1] = min(box[0], x), min(box[1], y)
        box[2], box[3] = max(box[2], x), max(box[3], y)

    for sub in children(sym, "symbol"):
        for item in sub[2:]:
            if not isinstance(item, list):
                continue
            if item[0] == "pin":
                at = child(item, "at")
                hide = child(item, "hide")
                hidden = "hide" in item or (hide is not None and hide[1] == "yes")
                pins.append({
                    "type": item[1], "x": float(at[1]), "y": float(at[2]), "a": int(float(at[3])),
                    "len": float(child(item, "length")[1]), "hidden": hidden,
                    "name": unq(child(item, "name")[1]), "number": unq(child(item, "number")[1]),
                })
            elif item[0] == "circle":
                c, r = child(item, "center"), float(child(item, "radius")[1])
                grow(float(c[1]) - r, float(c[2]) - r)
                grow(float(c[1]) + r, float(c[2]) + r)
            else:
                for key in ("start", "end", "mid"):
                    c = child(item, key)
                    if c is not None:
                        grow(float(c[1]), float(c[2]))
                pts = child(item, "pts")
                if pts is not None:
                    for xy in children(pts, "xy"):
                        grow(float(xy[1]), float(xy[2]))
    if box[0] > box[2]:
        box = [-1.27, -1.27, 1.27, 1.27]
    props = {}
    for p in children(sym, "property"):
        at = child(p, "at")
        eff = child(p, "effects")
        just = child(eff, "justify") if eff else None
        props[unq(p[1])] = {"value": unq(p[2]), "x": float(at[1]), "y": float(at[2]),
                            "justify": just[1:] if just else []}
    info = {"sym": sym, "pins": pins, "box": box, "props": props}
    _sym_cache[lib_id] = info
    return info


# ------------------------------------------------------------------ geometry --
def tx(px, py, rot):
    """Symbol (y up) -> sheet offset (y down) for a symbol rotated by rot."""
    sx, sy = px, -py
    if rot == 0:
        return sx, sy
    if rot == 90:
        return sy, -sx
    if rot == 180:
        return -sx, -sy
    return -sy, sx


def snap(v, g=G):
    return round(round(v / g) * g, 4)


def text_w(s, size=1.27):
    return len(s) * size * 0.84 + 0.4


# ------------------------------------------------------------------- builder --
class Sheet:
    def __init__(self):
        self.items = []       # s-expression strings
        self.boxes = []       # (x0, y0, x1, y1, kind, owner, text)
        self.used = []        # lib ids, in order of first use
        self.npwr = 0
        self.nflg = 0
        self.local = {}       # net -> True if local label

    # --- low level ---------------------------------------------------------
    def box(self, x0, y0, x1, y1, kind, owner, text=""):
        self.boxes.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), kind, owner, text))

    def use(self, lib_id):
        if lib_id not in self.used:
            self.used.append(lib_id)
        return get_symbol(lib_id)

    def wire(self, x1, y1, x2, y2, owner):
        self.items.append("(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))" % (
            num(x1), num(y1), num(x2), num(y2), q(uid("w%s,%s,%s,%s" % (num(x1), num(y1), num(x2), num(y2))))))
        self.box(x1 - 0.1, y1 - 0.1, x2 + 0.1, y2 + 0.1, "stub", owner)

    def no_connect(self, x, y):
        self.items.append("(no_connect (at %s %s) (uuid %s))" % (num(x), num(y), q(uid("nc%s,%s" % (num(x), num(y))))))

    def text(self, s, x, y, size=1.27, bold=False):
        self.items.append("(text %s (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) "
                          "(justify left bottom)) (uuid %s))" % (
                              q(s), num(x), num(y), num(size), num(size), " (bold yes)" if bold else "",
                              q(uid("t" + s + num(x) + num(y)))))
        self.box(x, y - size * 1.3, x + text_w(s, size) * (1.1 if bold else 1), y, "text", "text:" + s, s)

    def rect(self, x0, y0, x1, y1):
        self.items.append("(rectangle (start %s %s) (end %s %s) (stroke (width 0.2) (type dash)) "
                          "(fill (type none)) (uuid %s))" % (num(x0), num(y0), num(x1), num(y1),
                                                             q(uid("r%s,%s" % (num(x0), num(y0))))))

    def symbol(self, lib_id, ref, value, x, y, rot, fields, ref_pos, val_pos, in_bom=True,
               hide_ref=False, hide_val=False):
        """ref_pos / val_pos: (x, y, justify or None) absolute, text drawn horizontally."""
        info = self.use(lib_id)
        ang = 90 if rot in (90, 270) else 0   # field angle is relative to the symbol
        s = ["(symbol (lib_id %s) (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp no)" % (
            q(lib_id), num(x), num(y), rot, "yes" if in_bom else "no")]
        s.append("(uuid %s)" % q(uid("sym" + ref)))

        def prop(name, val, pos, hide):
            px, py, just = pos
            eff = "(effects (font (size 1.27 1.27))%s%s)" % (
                " (justify %s)" % just if just else "", " (hide yes)" if hide else "")
            s.append("(property %s %s (at %s %s %d) %s)" % (q(name), q(val), num(px), num(py), ang, eff))
            if not hide:
                w = text_w(val)
                x0 = px if just == "left" else (px - w if just == "right" else px - w / 2)
                self.box(x0, py - 0.8, x0 + w, py + 0.8, "field", ref, val)

        prop("Reference", ref, ref_pos, hide_ref)
        prop("Value", value, val_pos, hide_val)
        for name, val in fields:
            prop(name, val, (x, y, None), True)
        numbers = []
        for p in info["pins"]:
            if p["number"] not in numbers:
                numbers.append(p["number"])
        for n in numbers:
            s.append("(pin %s (uuid %s))" % (q(n), q(uid("pin" + ref + ":" + n))))
        s.append("(instances (project %s (path %s (reference %s) (unit 1)))))" % (
            q(PROJECT), q("/" + ROOT_UUID), q(ref)))
        self.items.append("\n".join(s))
        b = info["box"]
        c = [tx(b[0], b[1], rot), tx(b[2], b[3], rot)]
        self.box(x + c[0][0], y + c[0][1], x + c[1][0], y + c[1][1], "body", ref)
        return info

    # --- net attachment ----------------------------------------------------
    def attach(self, net, x, y, d, owner):
        """Put the marker for `net` at (x, y); d = unit vector pointing away from the pin."""
        if net == "GND":
            self.npwr += 1
            ref = "#PWR%03d" % self.npwr
            rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
            self.symbol("power:GND", ref, "GND", x, y, rot, [], (x, y, None), (x, y, None),
                        in_bom=False, hide_ref=True, hide_val=True)
            self.boxes.pop()  # replace body box by a fixed-size one
            self.box(x - 1.2 + 1.3 * d[0], y - 1.2 + 1.3 * d[1], x + 1.2 + 1.3 * d[0], y + 1.2 + 1.3 * d[1],
                     "label", owner, "GND")
            return
        ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[d]
        just = "left" if ang in (0, 90) else "right"
        if self.local.get(net, False):
            self.items.append("(label %s (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))" % (
                q(net), num(x), num(y), ang, just, q(uid("lab%s@%s,%s" % (net, num(x), num(y))))))
            ln, h0, h1 = text_w(net) + 0.3, -1.6, 0.0
        else:
            self.items.append("(global_label %s (shape passive) (at %s %s %d) (effects (font (size 1.27 1.27)) "
                              "(justify %s)) (uuid %s))" % (
                                  q(net), num(x), num(y), ang, just, q(uid("glab%s@%s,%s" % (net, num(x), num(y))))))
            ln, h0, h1 = text_w(net) + 2.6, -1.15, 1.15
        if d[0]:
            self.box(x, y + h0, x + d[0] * ln, y + h1, "label", owner, net)
        else:
            # vertical text: the text height is along x (left of the wire for local labels)
            self.box(x + h0, y, x + h1, y + d[1] * ln, "label", owner, net)

    # --- part placement ------------------------------------------------------
    def place(self, part, x, y, rot=0, stub=2.54, style="lib", top=2.54, ref_dx=None, val_dx=None,
              ref_at=None, val_at=None, hide_val=False):
        """Place a design part with a stub + net marker on every connected pin."""
        x, y = snap(x, 2.54), snap(y, 2.54)
        ref, lib_id = part["ref"], part["symbol"]
        info = self.use(lib_id)
        lp = info["props"]
        if style == "row":      # "REF  VALUE" on one line above a horizontal two-pin part
            wr, wv = text_w(ref), text_w(part["value"])
            total = wr + 1.0 + wv
            ref_pos = (x - total / 2 + wr / 2, y - top, None)
            val_pos = (x + total / 2 - wv / 2, y - top, None)
        else:
            def from_lib(name):
                p = lp[name]
                ox, oy = tx(p["x"], p["y"], 0)
                just = p["justify"][0] if p["justify"] and p["justify"][0] in ("left", "right") else None
                return (x + ox, y + oy, just)
            ref_pos, val_pos = from_lib("Reference"), from_lib("Value")
        if ref_at:
            ref_pos = (x + ref_at[0], y + ref_at[1], ref_at[2] if len(ref_at) > 2 else None)
        if val_at:
            val_pos = (x + val_at[0], y + val_at[1], val_at[2] if len(val_at) > 2 else None)
        fields = [("Footprint", part["footprint"]), ("Datasheet", lp.get("Datasheet", {}).get("value", "")),
                  ("Description", part["desc"] or lp.get("Description", {}).get("value", "")),
                  ("LCSC", part["lcsc"]),
                  ("Assembly", {"jlc": "JLCPCB", "hand": "hand-solder", "none": "none"}[part["assembly"]])]
        self.symbol(lib_id, ref, part["value"], x, y, rot, fields, ref_pos, val_pos,
                    in_bom=part["assembly"] != "none", hide_val=hide_val)
        self.connect_pins(info, ref, part["pins"], x, y, rot, stub)

    def connect_pins(self, info, ref, pinmap, x, y, rot, stub):
        sym_numbers = set(p["number"] for p in info["pins"])
        if sym_numbers != set(pinmap):
            raise SystemExit("%s: pin map %s does not match symbol pins %s" % (
                ref, sorted(set(pinmap) ^ sym_numbers), sorted(sym_numbers)))
        by_pos = {}
        for p in info["pins"]:
            by_pos.setdefault((p["x"], p["y"]), []).append(p)
        for (px, py), plist in by_pos.items():
            nets = set(pinmap[p["number"]] for p in plist)
            if len(nets) != 1:
                raise SystemExit("%s: stacked pins %s on different nets %s" % (
                    ref, [p["number"] for p in plist], nets))
            net = nets.pop()
            ox, oy = tx(px, py, rot)
            ex, ey = round(x + ox, 4), round(y + oy, 4)
            a = plist[0]["a"]
            body = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[a]   # towards the body, y up
            dx, dy = tx(-body[0], -body[1], rot)
            d = (int(round(dx)), int(round(dy)))
            owner = "%s.%s" % (ref, plist[0]["number"])
            if net is None:
                if all(p["hidden"] for p in plist):
                    if not all(p["type"] == "no_connect" for p in plist):
                        raise SystemExit("%s: hidden pin left open" % owner)
                else:
                    self.no_connect(ex, ey)
                continue
            sx, sy = round(ex + d[0] * stub, 4), round(ey + d[1] * stub, 4)
            self.wire(ex, ey, sx, sy, owner)
            self.attach(net, sx, sy, d, owner)

    def flag(self, net, x, y):
        """PWR_FLAG pointing left, net marker to the right."""
        x, y = snap(x, 2.54), snap(y, 2.54)
        self.nflg += 1
        ref = "#FLG%02d" % self.nflg
        info = self.symbol("power:PWR_FLAG", ref, "PWR_FLAG", x, y, 90, [], (x, y, None), (x, y, None),
                           in_bom=False, hide_ref=True, hide_val=True)
        self.connect_pins(info, ref, {"1": net}, x, y, 90, 2.54)

    # --- output --------------------------------------------------------------
    def overlaps(self):
        out = []
        bx = self.boxes
        for i in range(len(bx)):
            a = bx[i]
            for j in range(i + 1, len(bx)):
                b = bx[j]
                if a[0] >= b[2] - 0.05 or b[0] >= a[2] - 0.05 or a[1] >= b[3] - 0.05 or b[1] >= a[3] - 0.05:
                    continue
                kinds = {a[4], b[4]}
                same_part = a[5].split(".")[0] == b[5].split(".")[0]
                if a[5] == b[5] and kinds <= {"stub", "label"}:
                    continue
                if same_part and kinds in ({"stub", "body"}, {"body", "field"}, {"stub"}, {"body"}):
                    continue
                out.append("%s %s '%s'  x  %s %s '%s'  at (%.1f, %.1f)" % (
                    a[4], a[5], a[6], b[4], b[5], b[6], max(a[0], b[0]), max(a[1], b[1])))
        return out

    def render(self):
        libs = []
        for lib_id in self.used:
            sym = get_symbol(lib_id)["sym"]
            libs.append(dump(renamed(sym, unq(sym[1])) if False else _embedded(sym, lib_id), 2))
        out = ['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")',
               '\t(uuid %s)' % q(ROOT_UUID),
               '\t(paper "A3")',
               '\t(title_block (title %s) (rev %s) (company "generated by hardware/pcb/gen/gen_sch.py - do not edit by hand"))' % (
                   q(design.TITLE), q(design.REVISION)),
               '\t(lib_symbols', "\n".join("\t\t" + s for s in libs), '\t)']
        out += ["\t" + s.replace("\n", "\n\t") for s in self.items]
        out.append('\t(sheet_instances (path "/" (page "1")))')
        out.append('\t(embedded_fonts no)')
        out.append(')')
        return "\n".join(out) + "\n"


def _embedded(sym, lib_id):
    out = list(sym)
    out[1] = q(lib_id)
    return out


# -------------------------------------------------------------------- layout --
ROW_TOP = {  # distance of the "REF VALUE" text line above a horizontal two-pin part
    "Device:R": 2.4, "Device:C": 3.3, "Device:L": 2.7, "Device:Fuse": 2.4, "Device:Polyfuse": 2.8,
    "Device:LED": 3.7, "handheld:BAT54": 2.7, "Diode:SMF5V0A": 2.7,
    "Jumper:SolderJumper_2_Bridged": 2.9, "Switch:SW_Push": 3.9,
}
VERTICAL = ("Device:R", "Device:C", "Device:L", "Device:Fuse", "Device:Polyfuse")
ROW_PITCH = 7.62
# single-block nets drawn as global labels anyway (they sit right below another label on an IC)
FORCE_GLOBAL = ("CHG_K", "CHG_TMR", "CHG_EN1", "FB", "UART_TX", "UART_RX")

# block: (group, x, y, w, h)
BLOCKS = [
    ("usb", 12, 14, 98, 76),
    ("charger", 112, 14, 152, 76),
    ("battery", 266, 14, 134, 76),
    ("gauge", 12, 92, 100, 72),
    ("regulator", 114, 92, 154, 72),
    ("audio", 270, 92, 130, 72),
    ("mcu", 12, 166, 124, 116),
    ("display", 138, 166, 56, 116),
    ("buttons", 196, 166, 90, 116),
    ("misc", 288, 166, 112, 84),
]


def build():
    sh = Sheet()
    parts = {p["ref"]: p for p in design.PARTS}
    placed = set()

    # a net is drawn with local labels when all its pins sit in one block
    groups = {}
    for p in design.PARTS:
        for net in p["pins"].values():
            if net:
                groups.setdefault(net, set()).add(p["group"])
    for net, gs in groups.items():
        sh.local[net] = len(gs) == 1 and net not in FORCE_GLOBAL

    origin = {b[0]: (b[1], b[2]) for b in BLOCKS}
    for g, bx, by, w, h in BLOCKS:
        sh.rect(bx, by, bx + w, by + h)
        sh.text(design.GROUPS[g], bx + 1.5, by + 5, size=2.2, bold=True)

    def put(ref, x, y, **kw):
        p = parts[ref]
        ox, oy = origin[p["group"]]
        sh.place(p, ox + x, oy + y, **kw)
        placed.add(ref)

    def row(ref, x, y):
        lib_id = parts[ref]["symbol"]
        put(ref, x, y, rot=90 if lib_id in VERTICAL else 0, style="row", top=ROW_TOP[lib_id])

    def rows(x, y, refs, pitch=ROW_PITCH):
        for i, ref in enumerate(refs):
            row(ref, x, y + i * pitch)

    # USB input
    put("J1", 18, 40)
    rows(74, 14, ["F1", "D1", "R1", "R2"])
    put("U1", 74, 58, ref_at=(-12.7, -7.62, "left"), val_at=(3.81, -7.62, "left"))

    # charger
    put("U2", 36, 46)
    rows(92, 14, ["C1", "C2", "C3", "R3", "R4", "R5", "R6"])
    rows(130, 14, ["R8", "R9", "D2", "D3", "R10"])
    put("J3", 132, 60)

    # battery + protection
    put("J2", 26, 16)
    rows(24, 30, ["F2", "R11", "R13", "C4", "R14"])
    put("Q1", 62, 30)
    put("U3", 100, 26)
    put("Q2", 100, 60)

    # fuel gauge
    put("U4", 34, 34)
    rows(78, 16, ["C5", "R15", "R16", "R17"])

    # regulator
    put("U5", 76, 34)
    rows(24, 14, ["JP1", "C6", "C7", "C8", "R21", "R20"])
    put("SW1", 26, 62)
    rows(130, 14, ["L1", "C9", "C10", "C11", "R18", "R19", "JP2"])

    # audio
    put("U7", 38, 40)
    rows(96, 16, ["C17", "C18", "R26"])
    put("J7", 100, 44)

    # MCU
    put("U6", 48, 62, val_at=(3.81, -26.67, "left"))
    rows(102, 14, ["C12", "C13", "R22", "C14", "SW2", "R23", "SW3", "R24", "R25", "C15", "C16"])
    put("J9", 104, 102)

    # display + SD
    put("J4", 40, 34)
    put("J5", 40, 80)

    # buttons + joystick
    rows(30, 16, ["SW%d" % i for i in range(4, 12)])
    put("J6", 72, 30)

    # misc
    ox, oy = origin["misc"]
    for i in range(6):
        ref = "TP%d" % (i + 1)
        sh.place(parts[ref], ox + 16, oy + 16 + i * 7.62, rot=90, ref_at=(-6.5, 0), hide_val=True)
        placed.add(ref)
    sh.text("PWR_FLAG (ERC only)", ox + 40, oy + 12)
    for i, net in enumerate(design.PWR_FLAG_NETS):
        sh.flag(net, ox + 46, oy + 16 + i * 7.62)
    sh.text("Mounting holes", ox + 72, oy + 12)
    for i in range(8):
        ref = "H%d" % (i + 1)
        sh.place(parts[ref], ox + 76 + (i % 4) * 9, oy + 24 + (i // 4) * 14,
                 ref_at=(0, -6.2), val_at=(0, -4.2))
        placed.add(ref)

    missing = [p["ref"] for p in design.PARTS if p["ref"] not in placed]
    if missing:
        raise SystemExit("parts not placed: %s" % missing)
    return sh


# --------------------------------------------------------------- other files --
def write_symbol_lib(path):
    syms = custom_symbols()
    body = "\n".join("\t" + dump(s, 1) for s in syms.values())
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '
                '(generator_version "9.0")\n%s\n)\n' % body)


def write_project(path):
    classes = [{
        "name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6, "via_drill": 0.3,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25, "bus_width": 12, "wire_width": 6, "line_style": 0,
        "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
        "priority": 2147483647, "tuning_profile": "",
    }]
    patterns = []
    for name, nc in design.NET_CLASSES.items():
        c = dict(classes[0])
        c.update(name=name, clearance=nc["clearance"], track_width=nc["track_width"],
                 via_diameter=nc["via_diameter"], via_drill=nc["via_drill"], priority=0)
        classes.append(c)
        patterns += [{"netclass": name, "pattern": n} for n in nc["nets"]]
    pro = {
        "board": {}, "boards": [], "cvpcb": {"equivalence_files": []},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": PROJECT + ".kicad_pro", "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4}, "net_colors": None,
                         "netclass_assignments": None, "netclass_patterns": patterns},
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[ROOT_UUID, "Root"]],
        "text_variables": {},
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sh = build()
    with open(os.path.join(OUT_DIR, PROJECT + ".kicad_sch"), "w", encoding="utf-8", newline="\n") as f:
        f.write(sh.render())
    write_symbol_lib(os.path.join(OUT_DIR, PROJECT + ".kicad_sym"))
    write_project(os.path.join(OUT_DIR, PROJECT + ".kicad_pro"))
    with open(os.path.join(OUT_DIR, "sym-lib-table"), "w", encoding="utf-8", newline="\n") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "handheld")(type "KiCad")'
                '(uri "${KIPRJMOD}/handheld.kicad_sym")(options "")(descr "Project symbols (generated)"))\n)\n')
    with open(os.path.join(OUT_DIR, "fp-lib-table"), "w", encoding="utf-8", newline="\n") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "handheld")(type "KiCad")'
                '(uri "${KIPRJMOD}/handheld.pretty")(options "")(descr "Project footprints"))\n)\n')
    ov = sh.overlaps()
    print("wrote %s: %d parts, %d GND symbols, %d flags" % (PROJECT + ".kicad_sch", len(design.PARTS), sh.npwr, sh.nflg))
    print("layout overlaps: %d" % len(ov))
    for o in ov:
        print("  " + o)


if __name__ == "__main__":
    main()
