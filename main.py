#!/usr/bin/env python3
"""The World in One Day -- Friday 20 November 2026.

A one-page broadsheet that sums up one day's world news, drawn entirely by
this program with Pillow. It writes entry.png to /output (or to the folder
named by the MAKEFUN_OUTPUT_DIR environment variable). The drawing uses no
randomness, no clock and no network, so two runs write identical bytes.

Layout, top to bottom: strap line, dated masthead, deck, a six-number stat
strip, a region tally bar, three illustrated hero stories, ten illustrated
cards, a numbered-pin world map beside 23 sourced one-line briefs, a DATE
CHECK box, and a footer. Every story happened, or was first reported, on
Friday 20 November 2026, and names its source beside it.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 12

PAPER = (248, 242, 228)
PAPER_DARK = (238, 229, 205)
INK = (27, 25, 21)
INK_SOFT = (74, 68, 58)
RED = (176, 32, 38)
RED_DARK = (138, 24, 30)
NAVY = (23, 41, 74)
NAVY_LIGHT = (52, 78, 122)
BLUE = (58, 96, 148)
GREEN = (66, 110, 72)
GOLD = (176, 132, 44)
TAN = (226, 214, 182)
HAIR = (120, 110, 92)
WHITE = (255, 255, 255)

SERIF_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
]
SERIF_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
]
SANS_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]
SANS_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]
SERIF_ITALIC_CANDIDATES = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf",
]

_font_cache = {}


def font(candidates, size):
    """Load the first available font from a candidate list, cached by size."""
    key = (candidates[0], size)
    if key in _font_cache:
        return _font_cache[key]
    loaded = None
    for path in candidates:
        if os.path.exists(path):
            try:
                loaded = ImageFont.truetype(path, size)
                break
            except OSError:
                loaded = None
    if loaded is None:
        loaded = ImageFont.load_default()
    _font_cache[key] = loaded
    return loaded


def serif(size):
    return font(SERIF_CANDIDATES, size)


def serif_bold(size):
    return font(SERIF_BOLD_CANDIDATES, size)


def serif_italic(size):
    return font(SERIF_ITALIC_CANDIDATES, size)


def sans(size):
    return font(SANS_CANDIDATES, size)


def sans_bold(size):
    return font(SANS_BOLD_CANDIDATES, size)


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def fit_font(draw, s, candidates, start_size, max_w, min_size=10):
    """Shrink a font until the string fits max_w; return (font, size)."""
    size = start_size
    while size > min_size:
        fnt = font(candidates, size)
        if text_w(draw, s, fnt) <= max_w:
            return fnt, size
        size -= 2
    return font(candidates, min_size), min_size


def wrap(draw, s, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines = []
    current = ""
    for word in s.split():
        trial = word if not current else current + " " + word
        if text_w(draw, trial, fnt) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, s, fnt, fill, max_w, line_h, max_lines=None):
    """Draw wrapped text at xy; returns the y just past the last line."""
    x, y = xy
    lines = wrap(draw, s, fnt, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def centered(draw, cx, y, s, fnt, fill):
    draw.text((cx - text_w(draw, s, fnt) / 2, y), s, font=fnt, fill=fill)


def chip(draw, x, y, s, fnt, fill_bg, fill_fg, pad_x=5, pad_y=2):
    """A small filled label chip; returns the x just past it."""
    w = text_w(draw, s, fnt) + pad_x * 2
    h = fnt.size + pad_y * 2 + 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=fill_bg)
    draw.text((x + pad_x, y + pad_y), s, font=fnt, fill=fill_fg)
    return x + w


def chip_right(draw, right, y, s, fnt, outline, fill_fg, pad_x=5, pad_y=2):
    """An outlined chip whose right edge sits at `right`; returns its left x."""
    w = text_w(draw, s, fnt) + pad_x * 2
    h = fnt.size + pad_y * 2 + 2
    draw.rounded_rectangle([right - w, y, right, y + h], radius=3,
                           outline=outline, width=1)
    draw.text((right - w + pad_x, y + pad_y), s, font=fnt, fill=fill_fg)
    return right - w


def rule(draw, x0, x1, y, fill=INK, width=1):
    draw.line([x0, y, x1, y], fill=fill, width=width)


# --------------------------------------------------------------------------
# Page furniture: strap, masthead, deck, stat strip, region tally
# --------------------------------------------------------------------------

def draw_strap(draw):
    fnt = sans_bold(11)
    draw.text((MARGIN, 7), "THE WORLD IN ONE DAY", font=fnt, fill=INK)
    left2 = "13 STORIES DRAWN · 23 IN BRIEF"
    draw.text((MARGIN + 196, 7), left2, font=sans(11), fill=INK_SOFT)
    right = "36 STORIES · 7 REGIONS · ALL FRIDAY 20 NOVEMBER 2026"
    draw.text((W - MARGIN - text_w(draw, right, fnt), 7), right,
              font=fnt, fill=RED_DARK)
    rule(draw, MARGIN, W - MARGIN, 27, INK, 3)
    rule(draw, MARGIN, W - MARGIN, 31, INK, 1)


def draw_masthead(draw):
    title = "Friday 20 November 2026"
    fnt, _ = fit_font(draw, title, SERIF_BOLD_CANDIDATES, 96, W - 2 * MARGIN)
    centered(draw, W // 2, 38, title, fnt, INK)
    rule(draw, MARGIN, W - MARGIN, 128, INK, 1)
    rule(draw, MARGIN, W - MARGIN, 131, INK, 3)


def draw_deck(draw):
    deck = ("Kyiv under a huge overnight barrage · Cyclone Akvan ashore in "
            "Odisha · Asia's AI rout deepens · COP31's last day, still no deal")
    fnt, _ = fit_font(draw, deck, SERIF_ITALIC_CANDIDATES, 17, W - 2 * MARGIN)
    centered(draw, W // 2, 138, deck, fnt, INK_SOFT)


STATS = [
    ("300,000+", "people sheltered as Akvan hit Odisha"),
    ("3", "bridges hit in Kyiv overnight"),
    ("-6.2%", "Taiwan's close, worst of Asia's AI rout"),
    ("0", "fossil-fuel mentions in COP31's draft"),
    ("2.3%", "Japan inflation, Oct (core 2.2%)"),
    ("118", "Phillips' century v India"),
]


def draw_stats(draw, y0=162, y1=232):
    rule(draw, MARGIN, W - MARGIN, y0, HAIR, 1)
    col_w = (W - 2 * MARGIN) / 6
    num_fnt = serif_bold(30)
    gloss_fnt = sans(10)
    for i, (num, gloss) in enumerate(STATS):
        cx = MARGIN + col_w * i + col_w / 2
        centered(draw, cx, y0 + 5, num, num_fnt, RED)
        lines = wrap(draw, gloss, gloss_fnt, col_w - 12)
        gy = y0 + 41
        for line in lines[:2]:
            centered(draw, cx, gy, line, gloss_fnt, INK)
            gy += 11
        if i:
            draw.line([MARGIN + col_w * i, y0 + 10, MARGIN + col_w * i,
                       y1 - 10], fill=HAIR, width=1)
    rule(draw, MARGIN, W - MARGIN, y1, HAIR, 1)


REGIONS = [
    ("EUROPE", 9, NAVY),
    ("ASIA", 9, RED),
    ("MIDDLE EAST", 4, GOLD),
    ("AMERICAS", 5, GREEN),
    ("AFRICA", 3, (150, 84, 40)),
    ("OCEANIA", 3, BLUE),
    ("GLOBAL", 3, INK_SOFT),
]


def draw_tally(draw, y0=240):
    x = MARGIN
    total = sum(n for _, n, _ in REGIONS)
    span = W - 2 * MARGIN
    draw.text((x, y0), "WHERE THE DAY HAPPENED, BY REGION", font=sans_bold(9),
              fill=INK_SOFT)
    bar_y = y0 + 13
    for name, n, colour in REGIONS:
        w = span * n / total
        draw.rectangle([x, bar_y, x + w - 2, bar_y + 13], fill=colour)
        x += w
    label = " · ".join("%s %d" % (name, n) for name, n, _ in REGIONS)
    draw.text((MARGIN, bar_y + 16), label, font=sans_bold(10), fill=INK)
    return bar_y + 32


# --------------------------------------------------------------------------
# Hero illustrations (flat, original drawings)
# --------------------------------------------------------------------------

def burst(draw, cx, cy, r, colour):
    """A small explosion star."""
    pts = []
    for i in range(16):
        ang = i * math.pi / 8
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=colour)


def art_kyiv(draw, box):
    x0, y0, x1, y1 = box
    # night sky in horizontal bands
    bands = [(16, 24, 48), (24, 34, 64), (34, 46, 82), (46, 58, 100)]
    bh = (y1 - y0) // len(bands)
    for i, c in enumerate(bands):
        draw.rectangle([x0, y0 + i * bh, x1, y0 + (i + 1) * bh + 1], fill=c)
    # missile streaks falling from the top right
    for sx, sy, ex, ey in [(x1 - 30, y0 + 4, x1 - 96, y0 + 44),
                           (x1 - 74, y0 + 2, x1 - 128, y0 + 38),
                           (x1 - 8, y0 + 16, x1 - 58, y0 + 52)]:
        draw.line([sx, sy, ex, ey], fill=(240, 190, 90), width=2)
        draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=(255, 220, 130))
    # skyline silhouette
    base = y1 - 26
    for bx, bw, bh2 in [(6, 34, 30), (46, 26, 44), (78, 38, 24), (188, 30, 40),
                        (224, 24, 28), (254, 36, 48), (296, 24, 34)]:
        draw.rectangle([x0 + bx, base - bh2, x0 + bx + bw, base],
                       fill=(10, 14, 26))
        for wy in range(base - bh2 + 6, base - 6, 9):
            for wx in range(x0 + bx + 5, x0 + bx + bw - 5, 9):
                if (wx + wy) % 3:
                    draw.point((wx, wy), fill=(250, 205, 92))
    # a slim church tower with a spire for the Kyiv skyline
    draw.rectangle([x0 + 127, base - 30, x0 + 137, base], fill=(10, 14, 26))
    draw.polygon([(x0 + 125, base - 30), (x0 + 139, base - 30),
                  (x0 + 132, base - 41)], fill=(10, 14, 26))
    draw.rectangle([x0 + 146, base - 20, x0 + 168, base], fill=(10, 14, 26))
    # river and a bridge with a broken middle span
    draw.rectangle([x0, base, x1, y1], fill=(18, 34, 62))
    deck_y = base + 8
    draw.line([x0 + 4, deck_y, x0 + 118, deck_y], fill=(200, 205, 215), width=3)
    draw.line([x0 + 150, deck_y + 7, x1 - 4, deck_y], fill=(200, 205, 215),
              width=3)
    draw.line([x0 + 118, deck_y, x0 + 150, deck_y + 7], fill=(200, 205, 215),
              width=2)
    for px in (x0 + 60, x0 + 210):
        draw.rectangle([px, deck_y, px + 5, y1 - 2], fill=(120, 128, 140))
    burst(draw, x0 + 96, base - 18, 13, (255, 170, 60))
    burst(draw, x0 + 238, base - 30, 10, (255, 140, 60))
    burst(draw, x0 + 300, base - 8, 8, (255, 190, 80))


def art_akvan(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(196, 220, 228))
    # sea at the bottom, a coastal land mass on the right
    draw.rectangle([x0, y1 - 30, x1, y1], fill=(64, 116, 150))
    draw.polygon([(x1 - 58, y0), (x1, y0), (x1, y1 - 30), (x1 - 34, y1 - 30),
                  (x1 - 44, y0 + 30)], fill=(214, 196, 150))
    # a sandy shore strip along the bottom right for the shelters
    draw.polygon([(x0 + 148, y1), (x0 + 192, y1 - 30), (x1, y1 - 30),
                  (x1, y1)], fill=(222, 205, 160))
    # cyclone spiral
    cx, cy = x0 + 92, y0 + 44
    for r, start in [(40, 20), (31, 140), (22, 260), (13, 60)]:
        draw.arc([cx - r, cy - r * 0.72, cx + r, cy + r * 0.72], start,
                 start + 235, fill=(52, 92, 128), width=4)
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(52, 92, 128))
    # rain streaks over the sea
    for i in range(5):
        rx = x0 + 18 + i * 26
        draw.line([rx, y0 + 64, rx - 8, y0 + 80], fill=(70, 110, 140),
                  width=2)
    # palms leaning in the wind, rooted on the shore
    for px in (x1 - 52, x1 - 18):
        top = (px - 10, y1 - 58)
        draw.line([px, y1 - 30, px - 4, y1 - 44], fill=(110, 84, 50),
                  width=3)
        draw.line([px - 4, y1 - 44, top[0], top[1]], fill=(110, 84, 50),
                  width=3)
        for dx, dy in [(-15, 5), (-7, -8), (3, -11), (13, -3), (16, 8)]:
            draw.line([top[0], top[1], top[0] + dx, top[1] + dy],
                      fill=(66, 110, 72), width=2)
    # shelter tents on the shore
    for tx in (x0 + 202, x0 + 240, x0 + 278):
        draw.polygon([(tx, y1 - 26), (tx + 14, y1 - 44), (tx + 28, y1 - 26)],
                     fill=(196, 84, 60))
        draw.polygon([(tx + 10, y1 - 26), (tx + 14, y1 - 36),
                      (tx + 18, y1 - 26)], fill=(90, 40, 30))


def art_selloff(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(20, 26, 40))
    # circuit traces in the empty corners
    for tx, ty in [(26, 12), (110, 8), (52, 62)]:
        draw.line([x0 + tx, y0 + ty, x0 + tx + 24, y0 + ty],
                  fill=(46, 74, 110), width=2)
        draw.line([x0 + tx + 24, y0 + ty, x0 + tx + 24, y0 + ty + 10],
                  fill=(46, 74, 110), width=2)
        draw.ellipse([x0 + tx + 21, y0 + ty + 8, x0 + tx + 27, y0 + ty + 14],
                     outline=(46, 74, 110), width=2)
    # falling candles on the left two-thirds
    candles = [(16, 16, 30), (44, 24, 40), (72, 20, 36), (100, 34, 48),
               (128, 30, 46), (156, 44, 58), (184, 40, 56)]
    for cx, top, bot in candles:
        draw.line([x0 + cx + 6, y0 + top - 5, x0 + cx + 6, y0 + bot + 5],
                  fill=(230, 90, 90), width=1)
        draw.rectangle([x0 + cx, y0 + top, x0 + cx + 12, y0 + bot],
                       fill=(198, 52, 52))
    # trend line plunging toward the table
    pts = [(x0 + 14, y0 + 14), (x0 + 70, y0 + 26), (x0 + 124, y0 + 38),
           (x0 + 176, y0 + 50), (x0 + 208, y0 + 64)]
    draw.line(pts, fill=(255, 196, 84), width=3)
    draw.polygon([(x0 + 208, y0 + 64), (x0 + 193, y0 + 62),
                  (x0 + 200, y0 + 48)], fill=(255, 196, 84))
    # index closes as a small table on the right
    rows = [("TAIPEI", "-6.2%"), ("SEOUL", "-5.2%"), ("TOKYO", "-5.1%"),
            ("HONG KONG", "-1.9%")]
    tx, ty = x0 + 224, y0 + 8
    for name, val in rows:
        draw.text((tx, ty), name, font=sans_bold(8), fill=(168, 188, 220))
        draw.text((tx + 62, ty), val, font=sans_bold(8), fill=(255, 120, 120))
        ty += 12


HEROES = [
    {
        "art": art_kyiv, "label": "KYIV BARRAGE", "fact": "3 bridges hit",
        "source": "Officials' count", "kicker": "1 · KYIV, UKRAINE · WAR",
        "headline": "Missiles and drones pound Kyiv; power and water cut",
        "body": ("Some 110 missiles and 400 drones struck overnight. Three "
                 "bridges were hit, 3 people killed in the capital and 9 "
                 "across Ukraine. (Officials' count)"),
    },
    {
        "art": art_akvan, "label": "CYCLONE AKVAN", "fact": "Landfall · 8 am",
        "source": "Weather office", "kicker": "2 · GOPALPUR, INDIA · WEATHER",
        "headline": "Cyclone Akvan ashore in Odisha; 300,000 sheltered",
        "body": ("Winds 70-80 km/h, gusting 90, near Gopalpur from 8 am; "
                 "209 mm of rain at Patrapur. 423 rescue teams out; no "
                 "deaths reported. (Weather office)"),
    },
    {
        "art": art_selloff, "label": "AI SELL-OFF", "fact": "Closing prices",
        "source": "Market closes", "kicker": "3 · ASIA MARKETS · MONEY",
        "headline": "Asia's AI rout deepens as chip shares slide again",
        "body": ("Chipmakers led the fall after Wall Street's slide. Taiwan "
                 "had its worst week since 1991; SoftBank fell over 14%. "
                 "(Closing prices)"),
    },
]


def draw_hero(draw, x, y, w, h, hero):
    draw.rectangle([x, y, x + w, y + h], outline=HAIR, width=1)
    hero["art"](draw, (x + 1, y + 1, x + w - 1, y + 84))
    cy = y + 89
    chip(draw, x + 7, cy, hero["label"], sans_bold(10), RED, WHITE)
    chip_right(draw, x + w - 7, cy, hero["source"], sans(9), HAIR, INK_SOFT)
    ky = cy + 19
    draw.text((x + 7, ky), hero["kicker"], font=sans_bold(9), fill=RED_DARK)
    hy = ky + 13
    hy = draw_wrapped(draw, (x + 7, hy), hero["headline"], serif_bold(15),
                      INK, w - 14, 18, max_lines=2)
    draw_wrapped(draw, (x + 7, hy + 2), hero["body"], sans(11), INK,
                 w - 14, 13, max_lines=3)
    fact_w = text_w(draw, hero["fact"], sans_bold(9)) + 10
    draw.rounded_rectangle([x + w - fact_w - 7, y + 60, x + w - 7, y + 78],
                           radius=3, fill=NAVY)
    draw.text((x + w - fact_w - 2, y + 63), hero["fact"], font=sans_bold(9),
              fill=WHITE)


# --------------------------------------------------------------------------
# Card illustrations (small flat glyphs) and cards
# --------------------------------------------------------------------------

def icon_cop31(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(214, 228, 214))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(70, 120, 170))
    d.pieslice([cx - 15, cy - 15, cx + 15, cy + 15], 300, 60, fill=GREEN)
    d.pieslice([cx - 15, cy - 15, cx + 15, cy + 15], 130, 210, fill=GREEN)
    d.line([x0 + 12, y1 - 8, x1 - 12, y1 - 8], fill=INK_SOFT, width=2)
    d.polygon([(x1 - 34, y0 + 8), (x1 - 26, y0 + 20), (x1 - 42, y0 + 20)],
              fill=RED)


def icon_japan(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(240, 236, 226))
    cx, cy = x0 + 34, (y0 + y1) // 2
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline=INK, width=2)
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
    pts = [(x0 + 66, y1 - 10), (x0 + 96, y1 - 18), (x0 + 122, y1 - 14),
           (x0 + 158, y1 - 30)]
    d.line(pts, fill=RED, width=3)
    d.polygon([(x0 + 158, y1 - 30), (x0 + 144, y1 - 28), (x0 + 152, y1 - 18)],
              fill=RED)


def icon_uk_eu(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(226, 230, 240))
    # two flags facing each other
    d.rectangle([x0 + 18, y0 + 8, x0 + 62, y0 + 34], fill=(178, 34, 52))
    d.rectangle([x0 + 18, y0 + 19, x0 + 62, y0 + 23], fill=WHITE)
    d.rectangle([x0 + 36, y0 + 8, x0 + 44, y0 + 34], fill=WHITE)
    d.rectangle([x0 + 130, y0 + 8, x0 + 174, y0 + 34], fill=NAVY)
    for i in range(6):
        ang = i * 1.047
        sx = x0 + 152 + int(9 * __import__("math").cos(ang))
        sy = y0 + 21 + int(9 * __import__("math").sin(ang))
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=GOLD)
    # handshake bridge between them
    d.arc([x0 + 56, y0 + 6, x0 + 138, y0 + 44], 20, 160, fill=INK, width=2)


def icon_italy(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(238, 226, 210))
    # factory silhouette
    d.rectangle([x0 + 14, y1 - 22, x0 + 74, y1 - 6], fill=(90, 84, 74))
    d.rectangle([x0 + 22, y1 - 34, x0 + 30, y1 - 22], fill=(90, 84, 74))
    # picket signs
    for sx in (x0 + 104, x0 + 134, x0 + 164):
        d.line([sx, y1 - 6, sx, y0 + 16], fill=INK, width=2)
        d.rectangle([sx - 11, y0 + 6, sx + 11, y0 + 17], fill=WHITE,
                    outline=RED, width=1)


def icon_cricket(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(206, 226, 196))
    # bat
    d.polygon([(x0 + 52, y0 + 6), (x0 + 66, y0 + 10), (x0 + 46, y1 - 8),
               (x0 + 34, y1 - 12)], fill=(196, 158, 96), outline=INK)
    d.line([x0 + 58, y0 + 8, x0 + 76, y0 - 2], fill=INK, width=3)
    # ball with seam
    cx, cy = x0 + 138, (y0 + y1) // 2
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=RED)
    d.arc([cx - 8, cy - 11, cx + 2, cy + 11], 300, 60, fill=WHITE, width=1)
    d.arc([cx - 2, cy - 11, cx + 8, cy + 11], 120, 240, fill=WHITE, width=1)
    # stumps
    for sx in (x0 + 168, x0 + 176, x0 + 184):
        d.line([sx, y0 + 12, sx, y1 - 8], fill=(196, 158, 96), width=3)


def icon_seoul(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(232, 228, 238))
    # courthouse columns
    for cx in (x0 + 34, x0 + 62, x0 + 90, x0 + 118):
        d.rectangle([cx, y0 + 16, cx + 10, y1 - 10], fill=(150, 146, 160))
    d.polygon([(x0 + 24, y0 + 16), (x0 + 76, y0 + 4), (x0 + 128, y0 + 16)],
              fill=NAVY)
    d.rectangle([x0 + 20, y1 - 10, x0 + 132, y1 - 6], fill=NAVY)
    # gavel
    d.line([x0 + 150, y1 - 12, x0 + 172, y0 + 14], fill=(120, 84, 40),
           width=4)
    d.rectangle([x0 + 164, y0 + 6, x0 + 180, y0 + 16], fill=(120, 84, 40))


def icon_ballot(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(238, 232, 214))
    # ballot box and paper
    d.rectangle([x0 + 56, y1 - 26, x0 + 138, y1 - 6], fill=NAVY)
    d.rectangle([x0 + 78, y1 - 24, x0 + 116, y1 - 20], fill=INK)
    d.polygon([(x0 + 82, y0 + 4), (x0 + 112, y0 + 4), (x0 + 106, y1 - 22),
               (x0 + 88, y1 - 22)], fill=WHITE, outline=INK)
    d.line([x0 + 88, y0 + 12, x0 + 104, y0 + 12], fill=RED, width=2)
    d.line([x0 + 90, y0 + 18, x0 + 102, y0 + 18], fill=INK_SOFT, width=1)


def icon_hormuz(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(196, 218, 232))
    d.rectangle([x0, y1 - 12, x1, y1], fill=(64, 116, 150))
    # tanker
    d.polygon([(x0 + 34, y1 - 16), (x0 + 150, y1 - 16), (x0 + 138, y1 - 26),
               (x0 + 44, y1 - 26)], fill=(60, 60, 66))
    for tx in (x0 + 56, x0 + 82, x0 + 108):
        d.rectangle([tx, y1 - 34, tx + 18, y1 - 26], fill=(168, 60, 50))
    d.rectangle([x0 + 132, y1 - 38, x0 + 142, y1 - 26], fill=(60, 60, 66))
    # strait markers
    d.polygon([(x0 + 8, y0 + 2), (x0 + 40, y0 + 2), (x0 + 24, y0 + 14)],
              fill=(214, 196, 150))
    d.polygon([(x1 - 40, y0 + 2), (x1 - 8, y0 + 2), (x1 - 24, y0 + 14)],
              fill=(214, 196, 150))


def icon_f1(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(52, 56, 72))
    # rain
    for i in range(8):
        rx = x0 + 14 + i * 22
        d.line([rx, y0 + 4, rx - 4, y0 + 12], fill=(140, 170, 210), width=1)
    # simple race car
    d.polygon([(x0 + 30, y1 - 14), (x0 + 62, y1 - 22), (x0 + 118, y1 - 22),
               (x0 + 148, y1 - 14)], fill=RED)
    d.polygon([(x0 + 74, y1 - 22), (x0 + 88, y1 - 30), (x0 + 106, y1 - 30),
               (x0 + 116, y1 - 22)], fill=RED_DARK)
    d.rectangle([x0 + 22, y1 - 20, x0 + 40, y1 - 16], fill=INK)
    d.rectangle([x0 + 140, y1 - 26, x0 + 158, y1 - 22], fill=INK)
    for wx in (x0 + 48, x0 + 128):
        d.ellipse([wx - 8, y1 - 16, wx + 8, y1 - 2], fill=INK)
        d.ellipse([wx - 3, y1 - 11, wx + 3, y1 - 5], fill=(150, 150, 150))
    d.line([x0 + 8, y1 - 4, x1 - 8, y1 - 4], fill=(200, 200, 200), width=1)


def icon_fuel(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(240, 230, 200))
    # pump
    d.rectangle([x0 + 30, y0 + 8, x0 + 58, y1 - 6], fill=RED)
    d.rectangle([x0 + 36, y0 + 13, x0 + 52, y0 + 24], fill=WHITE)
    d.line([x0 + 58, y0 + 16, x0 + 68, y0 + 24], fill=INK, width=2)
    d.line([x0 + 68, y0 + 24, x0 + 68, y1 - 12], fill=INK, width=2)
    # queue of cars
    for i, cx in enumerate((x0 + 92, x0 + 128, x0 + 162)):
        yy = y1 - 14 - (i % 2) * 8
        d.rectangle([cx, yy, cx + 24, yy + 8], fill=NAVY_LIGHT)
        d.ellipse([cx + 3, yy + 6, cx + 9, yy + 12], fill=INK)
        d.ellipse([cx + 15, yy + 6, cx + 21, yy + 12], fill=INK)


CARDS = [
    {"icon": icon_cop31, "label": "COP31", "source": "Draft text",
     "kicker": "4 · ANTALYA, TÜRKIYE · CLIMATE",
     "headline": "Final day at COP31 - and still no deal",
     "body": "The draft omits fossil fuels; a $120bn adaptation gap stays open."},
    {"icon": icon_japan, "label": "JAPAN PRICES", "source": "Official data",
     "kicker": "5 · TOKYO, JAPAN · ECONOMY",
     "headline": "Inflation quickens: 2.3% headline, 2.2% core",
     "body": "Core rose 2.2%, its fastest this year; a December rise is in view."},
    {"icon": icon_uk_eu, "label": "UK-EU RESET", "source": "Agreed text",
     "kicker": "6 · BRUSSELS · EUROPE",
     "headline": "Britain and the EU seal their 'reset' deal",
     "body": "Food trade, a carbon link and 100,000 youth visas a year."},
    {"icon": icon_italy, "label": "ITALY STRIKE", "source": "Union count",
     "kicker": "7 · ROME, ITALY · LABOUR",
     "headline": "General strike stops Italy over the budget",
     "body": "CGIL's 24-hour stoppage fills some 100 squares; trains and transit hit."},
    {"icon": icon_cricket, "label": "CRICKET", "source": "Scorecard · ICC",
     "kicker": "8 · WELLINGTON, NZ · SPORT",
     "headline": "Phillips hits 118 as New Zealand pile up 368",
     "body": "Against India; Nicholls made 175* in a 216-run stand."},
    {"icon": icon_seoul, "label": "SEOUL COURT ROW", "source": "Broadcaster",
     "kicker": "9 · SEOUL, S KOREA · POLITICS",
     "headline": "Ruling party moves to impeach chief justice",
     "body": "Lawmakers target Cho Hee-dae after an overturned conviction. (SBS)"},
    {"icon": icon_ballot, "label": "BUKELE AGAIN", "source": "Filed",
     "kicker": "10 · SAN SALVADOR · POLITICS",
     "headline": "Bukele files to run for a third term",
     "body": "Filed at Thursday night's deadline; the vote is 28 February 2027."},
    {"icon": icon_hormuz, "label": "HORMUZ", "source": "Ship trackers",
     "kicker": "11 · STRAIT OF HORMUZ · SHIPPING",
     "headline": "Strait stays shut; 46 ships wait, Brent $92.50",
     "body": "The count was taken at 02:30 UTC, tankers holding off the strait."},
    {"icon": icon_f1, "label": "GRAND PRIX", "source": "Timing sheet",
     "kicker": "12 · LAS VEGAS, USA · F1",
     "headline": "Russell fastest in a wet Las Vegas practice",
     "body": "His 1:47.272 topped the times in the rain; qualifying is Saturday."},
    {"icon": icon_fuel, "label": "MALAWI FUEL", "source": "Ministry",
     "kicker": "13 · LILONGWE, MALAWI · FUEL",
     "headline": "Fuel crisis: a 20-litre daily cap in Malawi",
     "body": "Petrol is $3.24 a litre; the ministry blames a forex shortage."},
]


def draw_card(draw, x, y, w, h, card):
    draw.rectangle([x, y, x + w, y + h], outline=HAIR, width=1)
    card["icon"](draw, (x + 1, y + 1, x + w - 1, y + 45))
    chip(draw, x + 5, y + 28, card["label"], sans_bold(8), RED, WHITE,
         pad_x=4, pad_y=1)
    src_w = text_w(draw, card["source"], sans(8)) + 8
    draw.rounded_rectangle([x + w - src_w - 5, y + 28, x + w - 5, y + 43],
                           radius=3, fill=PAPER)
    draw.text((x + w - src_w - 1, y + 30), card["source"], font=sans(8),
              fill=INK_SOFT)
    draw.text((x + 6, y + 50), card["kicker"], font=sans_bold(8),
              fill=RED_DARK)
    hy = draw_wrapped(draw, (x + 6, y + 62), card["headline"], serif_bold(13),
                      INK, w - 12, 15, max_lines=2)
    draw_wrapped(draw, (x + 6, hy + 1), card["body"], sans(10), INK,
                 w - 12, 12, max_lines=2)


# --------------------------------------------------------------------------
# World map with numbered pins
# --------------------------------------------------------------------------

CONTINENTS = [
    [(8, 34), (30, 20), (58, 16), (76, 24), (72, 40), (58, 46), (52, 60),
     (40, 68), (30, 62), (18, 50), (10, 42)],                      # N America
    [(52, 74), (68, 72), (74, 84), (68, 106), (57, 122), (48, 102),
     (46, 86)],                                                    # S America
    [(126, 24), (148, 16), (168, 22), (166, 36), (152, 42), (139, 39),
     (131, 33)],                                                   # Europe
    [(132, 54), (158, 49), (174, 60), (172, 86), (159, 108), (142, 103),
     (134, 78)],                                                   # Africa
    [(168, 20), (212, 13), (250, 22), (264, 39), (247, 54), (229, 51),
     (215, 64), (197, 60), (183, 49), (171, 37)],                  # Asia
    [(196, 60), (209, 59), (202, 79)],                             # India
    [(222, 57), (235, 61), (229, 78), (220, 67)],                  # SE Asia
    [(238, 90), (263, 85), (272, 98), (255, 109), (240, 102)],     # Australia
    [(283, 116), (289, 112), (291, 119), (285, 124)],              # New Zealand
]

PINS = [
    (1, 160, 30), (2, 203, 66), (3, 233, 50), (4, 152, 45), (5, 253, 38),
    (6, 139, 27), (7, 146, 35), (8, 287, 120), (9, 238, 41), (10, 33, 60),
    (11, 177, 52), (12, 24, 42), (13, 157, 90),
]


def draw_map(draw, x, y, w, h):
    draw.text((x, y), "WHERE IT HAPPENED — THE 13 DRAWN STORIES",
              font=sans_bold(10), fill=INK)
    my = y + 15
    draw.rounded_rectangle([x, my, x + w, my + h], radius=6,
                           fill=(233, 223, 199))
    sx = w / 300.0
    sy = h / 132.0
    for poly in CONTINENTS:
        pts = [(x + px * sx, my + py * sy) for px, py in poly]
        draw.polygon(pts, fill=NAVY)
    for num, px, py in PINS:
        cx, cyy = x + px * sx, my + py * sy
        draw.ellipse([cx - 7, cyy - 7, cx + 7, cyy + 7], fill=RED,
                     outline=WHITE, width=1)
        label = str(num)
        tw = text_w(draw, label, sans_bold(8))
        draw.text((cx - tw / 2, cyy - 4), label, font=sans_bold(8),
                  fill=WHITE)


# --------------------------------------------------------------------------
# Briefs: 23 sourced one-liners (stories 14-36)
# --------------------------------------------------------------------------

BRIEFS = [
    (14, "BEIJING", "Loan rates held an 18th month: 3.0% / 3.5% (Xinhua)"),
    (15, "TURIN", "ATP groups end; semi-finals are Saturday (ATP)"),
    (16, "SHENZHEN", "Xi hails 'turnaround' in Australia ties (Xinhua)"),
    (17, "COX'S BAZAR", "Rohingya camps react to the ICJ ruling (AP)"),
    (18, "DAKAR", "Migrant boat sinks off Yenne; 4 dead (Agencies)"),
    (19, "SPACE", "BepiColombo reaches Mercury; orbit entry Sat (ESA)"),
    (20, "TONGA", "El Niño drought emergency declared (RNZ)"),
    (21, "DOROGOBUZH", "Plant hit by drones [CLAIM, unconfirmed]"),
    (22, "YEMEN", "Missile claim disputed by both sides [CLAIM]"),
    (23, "KHARKIV", "Drone hits a hospital; at least 4 hurt (Officials)"),
    (24, "KRYVYI RIH", "Drones cut power to hospitals (Officials)"),
    (25, "DNIPRO", "Five injured in a drone attack (Officials)"),
    (26, "SEOUL", "Court upholds Kakao founder's acquittal (Yonhap)"),
    (27, "GOLD", "Falls 2.6% to $3,526, lowest since Sep 2025 (Markets)"),
    (28, "ANTALYA", "France: fossil gap a 'black mark' on COP31 (AFP)"),
    (29, "SYDNEY", "General Pants enters administration (Filings)"),
    (30, "BEIT SHEMESH", "Haredi protesters clash with police (Press)"),
    (31, "DODOMA", "Tanzania now a top-five African gold holder (Bank)"),
    (32, "PORT-AU-PRINCE", "Raid kills 34 gang suspects (Police)"),
    (33, "MEXICO CITY", "116th Revolution Day marked (Government)"),
    (34, "SÃO PAULO", "Markets shut for Black Consciousness Day (B3)"),
    (35, "RED SEA", "Gunmen fire on a cargo ship off Yemen (UKMTO)"),
    (36, "SEOUL", "Sell-off triggers a KOSPI trading curb (Exchange)"),
]


def draw_briefs(draw, x, y, w):
    draw.text((x, y), "ALSO ON FRIDAY 20 NOVEMBER — 23 MORE STORIES",
              font=serif_bold(13), fill=INK)
    col_w = (w - 16) // 2
    top = y + 19
    pitch = 11.0
    for i, (num, place, text) in enumerate(BRIEFS):
        col = 0 if i < 12 else 1
        row = i if i < 12 else i - 12
        bx = x + col * (col_w + 16)
        by = top + row * pitch
        num_s = str(num)
        draw.text((bx, by), num_s, font=sans_bold(9), fill=RED)
        line = "%s — %s" % (place, text)
        fnt = sans(10)
        if text_w(draw, line, fnt) > col_w - 20:
            fnt = sans(9)
        draw.text((bx + 19, by), line, font=fnt, fill=INK)


# --------------------------------------------------------------------------
# Date check box and footer
# --------------------------------------------------------------------------

THURSDAY_ITEMS = [
    "Trump-Xi-Putin summit & APEC declaration, Shenzhen",
    "ICJ ruling on Myanmar (Rohingya) — Friday's camp reaction is story 17",
    "Wall Street's 2% fall — the sell-off's trigger, not its news",
    "GTA VI midnight launch · Voyager 1's one-light-day mark",
    "Crimean Bridge strike · Senate's 48-51 Iran war-powers vote",
]

NOT_YET_ITEMS = [
    "Any final COP31 deal — the closing plenary is Saturday 21",
    "BepiColombo's orbit insertion (Saturday)",
    "Las Vegas qualifying (Saturday) and the race itself",
    "The Turin ATP Finals title match (Sunday 22)",
]


def draw_date_check(draw, y0, y1):
    draw.rectangle([MARGIN, y0, W - MARGIN, y1], outline=RED, width=2)
    chip(draw, MARGIN + 8, y0 + 6, "DATE CHECK", sans_bold(10), RED, WHITE)
    draw.text((MARGIN + 92, y0 + 7),
              "WHAT WE LEFT OUT, AND WHY — the day is Friday 20 November 2026",
              font=sans_bold(10), fill=INK)
    col_x = [MARGIN + 10, W // 2 + 6]
    col_w = [W // 2 - MARGIN - 16, W - MARGIN - (W // 2 + 6) - 10]
    heads = ["THURSDAY 19 NOVEMBER'S NEWS — NOT FRIDAY'S:",
             "NOT YET HAPPENED — SO NOT SHOWN:"]
    for ci, items in enumerate((THURSDAY_ITEMS, NOT_YET_ITEMS)):
        draw.text((col_x[ci], y0 + 26), heads[ci], font=sans_bold(9),
                  fill=RED_DARK)
        iy = y0 + 38
        for item in items:
            draw.text((col_x[ci], iy), "· " + item, font=sans(9), fill=INK)
            iy += 10.2


def draw_footer(draw):
    rule(draw, MARGIN, W - MARGIN, 1008, INK, 1)
    line = ("Every story here happened, or was first reported, on Friday "
            "20 November 2026 · Officials' counts are attributed; claims "
            "are flagged, not stated as fact · Sources named beside each "
            "story · Original drawings")
    fnt, _ = fit_font(draw, line, SANS_CANDIDATES, 10, W - 2 * MARGIN)
    centered(draw, W // 2, 1011, line, fnt, INK_SOFT)


# --------------------------------------------------------------------------
# Assemble the page
# --------------------------------------------------------------------------

def build_page():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    draw_strap(draw)
    draw_masthead(draw)
    draw_deck(draw)
    draw_stats(draw, 156, 218)
    tally_end = draw_tally(draw, 224)
    hero_y = tally_end + 6
    hero_h = 208
    hero_w = (W - 2 * MARGIN - 16) // 3
    for i, hero in enumerate(HEROES):
        draw_hero(draw, MARGIN + i * (hero_w + 8), hero_y, hero_w, hero_h,
                  hero)
    card_y = hero_y + hero_h + 8
    card_h = 126
    card_w = (W - 2 * MARGIN - 32) // 5
    for r in range(2):
        for c in range(5):
            draw_card(draw, MARGIN + c * (card_w + 8),
                      card_y + r * (card_h + 6), card_w, card_h,
                      CARDS[r * 5 + c])
    band_y = card_y + 2 * card_h + 14
    draw_map(draw, MARGIN, band_y, 300, 128)
    draw_briefs(draw, MARGIN + 316, band_y, W - MARGIN - (MARGIN + 316))
    draw_date_check(draw, 916, 1004)
    draw_footer(draw)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build_page()
    img.save(os.path.join(out_dir, "entry.png"), format="PNG", optimize=True)


if __name__ == "__main__":
    main()
