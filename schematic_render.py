"""Themes and painters for the antenna schematics (see schematic.py).

A theme turns a `Layout` into drawing calls on a painter; two painters exist,
one for a Tk canvas (in-app viewer) and one producing SVG (export/print), so
every theme works in both. Themes:

  night -- electronics schematic: flat colour per function, the balun/unun as
           a transformer symbol, component codes (W1, T1, F1, E1)
  day   -- technical drawing: black ink on paper, counterpoise as a brick-red
           chain line, coax as a double line, ISO dimension arrows
  print -- situation sketch for export/printing: sky and lawn, copper wire,
           blue counterpoise, black coax, the shack as a little house
"""

import math

# ------------------------------------------------------------------ painters


class _Painter:
    def __init__(self, theme):
        self.theme = theme

    def font(self, key):
        return self.theme.FONTS[key]

    def line_h(self, key):
        return self.font(key)[2] * 1.35


class TkPainter(_Painter):
    """Draws on a tk.Canvas, scaled by f (fonts too). Dashes are drawn as
    separate segments: Tk on Windows ignores most dash patterns."""

    def __init__(self, canvas, theme, f=1.0):
        super().__init__(theme)
        import tkinter.font as tkfont
        self.c = canvas
        self.f = f
        self._tkfont = tkfont
        self._families = set(tkfont.families(canvas))
        self._cache = {}

    def _family(self, key):
        for fam in self.font(key)[0]:
            if fam in self._families:
                return fam
        return "TkDefaultFont"

    def _tk_font(self, key, scaled=True):
        fams, _css, size, bold, italic = self.font(key)
        px = size * (self.f if scaled else 1.0)
        ck = (key, round(px, 1))
        if ck not in self._cache:
            self._cache[ck] = self._tkfont.Font(root=self.c, family=self._family(key), size=-max(6, int(round(px))),
                                                weight="bold" if bold else "normal",
                                                slant="italic" if italic else "roman")
        return self._cache[ck]

    def measure(self, key, text):
        return self._tk_font(key, scaled=False).measure(text)

    def _xy(self, pts):
        return [v * self.f for p in pts for v in p]

    def line(self, pts, color, width=1.0, dash=None, cap="round"):
        if len(pts) < 2:
            return
        if dash:
            for a, b in _dash_segments(pts, dash):
                self.c.create_line(*self._xy([a, b]), fill=color, width=max(1, width * self.f), capstyle="butt")
            return
        self.c.create_line(*self._xy(pts), fill=color, width=max(1, width * self.f),
                           capstyle={"round": "round", "butt": "butt"}.get(cap, "round"), joinstyle="round")

    def polygon(self, pts, fill, outline=None, width=1.0):
        self.c.create_polygon(*self._xy(pts), fill=fill or "", outline=outline or "", width=width * self.f)

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=1.0, radius=0):
        if radius:
            self.polygon(_rounded(x0, y0, x1, y1, radius), fill, outline, width)
        else:
            self.c.create_rectangle(x0 * self.f, y0 * self.f, x1 * self.f, y1 * self.f, fill=fill or "",
                                    outline=outline or "", width=width * self.f if outline else 0)

    def circle(self, x, y, r, fill, outline=None, width=1.0):
        f = self.f
        self.c.create_oval((x - r) * f, (y - r) * f, (x + r) * f, (y + r) * f, fill=fill or "",
                           outline=outline or "", width=width * f if outline else 0)

    def dot_grid(self, w, h, step, color, size):
        for gx in range(int(step / 2), int(w), step):
            for gy in range(int(step / 2), int(h), step):
                self.rect(gx, gy, gx + size, gy + size, color)

    def text(self, x, y, text, key, color, anchor="nw"):
        self.c.create_text(x * self.f, y * self.f, text=text, font=self._tk_font(key), fill=color, anchor=anchor)


class SvgPainter(_Painter):
    def __init__(self, theme, width, height):
        super().__init__(theme)
        self.w, self.h = width, height
        self.out = []

    def measure(self, key, text):
        _f, css, size, bold, _i = self.font(key)
        per = 0.6 if "mono" in css.lower() or "consolas" in css.lower() else (0.58 if bold else 0.53)
        return len(text) * size * per

    @staticmethod
    def _pts(pts):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    def line(self, pts, color, width=1.0, dash=None, cap="round"):
        if len(pts) < 2:
            return
        d = f' stroke-dasharray="{",".join(str(v) for v in dash)}"' if dash else ""
        self.out.append(f'<polyline points="{self._pts(pts)}" fill="none" stroke="{color}" stroke-width="{width}" '
                        f'stroke-linecap="{cap}" stroke-linejoin="round"{d}/>')

    def polygon(self, pts, fill, outline=None, width=1.0):
        st = f' stroke="{outline}" stroke-width="{width}"' if outline else ""
        self.out.append(f'<polygon points="{self._pts(pts)}" fill="{fill or "none"}"{st}/>')

    def rect(self, x0, y0, x1, y1, fill, outline=None, width=1.0, radius=0):
        st = f' stroke="{outline}" stroke-width="{width}"' if outline else ""
        self.out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
                        f'rx="{radius}" fill="{fill or "none"}"{st}/>')

    def circle(self, x, y, r, fill, outline=None, width=1.0):
        st = f' stroke="{outline}" stroke-width="{width}"' if outline else ""
        self.out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill or "none"}"{st}/>')

    def text(self, x, y, text, key, color, anchor="nw"):
        _f, css, size, bold, italic = self.font(key)
        ta = {"w": "start", "nw": "start", "sw": "start", "e": "end", "ne": "end", "se": "end"}.get(anchor, "middle")
        if anchor in ("nw", "n", "ne"):
            y += size * 0.82
        elif anchor in ("w", "e", "center"):
            y += size * 0.35
        else:
            y -= size * 0.2
        t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ta}" font-family="{css}" font-size="{size}" '
                        f'font-weight="{"bold" if bold else "normal"}" font-style="{"italic" if italic else "normal"}" '
                        f'fill="{color}">{t}</text>')

    def dot_grid(self, w, h, step, color, size):
        pid = f"dots{len(self.out)}"
        self.out.append(f'<defs><pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse" '
                        f'x="{step / 2}" y="{step / 2}"><rect width="{size}" height="{size}" fill="{color}"/></pattern></defs>'
                        f'<rect width="{w:.0f}" height="{h:.0f}" fill="url(#{pid})"/>')

    def svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
                f'viewBox="0 0 {self.w:.0f} {self.h:.0f}">' + "".join(self.out) + "</svg>")


class MeasureOnly(_Painter):
    """Font metrics without a real canvas (SVG export estimate)."""
    measure = SvgPainter.measure


# ------------------------------------------------------------------ geometry helpers

def _rounded(x0, y0, x1, y1, r, n=5):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _dash_segments(pts, pattern):
    """Split a polyline into drawn dash segments following pattern (on, off, ...)."""
    segs = []
    pat = list(pattern)
    idx, left, on = 0, pat[0], True
    for a, b in zip(pts, pts[1:]):
        seg_len = math.dist(a, b)
        if seg_len == 0:
            continue
        pos = 0.0
        while pos < seg_len:
            step = min(left, seg_len - pos)
            if on:
                t0, t1 = pos / seg_len, (pos + step) / seg_len
                segs.append(((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0),
                             (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)))
            pos += step
            left -= step
            if left <= 1e-9:
                idx = (idx + 1) % len(pat)
                left = pat[idx]
                on = not on
    return segs


def _offset_poly(pts, off):
    """Polyline shifted sideways by off px (for ladder line)."""
    out = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy) or 1
        out.append((p[0] - dy / n * off, p[1] + dx / n * off))
    return out


def _arrow(p, tip_dir, size, color, painter):
    ux, uy = tip_dir
    bx, by = p[0] - ux * size, p[1] - uy * size
    nx, ny = -uy * size * 0.38, ux * size * 0.38
    painter.polygon([p, (bx + nx, by + ny), (bx - nx, by - ny)], color)


# ------------------------------------------------------------------ themes

class Theme:
    name = ""
    FONTS = {}
    PAGE = "#ffffff"
    ROLE = {}      # role -> (color, width, dash)
    TEXT = "#000000"
    MUTED = "#555555"
    CAT = {}       # callout category -> colour

    def paint(self, L, p):
        self.background(L, p)
        if L.ground_poly:
            self.ground(L, p)
        for role in ("support", "rope", "boom", "counterpoise", "stub", "parasitic", "radiator"):
            for pts, r in L.wires:
                if r == role:
                    self.wire(pts, r, p)
        for x, y in L.mast_dots:
            self.mast_dot(x, y, p)
        if L.feedline:
            self.feedline(*L.feedline, p)
        for x, y in L.insulators:
            self.insulator(x, y, p)
        if L.shack:
            self.shack(*L.shack, p)
        for x, y in L.earths:
            self.earth(x, y + 11, p)
        for x, y, kind, text in L.boxes:
            self.box(x, y, kind, text, p)
        if L.feed and not any(abs(b[0] - L.feed[0]) < 1 and abs(b[1] - L.feed[1]) < 1 for b in L.boxes):
            self.feed_dot(*L.feed, p)
        for d in L.dims:
            self.dim(d, p)
        for c in L.callouts:
            self.callout(c, p)
        for x, y, text, key, anchor in L.header:
            p.text(x, y, text, key, self.TEXT if key == "title" else self.MUTED, anchor)
        for x, y, kind, text in L.legend:
            self.swatch(x, y + 9, kind, p)
            p.text(x + 40, y + 9, text, "legend", self.TEXT, "w")

    # defaults, overridden per theme
    def background(self, L, p):
        p.rect(0, 0, L.width, L.height, self.PAGE)

    def ground(self, L, p):
        p.polygon(L.ground_poly, None, self.ROLE["support"][0], 1)

    def wire(self, pts, role, p):
        color, width, dash = self.ROLE[role]
        p.line(pts, color, width, dash)

    def mast_dot(self, x, y, p):
        color = self.ROLE["support"][0]
        p.circle(x, y, 5, color)

    def feedline(self, pts, kind, p):
        color = self.ROLE["coax"][0]
        if kind == "ladder":
            for off in (-3, 3):
                p.line(_offset_poly(pts, off), color, 1.3)
            for a, b in _dash_segments(pts, (2, 9)):
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                dx, dy = b[0] - a[0], b[1] - a[1]
                n = math.hypot(dx, dy) or 1
                p.line([(m[0] - dy / n * 3, m[1] + dx / n * 3), (m[0] + dy / n * 3, m[1] - dx / n * 3)], color, 1)
            return
        p.line(pts, color, 6.5)
        p.line(pts, self.PAGE_UNDER, 2.6)

    PAGE_UNDER = "#ffffff"

    def insulator(self, x, y, p):
        p.circle(x, y, 3.5, self.PAGE_UNDER, self.MUTED, 1.2)

    def feed_dot(self, x, y, p):
        p.circle(x, y, 5, self.PAGE_UNDER, self.ROLE["radiator"][0], 2)

    def earth(self, x, y, p):
        c = self.CAT["earth"]
        p.line([(x, y), (x, y + 8)], c, 1.8)
        for half, dy in ((12, 8), (8, 13), (4, 18)):
            p.line([(x - half, y + dy), (x + half, y + dy)], c, 1.8, cap="butt")

    def shack(self, x, y, p):
        c = self.CAT["feedline"]
        p.rect(x - 17, y - 10, x + 17, y + 10, self.PAGE_UNDER, c, 1.5, radius=3)
        p.text(x, y, "TX", "box", c, "center")

    def box(self, x, y, kind, text, p):
        p.rect(x - 23, y - 15, x + 23, y + 15, self.PAGE_UNDER, self.CAT["box"], 1.6, radius=3)
        p.text(x, y, text, "box", self.CAT["box"], "center")

    def dim(self, d, p):
        color = self.DIM
        (q1, q2) = d["q1"], d["q2"]
        for a, b in ((d["p1"], q1), (d["p2"], q2)):
            p.line([a, b], self.DIM_EXT, 0.8, (3, 3))
        ln = math.dist(q1, q2)
        u = ((q2[0] - q1[0]) / ln, (q2[1] - q1[1]) / ln)
        p.line([q1, q2], color, 1)
        _arrow(q2, u, 8, color, p)
        _arrow(q1, (-u[0], -u[1]), 8, color, p)
        r = d["rect"]
        p.rect(r[0], r[1], r[2], r[3], self.DIM_BG, None, radius=3)
        p.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, d["label"], "dim", self.DIM_TEXT, "center")

    def leader(self, c, p):
        col = self.CAT[c["cat"]]
        p.line(c["leader"], col, 1)
        ax, ay = c["anchor"]
        p.circle(ax, ay, 3, col)

    def callout(self, c, p):
        self.leader(c, p)
        x0, y0, x1, y1 = c["rect"]
        p.rect(x0, y0, x1, y1, self.CARD_BG, self.CARD_LINE, 1, radius=6)
        self.card_text(c, p)

    def card_text(self, c, p, x_indent=10):
        x0, y0, _x1, _y1 = c["rect"]
        y = y0 + 10
        for ln in c["title"]:
            p.text(x0 + x_indent, y, ln, "card_title", self.TEXT, "nw")
            y += p.line_h("card_title")
        for ln in c["detail"]:
            p.text(x0 + x_indent, y, ln, "card_detail", self.MUTED, "nw")
            y += p.line_h("card_detail")

    def swatch(self, x, y, kind, p):
        if kind in self.ROLE:
            color, width, dash = self.ROLE[kind]
            p.line([(x + 2, y), (x + 32, y)], color, width, dash)
        elif kind == "coax":
            self.feedline([(x + 2, y), (x + 32, y)], "coax", p)
        elif kind == "ladder":
            self.feedline([(x + 2, y), (x + 32, y)], "ladder", p)
        elif kind == "box":
            p.rect(x + 7, y - 8, x + 27, y + 8, self.PAGE_UNDER, self.CAT["box"], 1.5, radius=2)
        elif kind == "earth":
            self.earth(x + 17, y - 9, p)


class NightTheme(Theme):
    name = "night"
    MONO = ["Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"]
    CSS_MONO = "Consolas, Menlo, 'DejaVu Sans Mono', monospace"
    FONTS = {
        "title": (MONO, CSS_MONO, 17, True, False),
        "sub": (MONO, CSS_MONO, 12, False, False),
        "card_title": (MONO, CSS_MONO, 13, True, False),
        "card_detail": (MONO, CSS_MONO, 11.5, False, False),
        "dim": (MONO, CSS_MONO, 12, False, False),
        "legend": (MONO, CSS_MONO, 12, False, False),
        "box": (MONO, CSS_MONO, 11, True, False),
    }
    PAGE = "#16191f"
    PAGE_UNDER = "#16191f"
    TEXT = "#e5e7eb"
    MUTED = "#8b93a3"
    ROLE = {
        "radiator": ("#ff9f40", 3.2, None),
        "parasitic": ("#e8d44d", 2.6, None),
        "stub": ("#e8d44d", 2.6, None),
        "counterpoise": ("#3ecf8e", 3.0, None),
        "support": ("#4b5263", 2.2, (3, 4)),
        "rope": ("#4b5263", 1.4, (2, 4)),
        "boom": ("#6b7384", 3.0, None),
        "coax": ("#6ea8fe", 6.5, None),
    }
    CAT = {"radiator": "#ff9f40", "parasitic": "#e8d44d", "stub": "#e8d44d", "counterpoise": "#3ecf8e",
           "box": "#c792ea", "feedline": "#6ea8fe", "earth": "#e5e7eb", "support": "#8b93a3"}
    DIM, DIM_EXT, DIM_BG, DIM_TEXT = "#5c6474", "#3a404c", "#16191f", "#ffb877"
    CARD_BG, CARD_LINE = "#1b1f27", "#2a2f39"

    def background(self, L, p):
        p.rect(0, 0, L.width, L.height, self.PAGE)
        p.dot_grid(L.width, L.height, 20, "#262b34", 1.4)

    def ground(self, L, p):
        p.polygon(L.ground_poly, "#1a1e25", None)
        p.line(L.ground_poly + [L.ground_poly[0]], "#3a404c", 1.2, (6, 5))

    def box(self, x, y, kind, text, p):
        c = self.CAT["box"]
        p.rect(x - 23, y - 15, x + 23, y + 15, "#1f1a28", c, 1.6, radius=3)
        if kind in ("transformer", "choke"):
            top, bot = y - 10, y + 10
            for side in (-1, 1):
                pts = []
                for i in range(31):
                    t = i / 30
                    yy = top + (bot - top) * t
                    xx = x + side * (5 + 3.6 * abs(math.sin(math.pi * 3 * t)))
                    pts.append((xx, yy))
                p.line(pts, c, 1.4)
            if kind == "transformer":
                p.line([(x - 1.2, top), (x - 1.2, bot)], c, 1)
                p.line([(x + 1.2, top), (x + 1.2, bot)], c, 1)
            else:
                p.circle(x, y, 2.2, c)
        elif kind == "coil":
            pts = [(x - 14 + 28 * i / 40, y - 5 * abs(math.sin(math.pi * 4 * i / 40))) for i in range(41)]
            p.line(pts, c, 1.6)
        else:  # tuner: a variable-component arrow
            p.line([(x - 12, y + 8), (x + 12, y - 8)], c, 1.4)
            _arrow((x + 12, y - 8), (0.83, -0.55), 6, c, p)
            p.line([(x - 14, y), (x + 14, y)], c, 1.2)

    def callout(self, c, p):
        self.leader(c, p)
        x0, y0, x1, y1 = c["rect"]
        col = self.CAT[c["cat"]]
        p.rect(x0, y0, x1, y1, self.CARD_BG, col, 1, radius=2)
        p.text(x0 + 10, y0 + 10, c["code"], "card_title", col, "nw")
        x = x0 + 10 + p.measure("card_title", c["code"] + " ")
        y = y0 + 10
        for i, ln in enumerate(c["title"]):
            p.text(x if i == 0 else x0 + 10, y, ln, "card_title", self.TEXT, "nw")
            y += p.line_h("card_title")
        for ln in c["detail"]:
            p.text(x0 + 10, y, ln, "card_detail", self.MUTED, "nw")
            y += p.line_h("card_detail")

    def shack(self, x, y, p):
        c = self.CAT["feedline"]
        p.circle(x, y, 11, "#16191f", c, 1.6)
        p.text(x, y, "TX", "box", c, "center")

    def swatch(self, x, y, kind, p):
        if kind == "box":
            p.rect(x + 7, y - 8, x + 27, y + 8, "#1f1a28", self.CAT["box"], 1.5, radius=2)
        else:
            super().swatch(x, y, kind, p)


class DayTheme(Theme):
    name = "day"
    SANS = ["Bahnschrift SemiCondensed", "Bahnschrift", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial"]
    CSS_SANS = "'Bahnschrift SemiCondensed', Bahnschrift, 'IBM Plex Sans Condensed', 'Segoe UI', Arial, sans-serif"
    MONO = ["Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"]
    CSS_MONO = "Consolas, 'IBM Plex Mono', Menlo, monospace"
    FONTS = {
        "title": (SANS, CSS_SANS, 19, True, False),
        "sub": (MONO, CSS_MONO, 11.5, False, False),
        "card_title": (SANS, CSS_SANS, 14.5, True, False),
        "card_detail": (MONO, CSS_MONO, 11, False, False),
        "dim": (MONO, CSS_MONO, 12, False, False),
        "legend": (SANS, CSS_SANS, 13, False, False),
        "box": (MONO, CSS_MONO, 11.5, True, False),
    }
    PAGE = "#f8f6f0"
    PAGE_UNDER = "#f8f6f0"
    TEXT = "#161616"
    MUTED = "#4a463e"
    INK = "#161616"
    ROLE = {
        "radiator": ("#161616", 3.4, None),
        "parasitic": ("#161616", 2.2, None),
        "stub": ("#161616", 2.2, None),
        "counterpoise": ("#b3401f", 3.0, (12, 4, 2, 4)),
        "support": ("#9a958a", 2.4, None),
        "rope": ("#9a958a", 1.0, (3, 3)),
        "boom": ("#6f6b62", 3.0, None),
        "coax": ("#161616", 6.0, None),
    }
    CAT = {"radiator": "#161616", "parasitic": "#161616", "stub": "#161616", "counterpoise": "#b3401f",
           "box": "#161616", "feedline": "#161616", "earth": "#161616", "support": "#6f6b62"}
    DIM, DIM_EXT, DIM_BG, DIM_TEXT = "#161616", "#8f8a7e", "#f8f6f0", "#161616"

    def background(self, L, p):
        p.rect(0, 0, L.width, L.height, self.PAGE)
        for gx in range(0, int(L.width) + 1, 20):
            p.line([(gx, 0), (gx, L.height)], "#e9e5da", 0.8)
        for gy in range(0, int(L.height) + 1, 20):
            p.line([(0, gy), (L.width, gy)], "#e9e5da", 0.8)
        p.rect(8, 8, L.width - 8, L.height - 8, None, self.INK, 1.2)

    def ground(self, L, p):
        p.polygon(L.ground_poly, "#efebe1", None)
        g = L.ground_poly
        p.line(g + [g[0]], self.INK, 1.1)

    def feedline(self, pts, kind, p):
        if kind == "ladder":
            return super().feedline(pts, kind, p)
        p.line(pts, self.INK, 6.0, cap="butt")
        p.line(pts, self.PAGE, 3.2, cap="butt")

    def mast_dot(self, x, y, p):
        p.circle(x, y, 5, self.PAGE, self.ROLE["support"][0], 2)

    def feed_dot(self, x, y, p):
        p.circle(x, y, 4, self.INK)

    def box(self, x, y, kind, text, p):
        p.rect(x - 23, y - 15, x + 23, y + 15, "#ffffff", self.INK, 1.6)
        p.line([(x - 23, y - 15), (x - 16, y - 8)], self.INK, 0.8)
        p.text(x, y, text, "box", self.INK, "center")

    def leader(self, c, p):
        p.line(c["leader"], self.INK, 0.8)
        ax, ay = c["anchor"]
        p.circle(ax, ay, 2.4, self.INK)

    def callout(self, c, p):
        x0, y0, x1, y1 = c["rect"]
        th = len(c["title"]) * p.line_h("card_title")
        y_line = y0 + 8 + th + 2
        lead = list(c["leader"])
        lead[-1] = (lead[-1][0], y_line)
        lead[-2] = (lead[-2][0], y_line)
        self.leader(dict(c, leader=lead), p)
        y = y0 + 8
        for ln in c["title"]:
            p.text(x0 + 4, y, ln, "card_title", self.INK, "nw")
            y += p.line_h("card_title")
        p.line([(x0, y_line), (x1, y_line)], self.INK, 0.8)
        y = y_line + 5
        for ln in c["detail"]:
            p.text(x0 + 4, y, ln, "card_detail", self.MUTED, "nw")
            y += p.line_h("card_detail")

    def dim(self, d, p):
        (q1, q2) = d["q1"], d["q2"]
        for a, b in ((d["p1"], q1), (d["p2"], q2)):
            ln = math.dist(a, b) or 1
            ext = ((b[0] - a[0]) / ln * 5, (b[1] - a[1]) / ln * 5)
            p.line([(a[0] + ext[0], a[1] + ext[1]), (b[0] + ext[0], b[1] + ext[1])], self.INK, 0.6)
        ln = math.dist(q1, q2)
        u = ((q2[0] - q1[0]) / ln, (q2[1] - q1[1]) / ln)
        p.line([q1, q2], self.INK, 0.8)
        _arrow(q2, u, 9, self.INK, p)
        _arrow(q1, (-u[0], -u[1]), 9, self.INK, p)
        r = d["rect"]
        p.rect(r[0], r[1], r[2], r[3], self.PAGE, None)
        p.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, d["label"], "dim", self.INK, "center")

    def shack(self, x, y, p):
        p.rect(x - 17, y - 10, x + 17, y + 10, "#ffffff", self.INK, 1.4)
        p.text(x, y, "TX", "box", self.INK, "center")

    def swatch(self, x, y, kind, p):
        if kind == "box":
            p.rect(x + 7, y - 8, x + 27, y + 8, "#ffffff", self.INK, 1.4)
        else:
            super().swatch(x, y, kind, p)


class PrintTheme(Theme):
    name = "print"
    SANS = ["Segoe UI", "Source Sans 3", "Helvetica Neue", "Arial"]
    CSS = "'Segoe UI', 'Source Sans 3', 'Helvetica Neue', Arial, sans-serif"
    FONTS = {
        "title": (SANS, CSS, 20, True, False),
        "sub": (SANS, CSS, 12.5, False, False),
        "card_title": (SANS, CSS, 14.5, True, False),
        "card_detail": (SANS, CSS, 12.5, False, False),
        "dim": (SANS, CSS, 13, True, False),
        "legend": (SANS, CSS, 13, False, False),
        "box": (SANS, CSS, 12, True, False),
    }
    PAGE = "#ffffff"
    PAGE_UNDER = "#ffffff"
    TEXT = "#1f2a30"
    MUTED = "#4d5c66"
    ROLE = {
        "radiator": ("#c0661c", 3.4, None),
        "parasitic": ("#d99a5b", 2.8, None),
        "stub": ("#d99a5b", 2.8, None),
        "counterpoise": ("#2f6fb5", 3.0, None),
        "support": ("#9aa5ad", 5.0, None),
        "rope": ("#8d7a60", 1.4, None),
        "boom": ("#8a959d", 4.5, None),
        "coax": ("#1d1d1d", 4.6, None),
    }
    CAT = {"radiator": "#c0661c", "parasitic": "#d99a5b", "stub": "#d99a5b", "counterpoise": "#2f6fb5",
           "box": "#58656e", "feedline": "#1d1d1d", "earth": "#5a3e22", "support": "#8a959d"}
    DIM, DIM_EXT, DIM_BG, DIM_TEXT = "#7a8a93", "#b3bec5", "#ffffff", "#1f2a30"

    def background(self, L, p):
        p.rect(0, 0, L.width, L.height, self.PAGE)
        g = L.geo
        top_view = L.ground_poly is None
        p.rect(g[0], g[1], g[2], g[3], "#e3ecd4" if top_view else "#e6eff5", None, radius=14)

    def ground(self, L, p):
        p.polygon(L.ground_poly, "#cfdcb4", "#a8bd86", 1.5)

    def feedline(self, pts, kind, p):
        if kind == "ladder":
            return super().feedline(pts, kind, p)
        p.line(pts, self.ROLE["coax"][0], 4.6)

    def insulator(self, x, y, p):
        p.polygon([(x - 6 * math.cos(a), y - 3.5 * math.sin(a)) for a in [i * math.pi / 8 for i in range(16)]],
                  "#ffffff", "#7d8a93", 1)

    def box(self, x, y, kind, text, p):
        p.rect(x - 23, y - 15, x + 23, y + 15, "#58656e", None, radius=5)
        p.text(x, y, text, "box", "#ffffff", "center")

    def earth(self, x, y, p):
        c = self.CAT["earth"]
        p.line([(x, y - 2), (x, y + 18)], c, 4)
        p.polygon([(x - 5, y + 16), (x, y + 25), (x + 5, y + 16)], c)

    def shack(self, x, y, p):
        p.rect(x - 22, y - 26, x + 22, y + 2, "#f4efe6", "#9c8f7c", 1)
        p.polygon([(x - 27, y - 24), (x, y - 44), (x + 27, y - 24)], "#b0664a")
        p.rect(x - 5, y - 14, x + 5, y + 2, "#9c8f7c")

    def dim(self, d, p):
        (q1, q2) = d["q1"], d["q2"]
        for a, b in ((d["p1"], q1), (d["p2"], q2)):
            p.line([a, b], self.DIM_EXT, 0.8)
        p.line([q1, q2], self.DIM, 1)
        ln = math.dist(q1, q2)
        nx, ny = -(q2[1] - q1[1]) / ln * 5, (q2[0] - q1[0]) / ln * 5
        for q in (q1, q2):
            p.line([(q[0] - nx, q[1] - ny), (q[0] + nx, q[1] + ny)], self.DIM, 1)
        r = d["rect"]
        p.rect(r[0] - 3, r[1] - 1, r[2] + 3, r[3] + 1, "#ffffff", self.ROLE["radiator"][0], 1, radius=10)
        p.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, d["label"], "dim", self.DIM_TEXT, "center")

    def leader(self, c, p):
        p.line(c["leader"], "#7a8a93", 1.2)
        ax, ay = c["anchor"]
        p.circle(ax, ay, 3, "#ffffff", "#7a8a93", 1.2)

    def callout(self, c, p):
        self.leader(c, p)
        x0, y0, x1, y1 = c["rect"]
        p.rect(x0, y0, x1, y1, "#ffffff", "#c3ced5", 1, radius=10)
        p.circle(x0 + 14, y0 + 10 + p.line_h("card_title") / 2, 5, self.CAT[c["cat"]])
        y = y0 + 10
        for i, ln in enumerate(c["title"]):
            p.text(x0 + (26 if i == 0 else 12), y, ln, "card_title", self.TEXT, "nw")
            y += p.line_h("card_title")
        for ln in c["detail"]:
            p.text(x0 + 12, y, ln, "card_detail", self.MUTED, "nw")
            y += p.line_h("card_detail")

    def swatch(self, x, y, kind, p):
        if kind == "box":
            p.rect(x + 7, y - 8, x + 27, y + 8, "#58656e", None, radius=3)
        elif kind == "earth":
            self.earth(x + 17, y - 10, p)
        else:
            super().swatch(x, y, kind, p)


THEMES = {"night": NightTheme(), "day": DayTheme(), "print": PrintTheme()}
