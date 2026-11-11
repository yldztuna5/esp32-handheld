"""Generate project footprints into handheld/handheld.pretty.

TPS63020_DSJ  (TI DSJ / R-PVSON-N14, VSON-14 3x4 mm, 0.5 mm pitch; short name keeps the path under MAX_PATH)
  Drawn from the TI land pattern 4210895-2/E (datasheet SLVS916I, "LAND PATTERN DATA",
  DSJ R-PVSON-N14), rotated so that pin 1 is top-left:
    - 14 oblong pads 0.24 x 0.60 mm, pitch 0.5 mm, rows 2.8 mm apart
    - thermal land 1.58 x 2.85 mm with 4 fingers at each short end
      (inner 0.20 mm wide, outer 0.23 mm wide, 0.46 mm pitch, overall length 4.4 mm)
    - paste: 4 x (0.66 x 1.25 mm) on the thermal land, full aperture on the fingers and pads
  Thermal vias (TI: 15 x d0.2 mm on a 0.5 mm grid) are left to the PCB generator.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "handheld", "handheld.pretty"))
NAME = "TPS63020_DSJ"


def n(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def line(x1, y1, x2, y2, layer, w):
    return '\t(fp_line (start %s %s) (end %s %s) (stroke (width %s) (type solid)) (layer "%s"))' % (
        n(x1), n(y1), n(x2), n(y2), n(w), layer)


def rect(x, y, layer, w):
    return [line(-x, -y, x, -y, layer, w), line(x, -y, x, y, layer, w),
            line(x, y, -x, y, layer, w), line(-x, y, -x, -y, layer, w)]


def pad(num, shape, x, y, w, h, layers):
    return '\t(pad "%s" smd %s (at %s %s) (size %s %s) (layers %s))' % (
        num, shape, n(x), n(y), n(w), n(h), " ".join('"%s"' % l for l in layers))


def text_prop(name, value, y, layer, hide=False):
    return ('\t(property "%s" "%s" (at 0 %s 0) (layer "%s")%s (effects (font (size 1 1) (thickness 0.15))))'
            % (name, value, n(y), layer, " (hide yes)" if hide else ""))


def dsj():
    o = ['(footprint "%s"' % NAME, '\t(version 20241229)', '\t(generator "gen_fp.py")', '\t(layer "F.Cu")',
         '\t(descr "TI DSJ (R-PVSON-N14) 3x4mm, 0.5mm pitch, thermal pad with fingers; land pattern TI 4210895-2/E (TPS63020 datasheet SLVS916)")',
         '\t(tags "VSON DFN 14 DSJ TPS63020")',
         text_prop("Reference", "REF**", -3.4, "F.SilkS"),
         text_prop("Value", NAME, 3.4, "F.Fab"),
         text_prop("Datasheet", "https://www.ti.com/lit/ds/symlink/tps63020.pdf", 0, "F.Fab", True),
         text_prop("Description", "TI DSJ VSON-14 3x4mm", 0, "F.Fab", True),
         '\t(attr smd)']
    # body 3.0 (x) x 4.0 (y)
    o += [line(-0.75, -2, 1.5, -2, "F.Fab", 0.1), line(1.5, -2, 1.5, 2, "F.Fab", 0.1),
          line(1.5, 2, -1.5, 2, "F.Fab", 0.1), line(-1.5, 2, -1.5, -1.25, "F.Fab", 0.1),
          line(-1.5, -1.25, -0.75, -2, "F.Fab", 0.1)]
    o += rect(1.95, 2.45, "F.CrtYd", 0.05)
    # silk: short marks at the four corners (clear of the exposed fingers) + pin-1 dot
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(line(sx * 1.15, sy * 2.15, sx * 1.6, sy * 2.15, "F.SilkS", 0.12))
    o.append('\t(fp_circle (center -2.2 -1.5) (end -2.1 -1.5) (stroke (width 0.2) (type solid)) (fill yes) (layer "F.SilkS"))')
    o.append('\t(fp_text user "${REFERENCE}" (at 0 0 90) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.105))))')
    smd = ["F.Cu", "F.Mask", "F.Paste"]
    for i in range(7):
        o.append(pad(str(i + 1), "oval", -1.4, -1.5 + 0.5 * i, 0.6, 0.24, smd))
    for i in range(7):
        o.append(pad(str(8 + i), "oval", 1.4, 1.5 - 0.5 * i, 0.6, 0.24, smd))
    # thermal land (pad 15): centre without paste, 4 paste windows, 8 fingers
    o.append(pad("15", "rect", 0, 0, 1.58, 2.85, ["F.Cu", "F.Mask"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            o.append(pad("", "rect", sx * 0.43, sy * 0.725, 0.66, 1.25, ["F.Paste"]))
    flen = (4.4 - 2.85) / 2
    for sy in (-1, 1):
        yc = sy * (2.85 / 2 + flen / 2)
        for xc, w in ((-0.675, 0.23), (-0.23, 0.2), (0.23, 0.2), (0.675, 0.23)):
            o.append(pad("15", "rect", xc, yc, w, flen, smd))
    o.append('\t(embedded_fonts no)')
    o.append('\t(model "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/DFN-14-1EP_3x4mm_P0.5mm_EP1.7x3.3mm.wrl"'
             ' (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    o.append(')')
    return "\n".join(o) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, NAME + ".kicad_mod")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dsj())
    print("wrote", path)


if __name__ == "__main__":
    main()
