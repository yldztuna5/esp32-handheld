"""Check handheld.kicad_pcb against design.py: every part present with the right
footprint, every pad on the net design.py says, SMD parts on the back only.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" check_pcb.py

Exit code 0 = identical, 1 = differences.  Also prints board statistics.
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402

FRONT_OK = ("J4", "J5", "SW4", "SW5", "SW6", "SW7", "SW8", "SW9", "SW10", "SW11")


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(HERE, "..", "handheld", design.PROJECT + ".kicad_pcb"))
    b = pcbnew.LoadBoard(path)
    errors = []
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    npads = 0
    for p in design.PARTS:
        ref = p["ref"]
        fp = fps.get(ref)
        if fp is None:
            errors.append("%s missing on the board" % ref)
            continue
        fpid = "%s:%s" % (fp.GetFPID().GetLibNickname(), fp.GetFPID().GetLibItemName())
        if fpid != p["footprint"]:
            errors.append("%s footprint %s != %s" % (ref, fpid, p["footprint"]))
        if fp.GetValue() != p["value"]:
            errors.append("%s value %r != %r" % (ref, fp.GetValue(), p["value"]))
        back = fp.GetLayer() == pcbnew.B_Cu
        if not back and ref not in FRONT_OK and not ref.startswith("H"):
            errors.append("%s is on the front" % ref)
        if back and ref in FRONT_OK:
            errors.append("%s is on the back" % ref)
        seen = set()
        for pad in fp.Pads():
            num = pad.GetNumber()
            name = pad.GetNetname()
            if not num:
                if name:
                    errors.append("%s unnumbered pad on net %s" % (ref, name))
                continue
            npads += 1
            if num not in p["pins"]:
                if name:
                    errors.append("%s.%s not in design but on net %s" % (ref, num, name))
                continue
            seen.add(num)
            want = p["pins"][num]
            if want is None:
                if name and not name.startswith("unconnected-"):
                    errors.append("%s.%s should be unconnected, is on %s" % (ref, num, name))
            elif name.lstrip("/") != want:
                errors.append("%s.%s on %r, expected %s" % (ref, num, name, want))
        for pin in p["pins"]:
            if pin not in seen:
                errors.append("%s.%s has no pad" % (ref, pin))
    for ref in fps:
        if ref not in [p["ref"] for p in design.PARTS]:
            errors.append("%s on the board but not in design" % ref)
    # copper items must be on design nets too
    known = set(design.nets())
    for t in b.GetTracks():
        if t.GetNetname().lstrip("/") not in known:
            errors.append("track/via on unknown net %r" % t.GetNetname())
            break

    tracks = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
    vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    bb = b.GetBoardEdgesBoundingBox()
    fcu = sum(pcbnew.ToMM(t.GetLength()) for t in tracks if t.GetLayer() == pcbnew.F_Cu)
    bcu = sum(pcbnew.ToMM(t.GetLength()) for t in tracks if t.GetLayer() == pcbnew.B_Cu)
    print("board %.1f x %.1f mm, %d footprints, %d pads checked" % (
        pcbnew.ToMM(bb.GetWidth()) - 0.1, pcbnew.ToMM(bb.GetHeight()) - 0.1, len(fps), npads))
    print("tracks: %d segments (F.Cu %.0f mm, B.Cu %.0f mm), min width %.2f mm; vias: %d" % (
        len(tracks), fcu, bcu, min(pcbnew.ToMM(t.GetWidth()) for t in tracks) if tracks else 0, len(vias)))
    if errors:
        print("PCB CHECK FAILED: %d difference(s)" % len(errors))
        for e in errors:
            print("  " + e)
        return 1
    print("PCB CHECK OK: all pad nets equal design.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
