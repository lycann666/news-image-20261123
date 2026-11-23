#!/usr/bin/env python3
"""THE WORLD TODAY - Monday, 23 November 2026.

A front-page summary of the day's world news, drawn with the Python
standard library only (zlib + struct PNG writer, hand-built 5x7 bitmap
font). No network, no randomness, no clock: two runs write identical
bytes to /output/entry.png (falls back to ./out/entry.png locally).

Stories (all reported on 22-23 November 2026):
  Lead   COP31 climate talks collapse in Antalya: final text drops all
         mention of fossil fuels; EU and UK reject the pact.
  Second Iran strikes US bases in Bahrain; two tankers hit in the
         Strait of Hormuz; 25 tankers attacked in seven days.
  Strip  Ukraine: drone hits Kyiv-region flats, 14 missing.
         Gaza: 9 killed in 48 hours as the truce frays.
         Mercury: BepiColombo enters orbit after eight years.
         Indonesia: factory fire, 24 dead, dozens missing.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (158, 30, 30)
BLUE = (31, 58, 110)
SEA = (24, 74, 96)
SEA_DARK = (16, 52, 70)
SKY = (214, 226, 232)
GREEN = (74, 128, 66)
SAND = (216, 198, 162)
GREY = (112, 107, 96)
ORANGE = (204, 92, 18)
YELLOW = (232, 178, 44)
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)

# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 bits ("#" on, "." off). Authored from scratch.
_G = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".#...", "#...."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".#...", "#...."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
}
_BLANK = (".....",) * 7


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, scale, max_w):
    """Greedy word wrap; returns list of lines fitting max_w."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[3 * i] = bg[0]
            self.px[3 * i + 1] = bg[1]
            self.px[3 * i + 2] = bg[2]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def bezier(self, p0, p1, p2, c, t=2, steps=40):
        prev = None
        for i in range(steps + 1):
            u = i / steps
            x = int((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0])
            y = int((1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])
            if prev is not None:
                self.line(prev[0], prev[1], x, y, c, t)
            prev = (x, y)

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5) if r * r - dy * dy >= 0 else 0
            if fill:
                self.rect(cx - dx, yy, 2 * dx + 1, 1, c)
            else:
                self.set(cx - dx, yy, c)
                self.set(cx + dx, yy, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / ry
            dx = int(rx * (max(0.0, 1 - dy * dy)) ** 0.5)
            self.rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def star(self, cx, cy, r_out, r_in, c, points=8):
        import math
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = 3.141592653589793 * i / points - 3.141592653589793 / 2
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        self.poly(pts, c)

    # ------------------------------------------------------------- text
    def glyph(self, x, y, ch, scale, c):
        rows = _G.get(ch.upper(), _BLANK)
        for r, row in enumerate(rows):
            for col, bit in enumerate(row):
                if bit == "1":
                    self.rect(x + col * scale, y + r * scale, scale, scale, c)

    def text(self, x, y, s, scale, c, align="left"):
        w = text_width(s, scale)
        if align == "center":
            x = x - w // 2
        elif align == "right":
            x = x - w
        for i, ch in enumerate(s):
            self.glyph(x + i * 6 * scale, y, ch, scale, c)
        return w

    def para(self, x, y, lines, scale, c, leading=None):
        lh = leading if leading is not None else 9 * scale
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, scale, c)
        return y + len(lines) * lh


# ------------------------------------------------------------------ drawing
def draw_masthead(cv):
    cv.text(512, 24, "THE WORLD TODAY", 10, INK, align="center")
    cv.hline(30, 102, 964, INK, 2)
    cv.text(512, 114, "MONDAY, 23 NOVEMBER 2026", 3, INK, align="center")
    cv.hline(30, 140, 964, INK, 4)
    cv.hline(30, 148, 964, INK, 1)


def draw_globe(cv, cx, cy, r):
    # Ocean.
    cv.circle(cx, cy, r, BLUE)
    # Landmasses (kept well inside the disc).
    cv.ellipse(cx - 38, cy - 42, 42, 26, GREEN)
    cv.ellipse(cx + 34, cy - 8, 34, 40, GREEN)
    cv.ellipse(cx - 8, cy + 52, 46, 22, GREEN)
    cv.ellipse(cx + 62, cy + 46, 18, 14, GREEN)
    # Cloud wisps.
    cv.ellipse(cx - 52, cy - 66, 30, 8, WHITE)
    cv.ellipse(cx + 30, cy + 18, 26, 7, WHITE)
    # Outline.
    for rr in (r, r - 1):
        for yy in range(cy - rr, cy + rr + 1):
            dy = yy - cy
            dx = int((rr * rr - dy * dy) ** 0.5)
            cv.set(cx - dx, yy, INK)
            cv.set(cx + dx, yy, INK)
    # The crack: a jagged black split across the globe.
    crack = [(cx - 88, cy - 78), (cx - 52, cy - 40), (cx - 66, cy - 6),
             (cx - 28, cy + 22), (cx - 44, cy + 58), (cx - 6, cy + 92)]
    for a, b in zip(crack, crack[1:]):
        cv.line(a[0], a[1], b[0], b[1], BLACK, 5)
    crack2 = [(cx + 30, cy - 88), (cx + 52, cy - 52), (cx + 40, cy - 14),
              (cx + 66, cy + 18), (cx + 52, cy + 56)]
    for a, b in zip(crack2, crack2[1:]):
        cv.line(a[0], a[1], b[0], b[1], BLACK, 4)
    # Smoke above the globe.
    cv.ellipse(cx - 70, cy - r - 6, 26, 12, GREY)
    cv.ellipse(cx + 48, cy - r - 14, 20, 10, GREY)


def draw_lead(cv):
    x0, y0, x1, y1 = 30, 162, 994, 592
    cv.rect(x0, y0, x1 - x0, 3, INK)
    # Kicker band.
    cv.rect(x0, y0 + 3, x1 - x0, 30, RED)
    cv.text(x0 + 16, y0 + 10, "CLIMATE  -  ANTALYA, TURKEY", 2, WHITE)
    cv.text(x1 - 16, y0 + 10, "LEAD STORY", 2, WHITE, align="right")
    # Headline.
    cv.text(x0 + 26, y0 + 52, "CLIMATE TALKS", 6, INK)
    cv.text(x0 + 26, y0 + 104, "COLLAPSE", 6, RED)
    # Globe visual, lower left.
    draw_globe(cv, 215, 448, 100)
    # "NO DEAL" stamp overlapping the globe.
    cv.rect(268, 496, 158, 46, RED)
    cv.rect(272, 500, 150, 38, RED)
    cv.hline(272, 500, 150, WHITE, 2)
    cv.hline(272, 536, 150, WHITE, 2)
    cv.text(347, 510, "NO DEAL", 3, WHITE, align="center")
    # Deck text, right side.
    deck = wrap("COP31 ENDS WITH NO DEAL AFTER TWO WEEKS OF TALKS IN "
                "ANTALYA. THE FINAL TEXT DROPS ALL MENTION OF FOSSIL "
                "FUELS. THE EU AND UK REJECT THE PACT; THE UN CHIEF "
                "CALLS IT 'DEEPLY DISAPPOINTING'. THE LONGEST CLIMATE "
                "SUMMIT ON RECORD.", 2, 560)
    cv.para(430, y0 + 170, deck, 2, INK, leading=20)
    # Bottom line of the panel.
    cv.hline(x0 + 26, 566, 912, INK, 1)
    cv.text(x0 + 26, 574, "FIRST CLIMATE SUMMIT TO END WITHOUT A DEAL SINCE COPENHAGEN 2009.",
            2, RED)


def draw_tanker(cv, x0, y0, x1, y1):
    # Sky and sea.
    cv.rect(x0, y0, x1 - x0, y1 - y0, SKY)
    cv.rect(x0, y0 + 62, x1 - x0, y1 - y0 - 62, SEA)
    cv.hline(x0, y0 + 62, x1 - x0, WHITE, 2)
    # Missile arcs with dotted trails.
    cv.bezier((x0 + 14, y0 + 18), (x0 + 150, y0 - 6), (x0 + 300, y0 + 52),
              ORANGE, 3)
    cv.bezier((x0 + 40, y0 + 30), (x0 + 190, y0 + 6), (x0 + 330, y0 + 58),
              YELLOW, 2)
    # Tanker silhouette.
    hull = [(x0 + 60, y0 + 96), (x0 + 330, y0 + 96), (x0 + 310, y0 + 122),
            (x0 + 80, y0 + 122)]
    cv.poly(hull, BLACK)
    cv.rect(x0 + 96, y0 + 66, 150, 30, BLACK)
    cv.rect(x0 + 250, y0 + 52, 34, 44, BLACK)
    cv.rect(x0 + 258, y0 + 40, 18, 12, RED)
    # Containers.
    for i, col in enumerate((RED, YELLOW, WHITE, BLUE)):
        cv.rect(x0 + 104 + i * 34, y0 + 74, 30, 22, col)
    # Explosion at the bow.
    cv.star(x0 + 342, y0 + 66, 30, 12, ORANGE)
    cv.star(x0 + 342, y0 + 66, 18, 7, YELLOW)
    # Wake.
    cv.hline(x0 + 70, y0 + 128, 260, WHITE, 2)


def draw_gulf(cv):
    x0, y0, x1, y1 = 30, 606, 994, 852
    cv.rect(x0, y0, x1 - x0, 3, INK)
    cv.rect(x0, y0 + 3, x1 - x0, 30, BLUE)
    cv.text(x0 + 16, y0 + 10, "GULF  -  STRAIT OF HORMUZ", 2, WHITE)
    cv.text(x1 - 16, y0 + 10, "WAR AT SEA", 2, WHITE, align="right")
    cv.text(x0 + 26, y0 + 46, "GULF WAR WIDENS", 5, INK)
    draw_tanker(cv, x0 + 26, y0 + 92, x0 + 400, y1 - 14)
    deck = wrap("IRAN STRIKES US BASES IN BAHRAIN. TWO TANKERS HIT IN "
                "THE STRAIT OF HORMUZ. 25 TANKERS ATTACKED IN SEVEN "
                "DAYS. A HOUTHI DRONE AIMED AT RIYADH IS INTERCEPTED.",
                2, 520)
    cv.para(462, y0 + 96, deck, 2, INK, leading=20)
    cv.text(462, y1 - 28, "OIL FLOW THROUGH THE STRAIT IS FALLING FAST.", 2, BLUE)


def draw_strip(cv):
    y0, y1 = 866, 988
    cells = [
        ("UKRAINE", RED, "14 MISSING AS DRONE HITS KYIV FLATS", "building"),
        ("GAZA", INK, "9 KILLED IN 48 HOURS AS TRUCE FRAYS", "blast"),
        ("MERCURY", BLUE, "BEPICOLOMBO ORBITS MERCURY AT LAST", "planet"),
        ("INDONESIA", ORANGE, "FACTORY FIRE: 24 DEAD, DOZENS MISSING", "flame"),
    ]
    cw, gap = 236, 8
    for i, (kick, col, head, icon) in enumerate(cells):
        x0 = 30 + i * (cw + gap)
        cv.rect(x0, y0, cw, 3, INK)
        cv.rect(x0, y0 + 3, cw, 24, col)
        cv.text(x0 + 10, y0 + 9, kick, 2, WHITE)
        draw_icon(cv, x0 + 12, y0 + 40, icon)
        lines = wrap(head, 2, cw - 66)
        cv.para(x0 + 62, y0 + 42, lines[:3], 2, INK, leading=19)
        cv.hline(x0, y1 - 2, cw, INK, 1)


def draw_icon(cv, x, y, kind):
    if kind == "building":
        cv.rect(x, y, 34, 44, INK)
        cv.rect(x + 6, y + 8, 6, 6, PAPER)
        cv.rect(x + 14, y + 8, 6, 6, PAPER)
        cv.rect(x + 6, y + 20, 6, 6, PAPER)
        cv.rect(x + 14, y + 20, 6, 6, PAPER)
        cv.line(x, y, x + 34, y + 44, RED, 4)
        cv.line(x + 34, y, x, y + 44, RED, 4)
    elif kind == "blast":
        cv.star(x + 17, y + 22, 22, 9, ORANGE)
        cv.star(x + 17, y + 22, 12, 5, YELLOW)
    elif kind == "planet":
        cv.circle(x + 17, y + 22, 16, ORANGE)
        cv.ellipse(x + 17, y + 22, 24, 7, INK)
        cv.circle(x + 17, y + 22, 16, ORANGE)
        cv.rect(x + 4, y + 20, 26, 3, INK)
    elif kind == "flame":
        cv.poly([(x + 17, y), (x + 34, y + 26), (x + 26, y + 44),
                 (x + 8, y + 44), (x, y + 26)], ORANGE)
        cv.poly([(x + 17, y + 18), (x + 26, y + 32), (x + 22, y + 44),
                 (x + 12, y + 44), (x + 8, y + 32)], YELLOW)


def draw_footer(cv):
    cv.hline(30, 996, 964, INK, 1)
    cv.text(512, 1004, "THE WORLD TODAY - MONDAY 23 NOVEMBER 2026 - "
            "NEWS AS REPORTED ON THE DAY", 1, GREY, align="center")


# --------------------------------------------------------------------- PNG
def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_lead(cv)
    draw_gulf(cv)
    draw_strip(cv)
    draw_footer(cv)
    out = "/output/entry.png"
    try:
        os.makedirs("/output", exist_ok=True)
        n = write_png(cv, out)
    except OSError:
        os.makedirs("out", exist_ok=True)
        out = os.path.join("out", "entry.png")
        n = write_png(cv, out)
    print("wrote %s (%d bytes, %dx%d)" % (out, n, W, H))


if __name__ == "__main__":
    main()
