"""Small two-layer grid router used by gen_pcb.py (pure Python + numpy).

Coordinates are board millimetres (origin = top-left board corner, front view).
Layer index 0 = F.Cu, 1 = B.Cu.

Obstacle model: for every width class (half track width hw) there is an
"owner" grid per layer.  A node is owned by net n if copper of net n is closer
than clearance + hw (+ margin) to it, -1 if copper of several nets (or a
no-net obstacle) is that close, 0 if free.  A track of net n and that width may
be centred on a node whose owner is 0 or n.
"""
import heapq
import math
import time

import numpy as np

PITCH = 0.25
MARGIN = 0.03          # extra distance on top of the nominal clearance
CLASSES = {"s": 0.125, "p": 0.3, "w": 0.5}     # half widths: signal, power, wide power
WIDTH = {"s": 0.25, "p": 0.6, "w": 1.0}
VIA_R = 0.3
SOFT = 6.0             # cost of crossing a routed track in a rip-up search (per node)
MAX_RIPS = 600
HWEIGHT = 2.0         # A* heuristic weight (>1: faster, slightly longer paths)
VIA_DRILL = 0.3
F, B = 0, 1

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
DLEN = [PITCH if dx == 0 or dy == 0 else PITCH * math.sqrt(2) for dx, dy in DIRS]


class Router:
    def __init__(self, w, h, clearance=0.2):
        self.w, self.h, self.clr = w, h, clearance
        self.nx = int(round(w / PITCH)) + 1
        self.ny = int(round(h / PITCH)) + 1
        self.own = {c: np.zeros((2, self.ny, self.nx), np.int16) for c in CLASSES}
        self.novia = np.zeros((self.ny, self.nx), bool)      # hole-to-hole spacing
        self.nearpad = np.zeros((self.ny, self.nx), bool)    # no vias on / touching SMD pads
        self.xs = np.arange(self.nx) * PITCH
        self.ys = np.arange(self.ny) * PITCH
        self.netid = {}
        self.comps = {}        # net -> list of sets of cell ids
        self.padcell = {}      # cell id -> pad centre (x, y) for snapping track ends
        self.tracks = []       # (net, layer, x1, y1, x2, y2, width)
        self.vias = []         # (net, x, y)
        self.grounded = set()  # cells that are solidly GND (for gnd stubs)
        self.log = []
        self.verbose = True
        self.mazing = False
        self.requeue = []
        self.ripcount = {}
        self.total_rips = 0
        self.last_exp = 0

    # ------------------------------------------------------------ helpers --
    def nid(self, net):
        if net not in self.netid:
            self.netid[net] = len(self.netid) + 1
        return self.netid[net]

    def cell(self, l, iy, ix):
        return (l * self.ny + iy) * self.nx + ix

    def uncell(self, c):
        ix = c % self.nx
        r = c // self.nx
        return r // self.ny, r % self.ny, ix

    def node(self, x, y):
        return int(round(y / PITCH)), int(round(x / PITCH))

    def on_grid(self, x, y):
        return abs(x / PITCH - round(x / PITCH)) < 1e-6 and abs(y / PITCH - round(y / PITCH)) < 1e-6

    def _window(self, x0, y0, x1, y1):
        ix0 = max(0, int(math.floor(x0 / PITCH)))
        ix1 = min(self.nx, int(math.ceil(x1 / PITCH)) + 1)
        iy0 = max(0, int(math.floor(y0 / PITCH)))
        iy1 = min(self.ny, int(math.ceil(y1 / PITCH)) + 1)
        if ix0 >= ix1 or iy0 >= iy1:
            return None
        X, Y = np.meshgrid(self.xs[ix0:ix1], self.ys[iy0:iy1])
        return ix0, ix1, iy0, iy1, X, Y

    @staticmethod
    def _dist(shape, X, Y):
        k = shape[0]
        if k == "rect":            # cx, cy, hx, hy
            _, cx, cy, hx, hy = shape
            dx = np.maximum(np.abs(X - cx) - hx, 0)
            dy = np.maximum(np.abs(Y - cy) - hy, 0)
            return np.hypot(dx, dy)
        if k == "circle":          # cx, cy, r
            _, cx, cy, r = shape
            return np.maximum(np.hypot(X - cx, Y - cy) - r, 0)
        if k == "seg":             # x1, y1, x2, y2, r
            _, x1, y1, x2, y2, r = shape
            vx, vy = x2 - x1, y2 - y1
            L2 = vx * vx + vy * vy
            if L2 < 1e-12:
                return np.maximum(np.hypot(X - x1, Y - y1) - r, 0)
            t = np.clip(((X - x1) * vx + (Y - y1) * vy) / L2, 0, 1)
            return np.maximum(np.hypot(X - (x1 + t * vx), Y - (y1 + t * vy)) - r, 0)
        if k == "poly":            # list of points
            pts = shape[1]
            d = np.full(X.shape, 1e9)
            inside = np.zeros(X.shape, bool)
            n = len(pts)
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                d = np.minimum(d, Router._dist(("seg", x1, y1, x2, y2, 0), X, Y))
                if y1 != y2:
                    cond = ((y1 > Y) != (y2 > Y)) & (X < (x2 - x1) * (Y - y1) / (y2 - y1) + x1)
                    inside ^= cond
            d[inside] = 0
            return d
        raise ValueError(k)

    @staticmethod
    def _bbox(shape):
        k = shape[0]
        if k == "rect":
            return shape[1] - shape[3], shape[2] - shape[4], shape[1] + shape[3], shape[2] + shape[4]
        if k == "circle":
            return shape[1] - shape[3], shape[2] - shape[3], shape[1] + shape[3], shape[2] + shape[3]
        if k == "seg":
            r = shape[5]
            return (min(shape[1], shape[3]) - r, min(shape[2], shape[4]) - r,
                    max(shape[1], shape[3]) + r, max(shape[2], shape[4]) + r)
        xs = [p[0] for p in shape[1]]
        ys = [p[1] for p in shape[1]]
        return min(xs), min(ys), max(xs), max(ys)

    def stamp(self, shape, layers, net, clr=None):
        """Mark copper `shape` of `net` (None = obstacle for everybody) on `layers`."""
        clr = self.clr if clr is None else clr
        n = -1 if net is None else self.nid(net)
        bx0, by0, bx1, by1 = self._bbox(shape)
        for c, hw in CLASSES.items():
            r = clr + hw + MARGIN
            win = self._window(bx0 - r, by0 - r, bx1 + r, by1 + r)
            if win is None:
                continue
            ix0, ix1, iy0, iy1, X, Y = win
            m = self._dist(shape, X, Y) < r
            for l in layers:
                sub = self.own[c][l, iy0:iy1, ix0:ix1]
                if n < 0:
                    sub[m] = -1
                else:
                    other = m & (sub != 0) & (sub != n)
                    sub[m & (sub == 0)] = n
                    sub[other] = -1

    def stamp_bool(self, arr, shape, r):
        bx0, by0, bx1, by1 = self._bbox(shape)
        win = self._window(bx0 - r, by0 - r, bx1 + r, by1 + r)
        if win is None:
            return
        ix0, ix1, iy0, iy1, X, Y = win
        arr[iy0:iy1, ix0:ix1] |= self._dist(shape, X, Y) < r

    def cells_in(self, shape, layers, inset=0.0):
        """Grid nodes inside `shape` (shrunk by inset)."""
        bx0, by0, bx1, by1 = self._bbox(shape)
        win = self._window(bx0, by0, bx1, by1)
        out = set()
        if win is None:
            return out
        ix0, ix1, iy0, iy1, X, Y = win
        if shape[0] == "rect" and inset:
            shape = ("rect", shape[1], shape[2], max(shape[3] - inset, 0), max(shape[4] - inset, 0))
        m = self._dist(shape, X, Y) <= 1e-9
        for iy, ix in zip(*np.nonzero(m)):
            for l in layers:
                out.add(self.cell(l, int(iy) + iy0, int(ix) + ix0))
        return out

    # --------------------------------------------------------- components --
    def add_comp(self, net, cells):
        """Add copper cells of a net; merges with every component it touches."""
        cells = set(cells)
        if not cells:
            return cells
        lst = self.comps.setdefault(net, [])
        keep = []
        for c in lst:
            if c & cells:
                cells |= c
            else:
                keep.append(c)
        keep.append(cells)
        self.comps[net] = keep
        return cells

    def merge(self, net, cell_a, cell_b):
        lst = self.comps[net]
        a = next(c for c in lst if cell_a in c)
        b = next(c for c in lst if cell_b in c)
        if a is not b:
            lst.remove(b)
            a |= b

    def add_pad(self, net, shape, layers, centre, hole=None, smd=True):
        self.stamp(shape, layers, net)
        cells = self.cells_in(shape, layers)
        if not cells:
            iy, ix = self.node(*centre)
            cells = {self.cell(l, iy, ix) for l in layers}
        for c in cells:
            self.padcell[c] = centre
        if hole:
            self.stamp_bool(self.novia, ("circle", centre[0], centre[1], hole / 2), 0.25 + VIA_DRILL / 2 + MARGIN)
        if smd:
            self.stamp_bool(self.nearpad, shape, VIA_R + 0.05)
        if net is not None:
            return self.add_comp(net, cells)
        return cells

    def add_track(self, net, layer, pts, width):
        """Explicit track (list of points).  On-grid points become routable copper."""
        cells = set()
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.tracks.append((net, layer, x1, y1, x2, y2, width))
            self.stamp(("seg", x1, y1, x2, y2, width / 2), [layer], net)
            n = max(1, int(round(max(abs(x2 - x1), abs(y2 - y1)) / PITCH)))
            for i in range(n + 1):
                x, y = x1 + (x2 - x1) * i / n, y1 + (y2 - y1) * i / n
                if self.on_grid(x, y):
                    cells.add(self.cell(layer, *self.node(x, y)))
        # merge with pads / copper touched by the end points
        for x, y in (pts[0], pts[-1]):
            iy, ix = self.node(x, y)
            c0 = self.cell(layer, iy, ix)
            for comp in self.comps.get(net, []):
                if c0 in comp:
                    cells.add(c0)
        return self.add_comp(net, cells)

    def add_via(self, net, x, y, r=VIA_R, drill=VIA_DRILL):
        self.vias.append((net, x, y, 2 * r, drill))
        self.stamp(("circle", x, y, r), [F, B], net)
        self.stamp_bool(self.novia, ("circle", x, y, drill / 2), 0.25 + VIA_DRILL / 2 + MARGIN)
        if self.on_grid(x, y):
            iy, ix = self.node(x, y)
            cells = {self.cell(F, iy, ix), self.cell(B, iy, ix)}
            if net == "GND":
                self.grounded |= cells
            return self.add_comp(net, cells)

    def add_pour(self, net, layer, pts):
        """Copper pour polygon of `net` (KiCad fills it; modelled as solid here)."""
        shape = ("poly", pts)
        self.stamp(shape, [layer], net)
        return self.add_comp(net, self.cells_in(shape, [layer]))

    def join(self, net, pads):
        """Declare pad component sets as connected (by a pour / explicit copper)."""
        lst = self.comps[net]
        base = None
        for p in pads:
            c = next(iter(p))
            comp = next(k for k in lst if c in k)
            if base is None:
                base = comp
            elif comp is not base:
                lst.remove(comp)
                base |= comp

    def ascii(self, net, l, cx, cy, half=3.0):
        """Text picture of the signal-class owner grid around a point (debugging)."""
        sym = "123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        n = self.nid(net)
        iy0, ix0 = self.node(cx - half, cy - half)
        iy1, ix1 = self.node(cx + half, cy + half)
        names = {v: k for k, v in self.netid.items()}
        seen = {}
        rows = ["   x %.2f..%.2f  y %.2f..%.2f  (* = %s, . free, # several nets)" % (
            ix0 * PITCH, ix1 * PITCH, iy0 * PITCH, iy1 * PITCH, net)]
        for iy in range(max(iy0, 0), min(iy1, self.ny - 1) + 1):
            row = ""
            for ix in range(max(ix0, 0), min(ix1, self.nx - 1) + 1):
                v = int(self.own["s"][l, iy, ix])
                if v == 0:
                    row += "."
                elif v == n:
                    row += "*"
                elif v < 0:
                    row += "#"
                else:
                    seen.setdefault(v, sym[len(seen) % len(sym)])
                    row += seen[v]
            rows.append("   " + row)
        rows.append("   " + " ".join("%s=%s" % (c, names[v]) for v, c in seen.items()))
        return "\n".join(rows)

    def png(self, path, layer, scale=4, x0=0.0, y0=0.0, x1=None, y1=None):
        """Debug picture of the signal-class owner grid of one layer."""
        import struct
        import zlib
        iy0, ix0 = self.node(x0, y0)
        iy1, ix1 = self.node(self.w if x1 is None else x1, self.h if y1 is None else y1)
        o = self.own["s"][layer, iy0:iy1 + 1, ix0:ix1 + 1]
        pal = np.zeros((len(self.netid) + 2, 3), np.uint8)
        rng = np.random.RandomState(7)
        pal[1:-1] = rng.randint(90, 256, (len(self.netid), 3))
        pal[0] = (40, 40, 40)
        pal[-1] = (0, 0, 0)
        if "GND" in self.netid:
            pal[self.netid["GND"]] = (0, 90, 0)
        img = pal[np.where(o < 0, len(self.netid) + 1, o)]
        if layer == B:
            pass
        img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
        raw = b"".join(b"\x00" + img[i].tobytes() for i in range(img.shape[0]))

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", img.shape[1], img.shape[0], 8, 2, 0, 0, 0)) +
                    chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))

    # ---------------------------------------------------------------- A* ---
    def _free(self, cls, net):
        n = self.nid(net)
        o = self.own[cls]
        return ((o == 0) | (o == n))

    def search(self, net, src, dst, power=False, layers=(F, B), fcost=2.0, via_cost=4.0,
               allow_via=True, max_exp=1500000, via_target=None, soft=False):
        """A* from the cell set src to the cell set dst.  Returns list of (l, iy, ix).
        soft=True: only fixed copper blocks; crossing routed tracks costs SOFT per node
        (used to find out which nets to rip up)."""
        nx, ny = self.nx, self.ny
        fs = self._free("s", net)
        fp = self._free("p", net)
        if soft:
            n = self.nid(net)
            cur = fs.tobytes()
            fs = (self.fix["s"] == 0) | (self.fix["s"] == n)
            fpx = (self.fix["p"] == 0) | (self.fix["p"] == n)
            curvia = (fp[0] & fp[1] & ~self.novia).tobytes()
            viaok = (fpx[0] & fpx[1] & ~self.novia_fix & ~self.nearpad).tobytes()
        else:
            viaok = (fp[0] & fp[1] & ~self.novia & ~self.nearpad).tobytes()
        free = fs.tobytes()
        if power:
            penb = np.where(self._free("w", net), 0, np.where(fp, 1, 2)).astype(np.uint8).tobytes()
            pent = (1.0, 1.25, 3.0)
        dstb = bytearray(2 * ny * nx)
        xs0 = ys0 = 10 ** 9
        xs1 = ys1 = -1
        for c in dst:
            dstb[c] = 1
            l, iy, ix = self.uncell(c)
            xs0, xs1, ys0, ys1 = min(xs0, ix), max(xs1, ix), min(ys0, iy), max(ys1, iy)
        if via_target is not None:        # any node where a GND via fits is a target (layer B)
            xs0, xs1, ys0, ys1 = 0, nx - 1, 0, ny - 1
        plane = ny * nx
        lcost = [fcost if l == F else 1.0 for l in (0, 1)]
        if len(layers) == 1:
            allow_via = False

        def h(iy, ix):
            dx = xs0 - ix if ix < xs0 else (ix - xs1 if ix > xs1 else 0)
            dy = ys0 - iy if iy < ys0 else (iy - ys1 if iy > ys1 else 0)
            return HWEIGHT * PITCH * (max(dx, dy) + 0.4142 * min(dx, dy))

        g = {}
        parent = {}
        heap = []
        for c in src:
            l, iy, ix = self.uncell(c)
            if l not in layers:
                continue
            s = (c, 8)
            g[s] = 0.0
            heapq.heappush(heap, (h(iy, ix), 0.0, c, 8))
        exp = 0
        goal = None
        while heap:
            f, gc, c, d = heapq.heappop(heap)
            if g.get((c, d), 1e18) < gc - 1e-9:
                continue
            if dstb[c] or (via_target is not None and c >= plane and via_target[c - plane]
                           and d != 8):
                goal = (c, d)
                break
            exp += 1
            if exp > max_exp:
                break
            l = c // plane
            rem = c - l * plane
            iy = rem // nx
            ix = rem - iy * nx
            base = l * plane
            for nd in range(8):
                if d != 8:
                    turn = (nd - d) % 8
                    if turn > 4:
                        turn = 8 - turn
                    if turn > 2:
                        continue
                else:
                    turn = 0
                dx, dy = DIRS[nd]
                jx, jy = ix + dx, iy + dy
                if jx < 0 or jy < 0 or jx >= nx or jy >= ny:
                    continue
                c2 = base + jy * nx + jx
                if not free[c2]:
                    continue
                if dx and dy and not (free[base + iy * nx + jx] and free[base + jy * nx + ix]):
                    continue
                step = DLEN[nd] * lcost[l]
                if power:
                    step *= pent[penb[c2]]
                if soft and not cur[c2]:
                    step += SOFT
                ng = gc + step + (0.0 if turn == 0 else (0.05 if turn == 1 else 0.4))
                s2 = (c2, nd)
                if ng < g.get(s2, 1e18):
                    g[s2] = ng
                    parent[s2] = (c, d)
                    heapq.heappush(heap, (ng + h(jy, jx), ng, c2, nd))
            if allow_via and viaok[rem]:
                c2 = (1 - l) * plane + rem
                if free[c2]:
                    ng = gc + via_cost
                    if soft and not (curvia[rem] and cur[c2]):
                        ng += 2 * SOFT
                    s2 = (c2, 8)
                    if ng < g.get(s2, 1e18):
                        g[s2] = ng
                        parent[s2] = (c, d)
                        heapq.heappush(heap, (ng + h(iy, ix), ng, c2, 8))
        self.last_exp = exp
        if goal is None:
            return None
        path = []
        s = goal
        while s is not None:
            path.append(self.uncell(s[0]))
            s = parent.get(s)
        path.reverse()
        return path

    # ------------------------------------------------------------ commit ---
    def _cls_at(self, net, l, iy, ix, power):
        if not power:
            return "s"
        n = self.nid(net)
        for c in ("w", "p"):
            o = self.own[c]
            ok = True
            for dy in (-1, 0, 1):          # node and its neighbours (covers diagonals)
                for dx in (-1, 0, 1):
                    v = o[l, min(max(iy + dy, 0), self.ny - 1), min(max(ix + dx, 0), self.nx - 1)]
                    if v != 0 and v != n:
                        ok = False
            if ok:
                return c
        return "s"

    def _twin_via(self, net, path, i):
        """Second via for a power net: 3 nodes back (or ahead) along the path, linked on
        the other layer by a 0.6 mm track."""
        n = self.nid(net)
        op = self.own["p"]
        for idx, tl in ((range(i - 3, i + 1), path[i + 1][0]), (range(i + 4, i, -1), path[i][0])):
            idx = list(idx)
            if idx[0] < 0 or max(idx) >= len(path):
                continue
            nodes = [path[k] for k in idx]
            if len({p[0] for p in nodes}) != 1 or nodes[0][0] == tl:
                continue
            _, iy, ix = nodes[0]
            if self.novia[iy, ix] or self.nearpad[iy, ix]:
                continue
            if any(op[l, iy, ix] not in (0, n) for l in (F, B)):
                continue
            if any(op[tl, p[1], p[2]] not in (0, n) for p in nodes):
                continue
            self.add_via(net, ix * PITCH, iy * PITCH)
            for p, q in zip(nodes, nodes[1:]):
                seg = (net, tl, p[2] * PITCH, p[1] * PITCH, q[2] * PITCH, q[1] * PITCH, WIDTH["p"])
                self.tracks.append(seg)
                self.stamp(("seg",) + seg[2:6] + (WIDTH["p"] / 2,), [tl], net)
            return

    def commit(self, net, path, power=False, max_cls="w", snap=True):
        """Turn a node path into tracks / vias, stamp it and add it to the net."""
        order = ["s", "p", "w"]
        cells = set()
        pts = []           # (l, x, y, cls)
        for l, iy, ix in path:
            cells.add(self.cell(l, iy, ix))
            c = self._cls_at(net, l, iy, ix, power)
            if order.index(c) > order.index(max_cls):
                c = max_cls
            pts.append((l, ix * PITCH, iy * PITCH, c))
        segs = []          # (layer, x1, y1, x2, y2, cls)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            if a[0] != b[0]:
                self.add_via(net, a[1], a[2])
                continue
            cls = a[3] if order.index(a[3]) < order.index(b[3]) else b[3]
            if segs:
                s = segs[-1]
                if (s[0] == a[0] and s[5] == cls and abs(s[3] - a[1]) < 1e-9 and abs(s[4] - a[2]) < 1e-9 and
                        abs((s[3] - s[1]) * (b[2] - a[2]) - (s[4] - s[2]) * (b[1] - a[1])) < 1e-9):
                    segs[-1] = (s[0], s[1], s[2], b[1], b[2], cls)
                    continue
            segs.append((a[0], a[1], a[2], b[1], b[2], cls))
        if snap:           # extend the ends to the pad centres
            for end in (0, -1):
                l, iy, ix = path[end]
                pc = self.padcell.get(self.cell(l, iy, ix))
                x, y = ix * PITCH, iy * PITCH
                if pc and (abs(pc[0] - x) > 1e-6 or abs(pc[1] - y) > 1e-6):
                    self.tracks.append((net, l, x, y, pc[0], pc[1], WIDTH["s"]))
        for l, x1, y1, x2, y2, cls in segs:
            w = WIDTH[cls]
            self.tracks.append((net, l, x1, y1, x2, y2, w))
            self.stamp(("seg", x1, y1, x2, y2, w / 2), [l], net)
        return self.add_comp(net, cells)

    def route_net(self, net, power=False, first=None, **kw):
        """Connect all components of a net.  Returns number of failed connections."""
        fails = 0
        lst = self.comps.get(net, [])
        while len(self.comps[net]) > 1:
            lst = self.comps[net]
            # search from the smallest component: if it is fenced in, that is found quickly
            start = min(lst, key=len)
            dst = set()
            for c in lst:
                if c is not start:
                    dst |= c
            t0 = time.time()
            path = self.search(net, start, dst, power=power, **kw)
            if self.verbose:
                print("  %-12s %s exp %7d  %.1fs" % (net, "ok  " if path else "FAIL", self.last_exp, time.time() - t0),
                      flush=True)
            if path is None and self.mazing and self.total_rips < MAX_RIPS and self.ripcount.get(net, 0) < 12:
                sp = self.search(net, start, dst, power=power, soft=True, **kw)
                bl = self.blockers(net, sp) if sp else []
                if bl:
                    self.ripcount[net] = self.ripcount.get(net, 0) + 1
                    self.total_rips += len(bl)
                    if self.verbose:
                        print("  %-12s rips %s" % (net, " ".join(bl)), flush=True)
                    for m in bl:
                        self.rip(m)
                        if m not in self.requeue:
                            self.requeue.append(m)
                    self.rebuild()
                    continue
            if path is None:
                fails += 1
                # give up on the smallest other component so the loop ends
                other = min((c for c in lst if c is not start), key=len)
                l, iy, ix = self.uncell(next(iter(other)))
                self.log.append("FAILED %s: component at (%.2f, %.2f) layer %d" % (net, ix * PITCH, iy * PITCH, l))
                self.log.append(self.ascii(net, l, ix * PITCH, iy * PITCH))
                lst.remove(other)
                continue
            self.commit(net, path, power=power)
        return fails

    # ------------------------------------------------------------ rip-up ---
    def begin_maze(self):
        """Everything stamped so far is fixed; later tracks / vias can be ripped up."""
        self.fix = {c: a.copy() for c, a in self.own.items()}
        self.novia_fix = self.novia.copy()
        self.base = {net: [set(c) for c in lst] for net, lst in self.comps.items()}
        self.nfix_t, self.nfix_v = len(self.tracks), len(self.vias)
        self.mazing = True

    def rip(self, net):
        self.tracks[self.nfix_t:] = [t for t in self.tracks[self.nfix_t:] if t[0] != net]
        self.vias[self.nfix_v:] = [v for v in self.vias[self.nfix_v:] if v[0] != net]
        self.comps[net] = [set(c) for c in self.base[net]]

    def rebuild(self):
        for c in self.own:
            self.own[c][:] = self.fix[c]
        self.novia[:] = self.novia_fix
        for net, l, x1, y1, x2, y2, w in self.tracks[self.nfix_t:]:
            self.stamp(("seg", x1, y1, x2, y2, w / 2), [l], net)
        for net, x, y, dia, drill in self.vias[self.nfix_v:]:
            self.stamp(("circle", x, y, dia / 2), [F, B], net)
            self.stamp_bool(self.novia, ("circle", x, y, drill / 2), 0.25 + VIA_DRILL / 2 + MARGIN)

    def blockers(self, net, path):
        """Routed nets whose copper is in the way of a (soft) path."""
        n = self.nid(net)
        o = self.own["s"]
        pts = []
        for i, (l, iy, ix) in enumerate(path):
            via = (i > 0 and path[i - 1][0] != l) or (i + 1 < len(path) and path[i + 1][0] != l)
            v = o[l, iy, ix]
            if via or (v != 0 and v != n):
                pts.append((l, ix * PITCH, iy * PITCH, 0.3 if via else 0.125, via))
        out = []
        for l, x, y, hw, via in pts:
            for t in self.tracks[self.nfix_t:]:
                if t[0] == net or t[0] in out or (t[1] != l and not via):
                    continue
                vx, vy = t[4] - t[2], t[5] - t[3]
                L2 = vx * vx + vy * vy
                k = 0.0 if L2 < 1e-12 else min(1.0, max(0.0, ((x - t[2]) * vx + (y - t[3]) * vy) / L2))
                if math.hypot(x - t[2] - k * vx, y - t[3] - k * vy) < self.clr + hw + t[6] / 2 + MARGIN + 0.01:
                    out.append(t[0])
            for v in self.vias[self.nfix_v:]:
                if v[0] != net and v[0] not in out and math.hypot(x - v[1], y - v[2]) < self.clr + hw + 0.3 + MARGIN + 0.26:
                    out.append(v[0])
        return out

    def route_all(self, jobs):
        """jobs: list of (net, kwargs).  Routes with rip-up and retry."""
        kw = dict(jobs)
        queue = [n for n, _ in jobs]
        fails = {}
        while queue:
            net = queue.pop(0)
            fails[net] = self.route_net(net, **kw[net])
            for m in self.requeue:
                if m not in queue:
                    queue.append(m)
            self.requeue = []
        return sum(fails.values())

    def gnd_stub(self, cells, viamask, power=True):
        """Short B.Cu track from a GND SMD pad to the nearest spot for a via."""
        net = "GND"
        fp = self._free("p", net)
        vt = (fp[0] & fp[1] & ~self.novia & ~self.nearpad & viamask).tobytes()
        dst = {c for c in self.grounded if c >= self.ny * self.nx}
        src = {c for c in cells if c >= self.ny * self.nx}
        if src & dst:
            return True
        path = self.search(net, src, dst, power=False, layers=(B,), via_target=vt, max_exp=200000)
        if path is None:
            self.log.append("GND stub failed at %s" % (self.uncell(next(iter(src))),))
            return False
        l, iy, ix = path[-1]
        end = self.cell(l, iy, ix)
        self.commit(net, path, power=power, max_cls="p")
        if end not in self.grounded:
            self.add_via(net, ix * PITCH, iy * PITCH)
        for l, iy, ix in path:
            self.grounded.add(self.cell(l, iy, ix))
        self.grounded |= src
        return True
