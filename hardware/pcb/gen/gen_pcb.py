"""Generate handheld/handheld.kicad_pcb from design.py (KiCad 9 pcbnew API).

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" gen_pcb.py [--noroute]

The board is rebuilt from scratch on every run: outline, footprints (KiCad
libraries / handheld.pretty) with nets from design.py, placement, routing
(explicit power / USB copper + the grid router in pcb_route.py), GND zones,
silkscreen.  Coordinates in this file are millimetres, origin = top-left board
corner, x right, y down, seen from the FRONT (also for parts on the back).
"""
import json
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402
import gen_sch  # noqa: E402  (s-expression parser)
import pcb_route  # noqa: E402
from pcb_route import F, B  # noqa: E402

OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "handheld"))
PCB = os.path.join(OUT_DIR, design.PROJECT + ".kicad_pcb")
PRO = os.path.join(OUT_DIR, design.PROJECT + ".kicad_pro")
NET = os.path.join(OUT_DIR, design.PROJECT + ".net")
KICAD_FP = os.environ.get("KICAD9_FOOTPRINT_DIR", r"C:\Program Files\KiCad\9.0\share\kicad\footprints")

W, H, RAD = 90.0, 100.0, 2.0
OX, OY = 100.0, 50.0            # position of the board origin on the KiCad page
CLR = 0.2
EDGE = 0.4

mm = pcbnew.FromMM
LAYER = {F: pcbnew.F_Cu, B: pcbnew.B_Cu}


def P(x, y):
    return pcbnew.VECTOR2I(mm(float(OX + x)), mm(float(OY + y)))


# ------------------------------------------------------------- placement --
# ref: (x, y, rotation, side)   side "F" or "B"
PLACE = {
    # display (fixed)
    "J4": (4.00, 18.49, 0, "F"), "J5": (85.00, 31.19, 0, "F"),
    "H1": (85.00, 13.00, 0, "F"), "H2": (85.00, 57.00, 0, "F"),
    "H3": (8.92, 13.00, 0, "F"), "H4": (8.92, 57.00, 0, "F"),
    "H5": (4, 96, 0, "F"), "H6": (86, 96, 0, "F"), "H7": (4, 66, 0, "F"), "H8": (86, 66, 0, "F"),
    # MCU
    "U6": (24.0, 13.75, 0, "B"),
    "SW2": (41.0, 10.0, 0, "B"), "SW3": (41.0, 16.5, 0, "B"),
    "C13": (34.8, 9.4, 270, "B"), "C12": (36.4, 9.4, 270, "B"),
    "R22": (47.0, 8.25, 0, "B"), "C14": (47.0, 9.85, 0, "B"),
    "R23": (12.4, 27.5, 0, "B"), "R24": (21.0, 31.3, 0, "B"), "R25": (25.5, 31.3, 0, "B"),
    "J9": (12.0, 42.2, 0, "B"),
    # USB
    "J1": (62.0, 3.15, 180, "B"),
    "R1": (60.4, 10.0, 90, "B"), "R2": (63.5, 10.0, 90, "B"),
    "U1": (53.5, 12.75, 0, "B"),
    "F1": (70.5, 9.5, 180, "B"), "D1": (72.4, 12.5, 180, "B"),
    "D2": (72.0, 3.6, 0, "B"), "R9": (72.0, 5.5, 0, "B"),
    # charger
    "U2": (64.5, 18.5, 270, "B"),
    "C2": (64.0, 15.5, 0, "B"), "C1": (68.3, 16.5, 180, "B"), "R4": (67.4, 14.8, 180, "B"),
    "R5": (69.0, 18.25, 180, "B"), "R3": (69.0, 19.9, 180, "B"),
    "C3": (64.5, 22.3, 90, "B"),
    "R6": (60.2, 20.4, 180, "B"), "R8": (60.2, 18.6, 180, "B"),
    "D3": (58.5, 16.0, 0, "B"), "R10": (55.6, 18.0, 180, "B"),
    # battery chain
    "J2": (63.0, 54.9, 0, "B"), "J3": (77.25, 54.0, 0, "B"),
    "F2": (63.0, 49.6, 270, "B"), "Q1": (63.0, 45.2, 90, "B"), "R11": (60.3, 45.0, 90, "B"),
    "Q2": (57.5, 50.0, 270, "B"), "U3": (57.5, 45.5, 270, "B"),
    "C4": (57.9, 42.6, 180, "B"), "R13": (60.0, 40.9, 0, "B"), "R14": (54.5, 47.5, 90, "B"),
    "U4": (62.0, 33.0, 0, "B"), "C5": (64.0, 30.8, 0, "B"),
    "R15": (57.2, 31.2, 0, "B"), "R16": (57.2, 32.9, 0, "B"), "R17": (57.2, 34.6, 0, "B"),
    # regulator
    "U5": (49.0, 27.0, 180, "B"), "L1": (49.0, 22.0, 0, "B"),
    "C8": (53.0, 25.0, 180, "B"), "C6": (53.0, 26.75, 180, "B"), "C7": (53.0, 28.5, 180, "B"),
    "R21": (53.0, 23.4, 180, "B"),
    "C9": (44.9, 26.75, 0, "B"), "C10": (44.9, 28.85, 0, "B"), "C11": (44.9, 30.95, 0, "B"),
    "JP1": (53.0, 31.0, 270, "B"), "JP2": (45.3, 23.9, 270, "B"),
    "R18": (45.6, 33.0, 180, "B"), "R19": (48.75, 33.0, 180, "B"),
    "SW1": (88.1, 22.0, 90, "B"), "R20": (83.3, 22.75, 0, "B"),
    # audio
    "U7": (20.0, 40.0, 90, "B"), "C18": (23.8, 40.25, 180, "B"), "C17": (23.8, 41.85, 180, "B"),
    "R26": (22.3, 36.9, 0, "B"),
    "J7": (18.73, 64.0, 90, "B"),
    # joystick
    "J6": (39.92, 66.0, 90, "B"), "C15": (45.0, 62.5, 270, "B"), "C16": (47.54, 62.5, 270, "B"),
    # test points
    "TP1": (75.0, 9.5, 0, "B"), "TP2": (57.5, 24.5, 0, "B"), "TP3": (69.0, 24.0, 0, "B"),
    "TP4": (40.5, 24.0, 0, "B"), "TP5": (70.0, 30.0, 0, "B"), "TP6": (42.4, 33.6, 0, "B"),
}
for _i, (_x, _y) in enumerate([(20, 72), (20, 88), (12, 80), (28, 80), (76, 76), (66, 84), (50, 92), (38, 92)]):
    PLACE["SW%d" % (4 + _i)] = (_x - 3.25, _y - 2.25, 0, "F")

KEEPOUT = (12.0, 0.0, 36.0, 8.0)       # antenna keep-out requested by the designer


# ------------------------------------------------------------------ nets --
def load_netlist():
    """(ref, pin) -> net name as exported by the schematic, checked against design.py."""
    with open(NET, encoding="utf-8") as f:
        root = gen_sch.parse(f.read())
    pin_net, tstamp = {}, {}
    for c in gen_sch.children(gen_sch.child(root, "components"), "comp"):
        tstamp[gen_sch.unq(gen_sch.child(c, "ref")[1])] = gen_sch.unq(gen_sch.child(c, "tstamps")[1])
    for n in gen_sch.children(gen_sch.child(root, "nets"), "net"):
        name = gen_sch.unq(gen_sch.child(n, "name")[1])
        for node in gen_sch.children(n, "node"):
            pin_net[(gen_sch.unq(gen_sch.child(node, "ref")[1]), gen_sch.unq(gen_sch.child(node, "pin")[1]))] = name
    for p in design.PARTS:
        for pin, net in p["pins"].items():
            got = pin_net.get((p["ref"], pin))
            if got is None:
                raise SystemExit("netlist lacks %s.%s - re-export handheld.net" % (p["ref"], pin))
            if net is None:
                if not got.startswith("unconnected-"):
                    raise SystemExit("%s.%s: design says NC, netlist %s" % (p["ref"], pin, got))
            elif got.lstrip("/") != net:
                raise SystemExit("%s.%s: design %s, netlist %s" % (p["ref"], pin, net, got))
    return pin_net, tstamp


class Board:
    def __init__(self):
        pcbnew.KIID.SeedGenerator(20261111)
        self.b = pcbnew.BOARD()
        self.b.SetCopperLayerCount(2)
        self.pin_net, self.tstamp = load_netlist()
        self.nets = {}
        self.fp = {}
        self.pads = {}          # (ref, pin) -> list of dicts
        self.r = pcb_route.Router(W, H, CLR)
        self.OX, self.OY, self.PLACE = OX, OY, PLACE

    # -- low level items ---------------------------------------------------
    def net(self, name):
        """name = design.py net name or full netlist name."""
        if name not in self.nets:
            ni = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(ni)
            self.nets[name] = ni
        return self.nets[name]

    def line(self, x1, y1, x2, y2, layer, width=0.1):
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1))
        s.SetEnd(P(x2, y2))
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        self.b.Add(s)

    def arc(self, cx, cy, sx, sy, ex, ey, layer, width=0.1):
        import math
        a0, a1 = math.atan2(sy - cy, sx - cx), math.atan2(ey - cy, ex - cx)
        am = (a0 + a1) / 2
        if abs(a1 - a0) > math.pi:
            am += math.pi
        r = math.hypot(sx - cx, sy - cy)
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(P(sx, sy), P(cx + r * math.cos(am), cy + r * math.sin(am)), P(ex, ey))
        s.SetLayer(layer)
        s.SetWidth(mm(width))
        self.b.Add(s)

    def text(self, s, x, y, layer, size=1.0, thick=0.15, back=None, rot=0, hj=None):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(thick))
        t.SetPosition(P(x, y))
        if rot:
            t.SetTextAngleDegrees(rot)
        if hj is not None:
            t.SetHorizJustify(hj)
        if back if back is not None else layer in (pcbnew.B_SilkS, pcbnew.B_Fab):
            t.SetMirrored(True)
        self.b.Add(t)
        return t

    def zone(self, net, layer, pts, prio=0, clearance=0.25, solid=False, name=""):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(layer)
        z.SetNet(self.net(net))
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.5))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        if name:
            z.SetZoneName(name)
        o = z.Outline()
        o.NewOutline()
        for x, y in pts:
            o.Append(mm(OX + x), mm(OY + y))
        self.b.Add(z)
        return z

    def keepout(self, x0, y0, x1, y1):
        z = pcbnew.ZONE(self.b)
        z.SetIsRuleArea(True)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        z.SetLayerSet(ls)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetZoneName("antenna keep-out")
        o = z.Outline()
        o.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            o.Append(mm(OX + x), mm(OY + y))
        self.b.Add(z)

    # -- outline -----------------------------------------------------------
    def outline(self):
        e, r = pcbnew.Edge_Cuts, RAD
        self.line(r, 0, W - r, 0, e)
        self.line(W, r, W, H - r, e)
        self.line(W - r, H, r, H, e)
        self.line(0, H - r, 0, r, e)
        self.arc(r, r, 0, r, r, 0, e)
        self.arc(W - r, r, W - r, 0, W, r, e)
        self.arc(W - r, H - r, W, H - r, W - r, H, e)
        self.arc(r, H - r, r, H, 0, H - r, e)
        # display module reference
        d = pcbnew.Dwgs_User
        for x1, y1, x2, y2 in ((2, 10, 88, 10), (88, 10, 88, 60), (88, 60, 2, 60), (2, 60, 2, 10)):
            self.line(x1, y1, x2, y2, d, 0.15)
        self.text("LCD (MSP2807 module outline, mounted in front)", 45, 40, d, 2.0, 0.25, back=False)
        self.line(42, 10, 42, 35, d, 0.1)
        self.line(55, 10, 55, 35, d, 0.1)
        self.line(42, 35, 55, 35, d, 0.1)
        self.text("SD slot", 48.5, 30, d, 1.2, 0.15, back=False)

    # -- footprints --------------------------------------------------------
    def place_all(self):
        for p in design.PARTS:
            ref = p["ref"]
            lib, name = p["footprint"].split(":")
            d = os.path.join(OUT_DIR, "handheld.pretty") if lib == "handheld" else os.path.join(KICAD_FP, lib + ".pretty")
            fp = pcbnew.FootprintLoad(d, name)
            if fp is None:
                raise SystemExit("footprint %s not found" % p["footprint"])
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
            fp.SetReference(ref)
            fp.SetValue(p["value"])
            fp.SetPath(pcbnew.KIID_PATH("/" + self.tstamp[ref]))
            if p["lcsc"]:
                fp.SetField("LCSC", p["lcsc"])
                fld = fp.GetFieldByName("LCSC")
                if fld:
                    fld.SetVisible(False)
            x, y, rot, side = PLACE[ref]
            self.b.Add(fp)
            fp.SetPosition(P(x, y))
            if side == "B":
                fp.Flip(P(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            # after a left-right flip KiCad reports 180 deg for an unrotated part
            fp.SetOrientationDegrees(rot + 180 if side == "B" else rot)
            for pad in fp.Pads():
                num = pad.GetNumber()
                if num and (ref, num) in self.pin_net:
                    pad.SetNet(self.net(self.pin_net[(ref, num)]))
                # pads without a schematic pin (SW1 shell tabs "SH") stay netless
            if ref == "U6":      # module thermal vias: 0.2 mm drill in the library, 0.3 mm = JLCPCB 2-layer minimum
                for pad in fp.Pads():
                    if 0 < pad.GetDrillSize().x < mm(0.3):
                        pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
            self.fp[ref] = fp
        missing = [(p["ref"], pin) for p in design.PARTS for pin in p["pins"]
                   if not any(pad.GetNumber() == pin for pad in self.fp[p["ref"]].Pads())]
        if missing:
            raise SystemExit("pins without pad: %s" % missing)

    def scan_pads(self):
        """Register every pad with the router."""
        r = self.r
        for ref, fp in self.fp.items():
            for pad in fp.Pads():
                pos = pad.GetPosition()
                cx, cy = pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY
                layers = [l for l in (F, B) if pad.IsOnLayer(LAYER[l])]
                drill = pcbnew.ToMM(pad.GetDrillSize().x)
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    r.stamp(("circle", cx, cy, drill / 2), [F, B], None, clr=0.3)
                    r.stamp_bool(r.novia, ("circle", cx, cy, drill / 2), 0.5)
                    continue
                if not layers:
                    continue
                bb = pad.GetBoundingBox()
                bw, bh = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
                bcx = pcbnew.ToMM(bb.GetCenter().x) - OX
                bcy = pcbnew.ToMM(bb.GetCenter().y) - OY
                shp = pad.GetShape(LAYER[layers[0]])
                if shp == pcbnew.PAD_SHAPE_CIRCLE:
                    shape = ("circle", cx, cy, bw / 2)
                elif shp == pcbnew.PAD_SHAPE_OVAL:
                    if bw >= bh:
                        shape = ("seg", bcx - (bw - bh) / 2, bcy, bcx + (bw - bh) / 2, bcy, bh / 2)
                    else:
                        shape = ("seg", bcx, bcy - (bh - bw) / 2, bcx, bcy + (bh - bw) / 2, bw / 2)
                else:
                    shape = ("rect", bcx, bcy, bw / 2, bh / 2)
                num = pad.GetNumber()
                full = self.pin_net.get((ref, num))
                dnet = None
                if full:
                    dnet = full.lstrip("/")
                smd = drill == 0
                cells = r.add_pad(dnet, shape, layers, (cx, cy), hole=drill or None, smd=smd)
                info = {"ref": ref, "pin": num, "x": cx, "y": cy, "shape": shape, "layers": layers,
                        "net": dnet, "cells": cells, "smd": smd}
                self.pads.setdefault((ref, num), []).append(info)
                if dnet == "GND" and not smd:
                    r.grounded |= cells

    def pad(self, ref, pin, i=0):
        return self.pads[(ref, str(pin))][i]

    def xy(self, ref, pin, i=0):
        p = self.pad(ref, pin, i)
        return p["x"], p["y"]

    # -- output of routed copper --------------------------------------------
    def emit_copper(self):
        full = {}
        for (ref, pin), name in self.pin_net.items():
            full[name.lstrip("/")] = name
        # drop the last grid step of a branch when it lies completely inside the copper of a wider
        # track of the same net (KiCad reports such a piece as a dangling track)
        def inside(px, py, s):
            vx, vy = s[4] - s[2], s[5] - s[3]
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 < 1e-12 else min(1.0, max(0.0, ((px - s[2]) * vx + (py - s[3]) * vy) / L2))
            return math.hypot(px - s[2] - t * vx, py - s[3] - t * vy) < s[6] / 2 - 0.05

        by_net = {}
        for s in self.r.tracks:
            by_net.setdefault((s[0], s[1]), []).append(s)
        tracks = []
        for s in self.r.tracks:
            if math.hypot(s[4] - s[2], s[5] - s[3]) < 0.4 and any(
                    o is not s and o[6] > s[6] - 1e-6 and math.hypot(o[4] - o[2], o[5] - o[3]) > 0.4 and
                    inside(s[2], s[3], o) and inside(s[4], s[5], o) for o in by_net[(s[0], s[1])]):
                continue
            tracks.append(s)
        for net, l, x1, y1, x2, y2, w in tracks:
            if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
                continue
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(x1, y1))
            t.SetEnd(P(x2, y2))
            t.SetWidth(mm(float(w)))
            t.SetLayer(LAYER[l])
            t.SetNet(self.net(full[net]))
            self.b.Add(t)
        for net, x, y, dia, drill in self.r.vias:
            v = pcbnew.PCB_VIA(self.b)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetPosition(P(x, y))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetWidth(pcbnew.F_Cu, mm(dia))
            v.SetDrill(mm(drill))
            v.SetNet(self.net(full[net]))
            self.b.Add(v)


def write_project():
    """Board design rules live in the project file: merge them in."""
    with open(PRO, encoding="utf-8") as f:
        pro = json.load(f)
    dsg = pro.setdefault("board", {}).setdefault("design_settings", {})
    dsg.setdefault("rules", {}).update({
        "min_clearance": CLR, "min_track_width": 0.2, "min_copper_edge_clearance": EDGE,
        "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
        "min_through_hole_diameter": 0.3, "min_via_diameter": 0.6, "min_via_annular_width": 0.13,
        "min_resolved_spokes": 1,
    })
    dsg["track_widths"] = [0.0, 0.25, 0.6, 1.0]
    dsg["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}]
    # the schematic exports local nets as "/NAME": make the Power class match them too
    pats = pro["net_settings"]["netclass_patterns"]
    have = {(p["netclass"], p["pattern"]) for p in pats}
    for name, nc in design.NET_CLASSES.items():
        for n in nc["nets"]:
            if (name, "/" + n) not in have:
                pats.append({"netclass": name, "pattern": "/" + n})
    with open(PRO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def fix_islands(b, r):
    """Tie GND zone islands that are not connected to the main plane with an extra via.
    Returns the number of vias added (0 = plane is in one piece or nothing can be done)."""
    gz = {z.GetLayer(): z for z in b.Zones() if z.GetNetname() == "GND" and not z.GetIsRuleArea()}
    polys = {l: z.GetFilledPolysList(l) for l, z in gz.items()}
    isl = [(l, i) for l in polys for i in range(polys[l].OutlineCount())]
    parent = {k: k for k in isl}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    def island(l, pt):
        for i in range(polys[l].OutlineCount()):
            if polys[l].Contains(pt, i):
                return (l, i)
        return None

    links = []
    for v in b.GetTracks():
        if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND":
            links.append(v.GetPosition())
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "GND" and pad.GetDrillSize().x > 0:
                links.append(pad.GetPosition())
    count = {k: 0 for k in isl}
    for pt in links:
        a, c = island(pcbnew.F_Cu, pt), island(pcbnew.B_Cu, pt)
        for k in (a, c):
            if k:
                count[k] += 1
        if a and c:
            parent[find(a)] = find(c)
    size = {}
    for k in isl:
        size[find(k)] = size.get(find(k), 0) + count[k] + 1
    main = max(size, key=size.get)
    fpf = r._free("p", "GND")
    ok = fpf[0] & fpf[1] & ~r.novia & ~r.nearpad
    added = 0
    for (l, i) in isl:
        if find((l, i)) == find(main):
            continue
        other = pcbnew.B_Cu if l == pcbnew.F_Cu else pcbnew.F_Cu
        bb = polys[l].Outline(i).BBox()
        x0, y0 = pcbnew.ToMM(bb.GetLeft()) - OX, pcbnew.ToMM(bb.GetTop()) - OY
        x1, y1 = pcbnew.ToMM(bb.GetRight()) - OX, pcbnew.ToMM(bb.GetBottom()) - OY
        cands = []
        for iy in range(max(0, int(y0 / 0.25)), min(r.ny, int(y1 / 0.25) + 2)):
            for ix in range(max(0, int(x0 / 0.25)), min(r.nx, int(x1 / 0.25) + 2)):
                if ok[iy, ix]:
                    cands.append(((ix * 0.25 - (x0 + x1) / 2) ** 2 + (iy * 0.25 - (y0 + y1) / 2) ** 2, ix, iy))
        done = False
        for _, ix, iy in sorted(cands):
            pt = P(ix * 0.25, iy * 0.25)
            k2 = island(other, pt)
            if polys[l].Contains(pt, i) and k2 and find(k2) == find(main):
                v = pcbnew.PCB_VIA(b)
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetPosition(pt)
                v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetWidth(pcbnew.F_Cu, mm(0.6))
                v.SetDrill(mm(0.3))
                v.SetNet(gz[l].GetNet())
                b.Add(v)
                r.add_via("GND", ix * 0.25, iy * 0.25)
                ok[max(0, iy - 4):iy + 5, max(0, ix - 4):ix + 5] = False
                parent[find((l, i))] = find(main)
                added += 1
                done = True
                break
        if not done:
            print("GND island not tied: %s x %.2f..%.2f y %.2f..%.2f" % (b.GetLayerName(l), x0, x1, y0, y1))
    if added:
        print("added %d vias to tie GND islands to the plane" % added)
    return added


def main():
    noroute = "--noroute" in sys.argv
    bd = Board()
    bd.outline()
    bd.place_all()
    bd.keepout(*KEEPOUT)
    bd.scan_pads()
    if "--pads" in sys.argv:
        for (ref, pin), lst in sorted(bd.pads.items()):
            for p in lst:
                print("%-5s %-4s %-10s %7.3f %7.3f %s" % (ref, pin, p["net"], p["x"], p["y"], p["layers"]))
    if not noroute:
        import pcb_plan
        pcb_plan.route(bd)
    bd.emit_copper()
    import pcb_plan
    pcb_plan.finish(bd, noroute)
    full = [(0, 0), (W, 0), (W, H), (0, H)]
    bd.zone("GND", pcbnew.F_Cu, full, name="GND_F")
    bd.zone("GND", pcbnew.B_Cu, full, name="GND_B")
    write_project()
    pcbnew.SaveBoard(PCB, bd.b)
    # zones are filled on a re-loaded board (the filler needs the project's design rules)
    b2 = pcbnew.LoadBoard(PCB)
    ds = b2.GetDesignSettings()
    ds.m_CopperEdgeClearance = mm(EDGE)
    ds.m_MinClearance = mm(CLR)
    ds.m_TrackMinWidth = mm(0.2)
    ds.m_ViasMinSize = mm(0.6)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_HoleClearance = mm(0.25)
    ds.m_HoleToHoleMin = mm(0.25)
    pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    # GND vias that ended up without copper on one side (plane cut off there) are useless: drop them
    gz = {z.GetLayer(): z for z in b2.Zones() if z.GetNetname() == "GND" and not z.GetIsRuleArea()}
    drop = [v for v in b2.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND" and
            not all(gz[l].HitTestFilledArea(l, v.GetPosition(), 0) for l in (pcbnew.F_Cu, pcbnew.B_Cu))]
    for v in drop:
        b2.Remove(v)
    if drop:
        print("removed %d GND vias without plane on one side" % len(drop))
        pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    for _ in range(4):
        if not fix_islands(b2, bd.r):
            break
        pcbnew.ZONE_FILLER(b2).Fill(b2.Zones())
    pcbnew.SaveBoard(PCB, b2)
    write_project()
    for l in bd.r.log:
        print(l)
    print("wrote %s: %d footprints, %d tracks, %d vias" % (
        PCB, len(bd.fp), len(bd.r.tracks), len(bd.r.vias)))


if __name__ == "__main__":
    main()
