import re, sys
LIB = r"C:\Program Files\KiCad\9.0\share\kicad\symbols"

def find_block(text, start):
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1

def get_symbol(lib, name):
    text = open(f"{LIB}\\{lib}.kicad_sym", encoding="utf-8").read()
    m = re.search(r'\n\t\(symbol "' + re.escape(name) + '"', text)
    return find_block(text, m.start() + 2)

for spec in sys.argv[1:]:
    lib, name = spec.split(":")
    blk = get_symbol(lib, name)
    ext = re.search(r'\(extends "([^"]+)"\)', blk)
    print("==", spec, "extends", ext.group(1) if ext else None)
    for pm in re.finditer(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length ([\d.]+)\)(.*?)\(name "([^"]*)".*?\(number "([^"]*)"', blk, re.S):
        hidden = "hide" in pm.group(7)
        print(f"  {pm.group(9):>4} {pm.group(8):<14} {pm.group(1):<14} at {pm.group(3)},{pm.group(4)} r{pm.group(5)}{' HIDDEN' if hidden else ''}")
    fp = re.search(r'\(property "Footprint" "([^"]*)"', blk)
    print("  footprint:", fp.group(1) if fp else None)
