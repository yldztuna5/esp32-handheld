"""Summarise a kicad-cli DRC json report (coordinates shown relative to the board origin)."""
import collections
import json
import sys

OX, OY = 100.0, 50.0
d = json.load(open(sys.argv[1], encoding="utf-8"))
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 12
groups = collections.OrderedDict()
for key in ("violations", "unconnected_items", "schematic_parity"):
    for v in d.get(key, []):
        groups.setdefault((key, v["severity"], v["type"]), []).append(v)
err = sum(len(v) for (k, s, t), v in groups.items() if s == "error" and k != "unconnected_items")
warn = sum(len(v) for (k, s, t), v in groups.items() if s == "warning")
unc = len(d.get("unconnected_items", []))
print("DRC: %d errors, %d warnings, %d unconnected" % (err, warn, unc))
for (k, s, t), vs in groups.items():
    print("== %s %s %s: %d" % (k, s, t, len(vs)))
    for v in vs[:limit]:
        items = "; ".join("%s @(%.2f,%.2f)" % (i["description"], i["pos"]["x"] - OX, i["pos"]["y"] - OY)
                          for i in v.get("items", []))
        print("   %s | %s" % (v["description"], items))
