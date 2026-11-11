"""Compare a KiCad netlist (kicad-cli sch export netlist, kicadsexpr format)
against design.py, pin by pin.

    python check_netlist.py [path\\to\\handheld.net]

Exit code 0 = identical, 1 = differences.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design  # noqa: E402
from gen_sch import parse, child, children, unq  # noqa: E402


def load(path):
    with open(path, encoding="utf-8") as f:
        root = parse(f.read())
    comps = {}
    for c in children(child(root, "components"), "comp"):
        ref = unq(child(c, "ref")[1])
        fields = {}
        fl = child(c, "fields")
        if fl:
            for fd in children(fl, "field"):
                name = unq(child(fd, "name")[1])
                fields[name] = unq(fd[2]) if len(fd) > 2 else ""
        fp = child(c, "footprint")
        comps[ref] = {"value": unq(child(c, "value")[1]), "footprint": unq(fp[1]) if fp else "", "fields": fields}
    pin_net, net_nodes = {}, {}
    for n in children(child(root, "nets"), "net"):
        name = unq(child(n, "name")[1])
        for node in children(n, "node"):
            key = (unq(child(node, "ref")[1]), unq(child(node, "pin")[1]))
            if key in pin_net:
                raise SystemExit("pin %s listed twice in netlist" % (key,))
            pin_net[key] = name
            net_nodes.setdefault(name, []).append(key)
    return comps, pin_net, net_nodes


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(HERE, "..", "handheld", "handheld.net"))
    comps, pin_net, net_nodes = load(path)
    errors = []
    expected = {}
    for p in design.PARTS:
        ref = p["ref"]
        if ref not in comps:
            errors.append("%s missing from netlist" % ref)
            continue
        c = comps[ref]
        if c["value"] != p["value"]:
            errors.append("%s value %r != %r" % (ref, c["value"], p["value"]))
        if c["footprint"] != p["footprint"]:
            errors.append("%s footprint %r != %r" % (ref, c["footprint"], p["footprint"]))
        if c["fields"].get("LCSC") != p["lcsc"]:
            errors.append("%s LCSC %r != %r" % (ref, c["fields"].get("LCSC"), p["lcsc"]))
        for pin, net in p["pins"].items():
            expected[(ref, pin)] = net
    for ref in comps:
        if ref not in [p["ref"] for p in design.PARTS]:
            errors.append("%s in netlist but not in design" % ref)

    for key, net in sorted(expected.items()):
        got = pin_net.get(key)
        if got is None:
            errors.append("%s.%s missing from netlist (expected %s)" % (key[0], key[1], net))
        elif net is None:
            if not got.startswith("unconnected-") or len(net_nodes[got]) != 1:
                errors.append("%s.%s should be unconnected, is on %s" % (key[0], key[1], got))
        elif got.lstrip("/") != net:
            errors.append("%s.%s on %s, expected %s" % (key[0], key[1], got, net))
    for key, got in sorted(pin_net.items()):
        if key not in expected:
            errors.append("extra node %s.%s on %s" % (key[0], key[1], got))

    # net membership must match exactly (catches shorts between differently named nets)
    want = design.nets()
    have = {}
    for name, nodes in net_nodes.items():
        if not name.startswith("unconnected-"):
            have[name.lstrip("/")] = sorted(nodes)
    for net in sorted(set(want) | set(have)):
        if want.get(net) != have.get(net):
            errors.append("net %s: design %s / netlist %s" % (net, want.get(net), have.get(net)))

    npins = len(expected)
    nconn = sum(1 for v in expected.values() if v is not None)
    if errors:
        print("NETLIST CHECK FAILED: %d difference(s)" % len(errors))
        for e in errors:
            print("  " + e)
        return 1
    print("NETLIST CHECK OK: %d parts, %d pins (%d connected, %d unconnected), %d nets" % (
        len(design.PARTS), npins, nconn, npins - nconn, len(want)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
