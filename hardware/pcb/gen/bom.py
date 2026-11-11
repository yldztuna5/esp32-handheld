"""Write handheld/bom-jlcpcb.csv (JLCPCB assembly BOM) from design.py.

Only parts with assembly == "jlc" are listed; hand-soldered parts, test pads,
solder jumpers and mounting holes are left out.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402


def ref_key(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2)))


def main():
    groups = {}
    for p in design.assembled_parts():
        if not p["lcsc"]:
            raise SystemExit("%s is assembled but has no LCSC number" % p["ref"])
        key = (p["value"], p["footprint"].split(":")[1], p["lcsc"])
        groups.setdefault(key, []).append(p["ref"])
    rows = sorted(groups.items(), key=lambda kv: ref_key(sorted(kv[1], key=ref_key)[0]))
    path = os.path.normpath(os.path.join(HERE, "..", "handheld", "bom-jlcpcb.csv"))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (value, fp, lcsc), refs in rows:
            w.writerow([value, ",".join(sorted(refs, key=ref_key)), fp, lcsc])
    print("wrote %s: %d lines, %d parts" % (path, len(rows), sum(len(r) for r in groups.values())))


if __name__ == "__main__":
    main()
