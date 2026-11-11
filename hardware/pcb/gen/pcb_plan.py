"""Routing plan and silkscreen for gen_pcb.py.

route(bd):  explicit copper (regulator pours, USB connector fan-out, thermal
            vias), then GND via stubs, then the grid router for everything else.
finish(bd): silkscreen / fab texts.
All coordinates: mm, board origin top-left, front view.
"""
import time

import pcbnew

import design
import pcb_route
from pcb_route import F, B, PITCH

W, H = 90.0, 100.0


# ----------------------------------------------------------------- helpers --
def cells(bd, ref, pin):
    out = []
    for p in bd.pads[(ref, str(pin))]:
        out.append(p["cells"])
    return out


def track(bd, net, layer, pts, width=0.25, join=()):
    c = bd.r.add_track(net, layer, pts, width)
    sets = [c] if c else []
    for ref, pin in join:
        sets += cells(bd, ref, pin)
    if len(sets) > 1:
        bd.r.join(net, sets)


def pour(bd, net, pts, prio=1):
    bd.zone(net_full(bd, net), pcbnew.B_Cu, pts, prio=prio, clearance=0.2, solid=True, name=net)
    bd.r.add_pour(net, B, pts)


def net_full(bd, net):
    for (ref, pin), name in bd.pin_net.items():
        if name.lstrip("/") == net:
            return name
    raise KeyError(net)


def obstacles(bd):
    r = bd.r
    e = 0.4
    for shape in (("rect", W / 2, -1, W, 1), ("rect", W / 2, H + 1, W, 1),
                  ("rect", -1, H / 2, 1, H), ("rect", W + 1, H / 2, 1, H),
                  ("poly", [(0, 0), (1.17, 0), (0, 1.17)]), ("poly", [(W, 0), (W - 1.17, 0), (W, 1.17)]),
                  ("poly", [(0, H), (1.17, H), (0, H - 1.17)]), ("poly", [(W, H), (W - 1.17, H), (W, H - 1.17)])):
        r.stamp(shape, [F, B], None, clr=e)
    # antenna keep-outs: the module footprint's own rule area and the designer's
    r.stamp(("rect", 24.0, 3.5, 24.0, 3.5), [F, B], None, clr=0.0)
    r.stamp(("rect", 24.0, 4.0, 12.0, 4.0), [F, B], None, clr=0.0)
    r.stamp_bool(r.novia, ("rect", 24.0, 3.5, 24.0, 3.5), 0.35)
    r.stamp_bool(r.novia, ("rect", 24.0, 4.0, 12.0, 4.0), 0.35)
    # no tracks on the back under the module body (only the GND pour)
    r.stamp(("rect", 24.0, 16.3, 7.3, 8.3), [B], None, clr=0.0)


def ground_pad(bd, ref, pin):
    for c in cells(bd, ref, pin):
        bd.r.grounded |= c


# ----------------------------------------------------------- explicit copper --
def regulator(bd):
    r = bd.r
    # thermal vias under U5 (6 x 0.3 mm) and the other exposed pads
    for dx in (-0.4, 0.4):
        for dy in (-0.95, 0.0, 0.95):
            r.add_via("GND", 49.0 + dx, 27.0 + dy)
    for dx in (-0.4, 0.4):
        for dy in (-0.4, 0.4):
            r.add_via("GND", 64.5 + dx, 18.5 + dy)
    r.add_via("GND", 62.0, 33.0)
    r.add_via("GND", 20.0, 40.0)
    for ref, pin in (("U5", 15), ("U2", 17), ("U4", 9), ("U7", 17), ("U6", 41), ("U5", 2), ("U5", 13)):
        ground_pad(bd, ref, pin)
    # switch nodes, input and output as small pours (short, wide)
    pour(bd, "SW_L2", [(46.95, 20.15), (48.0, 20.15), (48.0, 26.12), (46.95, 26.12)])
    pour(bd, "SW_L1", [(50.0, 20.15), (51.05, 20.15), (51.05, 26.12), (50.0, 26.12)])
    pour(bd, "VIN_REG", [(50.1, 26.38), (51.7, 26.38), (51.7, 22.9), (52.7, 22.9), (52.7, 29.7), (53.75, 29.7),
                         (53.75, 30.85), (51.9, 30.85), (51.9, 27.12), (50.1, 27.12)])
    pour(bd, "VOUT_REG", [(44.6, 24.1), (46.0, 24.1), (46.0, 25.6), (46.4, 25.6), (46.4, 26.38), (47.9, 26.38),
                          (47.9, 27.12), (46.4, 27.12), (46.4, 31.7), (45.7, 31.7), (45.7, 34.35), (41.65, 34.35),
                          (41.65, 32.6), (45.35, 32.6), (45.35, 25.6), (44.6, 25.6)])
    r.join("SW_L2", cells(bd, "L1", 2) + cells(bd, "U5", 6) + cells(bd, "U5", 7))
    r.join("SW_L1", cells(bd, "L1", 1) + cells(bd, "U5", 8) + cells(bd, "U5", 9))
    r.join("VIN_REG", cells(bd, "U5", 10) + cells(bd, "U5", 11) + cells(bd, "C6", 1) + cells(bd, "C7", 1) +
           cells(bd, "C8", 1) + cells(bd, "R21", 1) + cells(bd, "JP1", 2))
    r.join("VOUT_REG", cells(bd, "U5", 4) + cells(bd, "U5", 5) + cells(bd, "C9", 1) + cells(bd, "C10", 1) +
           cells(bd, "C11", 1) + cells(bd, "JP2", 1) + cells(bd, "R18", 1) + cells(bd, "TP6", 1))
    # GND pins to the exposed pad (U5 and the charger U2)
    track(bd, "GND", B, [(63.062, 17.75), (63.4, 17.8), (63.9, 17.8)], 0.2)
    track(bd, "GND", B, [(63.062, 19.25), (63.4, 19.2), (63.9, 19.2)], 0.2)
    track(bd, "GND", B, [(63.75, 19.938), (63.75, 19.2)], 0.2)
    for pin in (4, 5, 8):
        ground_pad(bd, "U2", pin)
    track(bd, "GND", B, [(47.6, 28.0), (48.3, 28.0)], 0.2)
    track(bd, "GND", B, [(50.4, 28.0), (49.7, 28.0)], 0.2)
    # VINA (pin 1) around the bottom of the IC to the input caps / JP1
    track(bd, "VIN_REG", B, [(47.6, 28.5), (47.6, 29.5), (48.1, 30.0), (52.4, 30.0)], 0.25,
          join=[("U5", 1), ("JP1", 2)])
    # FB: left, then down to the divider below the output caps (away from L1)
    track(bd, "FB", B, [(47.6, 27.5), (46.75, 27.5), (46.75, 32.75), (46.5, 33.0), (47.925, 33.0)], 0.25,
          join=[("U5", 3), ("R18", 2), ("R19", 1)])
    # EN: out between the VIN finger and pin 13, via to the front
    track(bd, "EN_SW", B, [(50.4, 27.5), (51.25, 27.5), (51.25, 29.25)], 0.25, join=[("U5", 12)])
    c = r.add_via("EN_SW", 51.25, 29.25)
    r.join("EN_SW", [c] + cells(bd, "U5", 12))


def usb(bd):
    r = bd.r
    y0 = 7.195
    # D-: B7 + A7 joined on the connector side, D+: A6 + B6 joined on the board side
    track(bd, "USB_DN", B, [(61.25, y0), (61.25, 6.05), (62.25, 6.05), (62.25, y0)], 0.2,
          join=[("J1", "B7"), ("J1", "A7")])
    track(bd, "USB_DP", B, [(61.75, y0), (61.75, 8.5), (62.75, 8.5), (62.75, y0)], 0.25,
          join=[("J1", "A6"), ("J1", "B6")])
    track(bd, "USB_DN", B, [(61.25, y0), (61.25, 11.5), (60.95, 11.8), (52.363, 11.8)], 0.25,
          join=[("J1", "B7"), ("U1", 1), ("U1", 6)])
    track(bd, "USB_DP", B, [(62.25, 8.5), (62.25, 13.2), (61.75, 13.7), (52.363, 13.7)], 0.25,
          join=[("J1", "A6"), ("U1", 3), ("U1", 4)])
    track(bd, "CC1", B, [(60.75, y0), (60.75, 9.0)], 0.25, join=[("J1", "A5"), ("R1", 1)])
    track(bd, "CC2", B, [(63.75, y0), (63.75, 9.0)], 0.25, join=[("J1", "B5"), ("R2", 1)])
    # VBUS: right pads on the back to F1, left pads hop over on the front
    track(bd, "VBUS", B, [(64.45, y0), (64.45, 8.3), (64.9, 8.75)], 0.4)
    track(bd, "VBUS", B, [(64.9, 8.75), (67.25, 8.75), (68.0, 9.5), (69.1, 9.5)], 0.6,
          join=[("J1", "A9"), ("F1", 1)])
    track(bd, "VBUS", B, [(59.55, y0), (59.45, 8.45), (58.8, 8.9)], 0.4)
    for x, y in ((59.45, 8.45), (58.8, 8.9), (66.25, 8.75), (67.0, 8.75)):
        r.add_via("VBUS", x, y)
    track(bd, "VBUS", F, [(58.8, 8.9), (59.45, 8.45), (59.75, 8.75), (67.0, 8.75)], 0.6,
          join=[("J1", "A4"), ("J1", "A9")])


# -------------------------------------------------------------- stitching ---
def stitch(bd, seeds, radius=3.0):
    r = bd.r
    n = 0
    fp = r._free("p", "GND")
    ok = fp[0] & fp[1] & ~r.novia & ~r.nearpad
    k = int(radius / PITCH)
    for sx, sy in seeds:
        iy0, ix0 = r.node(sx, sy)
        best = None
        for dy in range(-k, k + 1):
            for dx in range(-k, k + 1):
                iy, ix = iy0 + dy, ix0 + dx
                if 0 <= iy < r.ny and 0 <= ix < r.nx and ok[iy, ix]:
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]:
                        best = (d, iy, ix)
        if best:
            r.add_via("GND", best[2] * PITCH, best[1] * PITCH)
            fp = r._free("p", "GND")
            ok = fp[0] & fp[1] & ~r.novia & ~r.nearpad
            n += 1
    return n


POWER_ORDER = ["VBUS", "VBUS_F", "BATT_P", "BATT_PF", "FET_D", "BATT_N", "VBAT", "SYS", "VIN_REG", "VOUT_REG",
               "SPK_P", "SPK_N", "3V3"]
EARLY = ["USB_DN", "USB_DP", "DW_OD", "DW_OC", "DW_CS", "DW_VCC", "Q1_G", "CHG_ILIM", "CHG_ISET", "CHG_TMR",
         "CHG_EN1", "FB", "EN_PU", "LED_A"]


def escape(bd, ref, length=0.75):
    """Short straight stub out of every connected pad of a fine-pitch part, so that
    later (wider) tracks cannot fence the pin in.  Ends on a grid node."""
    r = bd.r
    cx, cy = bd.PLACE[ref][0], bd.PLACE[ref][1]
    for (rf, pin), lst in sorted(bd.pads.items()):
        if rf != ref:
            continue
        for p in lst:
            net = p["net"]
            if net in (None, "GND") or net.startswith("unconnected-") or p["shape"][0] != "rect":
                continue
            _, bx, by, hx, hy = p["shape"]
            if hx > 1.0 and hy > 1.0:
                continue
            x, y = p["x"], p["y"]
            if hx > hy:
                sx = 1 if bx > cx else -1
                ex = bx + sx * (hx + length)
                ex = (int(ex / PITCH) + (1 if sx > 0 else 0)) * PITCH
                end = (ex, round(y / PITCH) * PITCH)
                mid = (bx + sx * (hx + 0.25), y)
            else:
                sy = 1 if by > cy else -1
                ey = by + sy * (hy + length)
                ey = (int(ey / PITCH) + (1 if sy > 0 else 0)) * PITCH
                end = (round(x / PITCH) * PITCH, ey)
                mid = (x, by + sy * (hy + 0.25))
            iy, ix = r.node(*end)
            if r.own["s"][B, iy, ix] not in (0, r.nid(net)):
                continue
            pts = [(x, y), mid, end] if (abs(mid[0] - end[0]) > 1e-6 and abs(mid[1] - end[1]) > 1e-6) else [(x, y), end]
            track(bd, net, B, pts, 0.25, join=[(ref, pin)])
            # routing must continue from the stub end (no second exit from the pad)
            endc = r.cell(B, iy, ix)
            comp = next(c for c in r.comps[net] if endc in c)
            comp.clear()
            comp.add(endc)


def route(bd):
    r = bd.r
    t0 = time.time()
    obstacles(bd)
    regulator(bd)
    usb(bd)
    for ref in ("U2", "U4", "U7"):
        escape(bd, ref)
    escape(bd, "U6", 1.25)
    nets = design.nets()

    def span(net):
        xs = [bd.pad(ref, pin)["x"] for ref, pin in nets[net]]
        ys = [bd.pad(ref, pin)["y"] for ref, pin in nets[net]]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    # GND vias of the decoupling / bulk capacitors first, so that they end up right at the pad
    for ref in ("C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13", "C1", "C2", "C3", "C5", "C17", "C18", "D1"):
        for p in bd.pads[(ref, "2")]:
            r.gnd_stub(p["cells"], True)
    sig = [n for n in nets if n not in POWER_ORDER and n != "GND" and len(nets[n]) > 1]
    sig.sort(key=span)
    short = [n for n in sig if span(n) < 7.0]
    rest = [n for n in sig if n not in short]
    # 1. local nets, 2. power, 3. the remaining signals shortest first (USB first), 4. 3V3;
    #    all with rip-up and retry
    r.begin_maze()
    jobs = [(net, dict(power=False, fcost=3.0)) for net in short]
    jobs += [(net, dict(power=True, fcost=3.0, via_cost=6.0)) for net in POWER_ORDER if net != "3V3"]
    jobs += [(net, dict(power=False, fcost=3.0)) for net in ["USB_DN", "USB_DP"] + [n for n in rest if not n.startswith("USB_")]]
    jobs.append(("3V3", dict(power=True, fcost=2.0, via_cost=5.0)))
    fails = r.route_all(jobs)
    # 5. GND: every SMD pad gets a short stub to a via into the front plane
    r.mazing = False
    nostub = 0
    for (ref, pin), lst in sorted(bd.pads.items()):
        for p in lst:
            if p["net"] == "GND" and p["smd"]:
                if not r.gnd_stub(p["cells"], True):
                    nostub += 1
    print("GND pads without own via: %d" % nostub)
    seeds = [(5 + 10 * i, 5 + 10 * j) for j in range(10) for i in range(9) if (i, j) not in NO_STITCH]
    seeds += [(10 * i, 10 * j) for j in range(1, 10) for i in range(1, 9)]
    seeds += [(46.0, 19.3), (52.0, 19.3), (55.5, 27.0), (43.0, 29.0), (50.5, 31.5), (49.0, 35.0), (43.0, 22.0)]
    n = stitch(bd, seeds)
    import os
    dbg = os.environ.get("KH_DEBUG_PNG")
    if dbg:
        r.png(dbg + "_b.png", B, 4)
        r.png(dbg + "_f.png", F, 4)
    print("routing: %d failed connections, %d stitching vias, %.0f s" % (fails, n, time.time() - t0))


NO_STITCH = {(6, 0)}      # under the USB connector: no front copper to connect to

# ------------------------------------------------------------- silkscreen ---
TXT = 0.8          # reference / label text height
BTN = {"SW4": "UP", "SW5": "DOWN", "SW6": "LEFT", "SW7": "RIGHT", "SW8": "A", "SW9": "B",
       "SW10": "START", "SW11": "SELECT"}
J4_NAMES = ["3V3", "GND", "CS", "RST", "DC", "MOSI", "SCK", "LED"]


class Silk:
    def __init__(self, bd):
        self.bd = bd
        self.boxes = {"F": [], "B": []}
        ox, oy = bd.OX, bd.OY
        for ref, fp in bd.fp.items():
            side = bd.PLACE[ref][3]
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                box = (pcbnew.ToMM(bb.GetLeft()) - ox - 0.2, pcbnew.ToMM(bb.GetTop()) - oy - 0.2,
                       pcbnew.ToMM(bb.GetRight()) - ox + 0.2, pcbnew.ToMM(bb.GetBottom()) - oy + 0.2)
                thru = pad.GetDrillSize().x > 0
                for s in ("F", "B"):
                    if thru or s == side:
                        self.boxes[s].append((box, ref))
            self.boxes[side].append((self.body(ref), ref))

    def body(self, ref):
        if ref == "U6":
            return (14.25, 1.0, 33.75, 27.2)
        fp = self.bd.fp[ref]
        side = self.bd.PLACE[ref][3]
        bb = fp.GetCourtyard(pcbnew.B_CrtYd if side == "B" else pcbnew.F_CrtYd).BBox()
        ox, oy = self.bd.OX, self.bd.OY
        return (pcbnew.ToMM(bb.GetLeft()) - ox, pcbnew.ToMM(bb.GetTop()) - oy,
                pcbnew.ToMM(bb.GetRight()) - ox, pcbnew.ToMM(bb.GetBottom()) - oy)

    def free(self, side, box, own=None):
        if box[0] < 0.6 or box[1] < 0.6 or box[2] > W - 0.6 or box[3] > H - 0.6:
            return False
        for (b, ref) in self.boxes[side]:
            if ref == own and own is not None and False:
                continue
            if box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3]:
                return False
        return True

    @staticmethod
    def size(s, h):
        return len(s) * h * 0.87 + 0.15, h * 1.25

    def label(self, s, x, y, side, h=TXT, force=True, rot=0):
        w, hh = self.size(s, h)
        if rot:
            w, hh = hh, w
        box = (x - w / 2, y - hh / 2, x + w / 2, y + hh / 2)
        if not force and not self.free(side, box):
            return False
        self.boxes[side].append((box, "text"))
        layer = pcbnew.B_SilkS if side == "B" else pcbnew.F_SilkS
        self.bd.text(s, x, y, layer, h, 0.12 if h < 1.2 else 0.2, rot=rot)
        return True

    def around(self, ref, s, h=TXT):
        """Candidate centres for a text next to footprint `ref`."""
        x0, y0, x1, y1 = self.body(ref)
        w, hh = self.size(s, h)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        g = 0.6 if ref[0] == "U" else 0.3
        out = [(cx, y0 - hh / 2 - g, 0), (cx, y1 + hh / 2 + g, 0), (x1 + w / 2 + g, cy, 0), (x0 - w / 2 - g, cy, 0),
               (x1 + hh / 2 + g, cy, 90), (x0 - hh / 2 - g, cy, 90)]
        for d in (0.8, -0.8, 1.6, -1.6):
            out += [(cx + d, y0 - hh / 2 - g, 0), (cx + d, y1 + hh / 2 + g, 0),
                    (x1 + w / 2 + g, cy + d, 0), (x0 - w / 2 - g, cy + d, 0)]
        return out

    def auto(self, ref, s, side, h=TXT):
        for x, y, rot in self.around(ref, s, h):
            if self.label(s, x, y, side, h, force=False, rot=rot):
                return True
        return False

    def reference(self, ref, side):
        fp = self.bd.fp[ref]
        fld = fp.Reference()
        w, hh = self.size(ref, TXT)
        for x, y, rot in self.around(ref, ref):
            bw, bh = (hh, w) if rot else (w, hh)
            box = (x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2)
            if self.free(side, box):
                self.boxes[side].append((box, "text"))
                fld.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(TXT), pcbnew.FromMM(TXT)))
                fld.SetTextThickness(pcbnew.FromMM(0.12))
                fld.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(self.bd.OX + x), pcbnew.FromMM(self.bd.OY + y)))
                fld.SetTextAngleDegrees(rot)
                fld.SetKeepUpright(True)
                return True
        fld.SetVisible(False)
        return False


def finish(bd, noroute):
    s = Silk(bd)
    # fixed labels first
    for ref, name in BTN.items():
        x, y = bd.PLACE[ref][0] + 3.25, bd.PLACE[ref][1] + 2.25
        s.label(name, x, y - 4.7, "F", 1.2)
    s.label("ESP32 Handheld v1", 45.0, 97.4, "B", 1.5)
    s.label("RST", 41.0, 6.3, "B", 1.0)
    s.label("BOOT", 41.0, 20.3, "B", 1.0)
    s.label("+", 66.4, 54.6, "B", 1.2)
    s.label("BAT", 67.6, 57.6, "B", 1.0)
    s.label("NTC", 76.0, 50.3, "B", 1.0)
    for i, name in enumerate(J4_NAMES):
        s.label(name, 5.3 + s.size(name, TXT)[0] / 2, 18.49 + 2.54 * i, "B")
    hidden = []
    for p in design.PARTS:
        ref = p["ref"]
        side = bd.PLACE[ref][3]
        if ref.startswith("H"):
            bd.fp[ref].Reference().SetVisible(False)
            continue
        if ref.startswith("TP"):
            bd.fp[ref].Reference().SetVisible(False)
            if not s.auto(ref, p["value"], side):
                hidden.append(ref + " label")
            continue
        if not s.reference(ref, side):
            hidden.append(ref)
    if hidden:
        print("silk: no room for reference of " + " ".join(hidden))
