"""Fabrication outputs for JLCPCB in handheld/fab/ :

    gerbers.zip      Gerbers (Protel extensions) + Excellon drill files
    cpl-jlcpcb.csv   placement file for the assembled parts (assembly == "jlc")
    bom-jlcpcb.csv   copy of the BOM written by bom.py

    python fab.py        (any Python 3; calls kicad-cli)

NOTE: the rotations in the CPL are KiCad's.  JLCPCB's part library uses its own
zero orientation for some packages - check every part in their placement preview.
"""
import csv
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bom  # noqa: E402
import design  # noqa: E402

CLI = os.environ.get("KICAD_CLI", r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe")
PRJ = os.path.normpath(os.path.join(HERE, "..", "handheld"))
PCB = os.path.join(PRJ, design.PROJECT + ".kicad_pcb")
FAB = os.path.join(PRJ, "fab")
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"


def run(*args):
    r = subprocess.run([CLI] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("kicad-cli %s failed:\n%s%s" % (" ".join(args[:3]), r.stdout, r.stderr))


def main():
    tmp = os.path.join(FAB, "g")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    run("pcb", "export", "gerbers", "-o", tmp + os.sep, "--layers", LAYERS, "--no-x2", "--no-netlist",
        "--subtract-soldermask", PCB)
    run("pcb", "export", "drill", "-o", tmp + os.sep, "--format", "excellon", "--drill-origin", "absolute",
        "--excellon-units", "mm", "--excellon-zeros-format", "decimal", "--excellon-oval-format", "alternate",
        "--excellon-separate-th", PCB)
    names = sorted(n for n in os.listdir(tmp) if not n.endswith(".gbrjob"))
    zpath = os.path.join(FAB, "gerbers.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            zi = zipfile.ZipInfo(n, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(tmp, n), "rb") as f:
                z.writestr(zi, f.read())
    # placement
    pos = os.path.join(tmp, "pos.csv")
    run("pcb", "export", "pos", "-o", pos, "--format", "csv", "--units", "mm", "--side", "both", PCB)
    want = {p["ref"] for p in design.assembled_parts()}
    rows = []
    with open(pos, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["Ref"] in want:
                rows.append([r["Ref"], "%.4f" % float(r["PosX"]), "%.4f" % float(r["PosY"]),
                             "Top" if r["Side"] == "top" else "Bottom", "%g" % (float(r["Rot"]) % 360)])
    missing = want - {r[0] for r in rows}
    if missing:
        raise SystemExit("parts missing from the position file: %s" % sorted(missing))
    rows.sort(key=lambda r: bom.ref_key(r[0]))
    with open(os.path.join(FAB, "cpl-jlcpcb.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writerows(rows)
    bom.main()
    shutil.copyfile(os.path.join(PRJ, "bom-jlcpcb.csv"), os.path.join(FAB, "bom-jlcpcb.csv"))
    shutil.rmtree(tmp)
    print("gerbers.zip: %s" % ", ".join(names))
    print("cpl-jlcpcb.csv: %d parts (%d top)" % (len(rows), sum(r[3] == "Top" for r in rows)))


if __name__ == "__main__":
    main()
