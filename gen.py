#!/usr/bin/env python3
"""The World in One Day -- Friday 20 November 2026.

A one-page broadsheet that sums up one day's world news, drawn entirely by
this program with Pillow. It writes entry.png to /output (or to the folder
named by the MAKEFUN_OUTPUT_DIR environment variable). The drawing uses no
randomness, no clock and no network, so two runs write identical bytes.

Layout, top to bottom: strap line, dated masthead, deck, a six-number stat
strip, a region tally bar, three illustrated hero stories, ten illustrated
cards, a numbered-pin world map beside 27 sourced one-line briefs, a DATE
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
    left2 = "13 STORIES DRAWN · 27 IN BRIEF"
    draw.text((MARGIN + 196, 7), left2, font=sans(11), fill=INK_SOFT)
    right = "40 STORIES · 7 REGIONS · ALL FRIDAY 20 NOVEMBER 2026"
    draw.text((W - MARGIN - text_w(draw, right, fnt), 7), right,
              font=fnt, fill=RED_DARK)
    rule(draw, MARGIN, W - MARGIN, 27, INK, 3)
    rule(draw, MARGIN, W - MARGIN, 31, INK, 1)


def draw_masthead(draw):
    title = "Friday 20 November 2026"
    fnt, _ = fit_font(draw, title, SERIF_BOLD_CANDIDATES, 96, W - 2 * MARGIN)
    centered(draw, W // 2, 34, title, fnt, INK)
    rule(draw, MARGIN, W - MARGIN, 124, INK, 1)
    rule(draw, MARGIN, W - MARGIN, 127, INK, 3)


def draw_deck(draw):
    deck = ("Kyiv under a huge overnight barrage · Cyclone Akvan ashore in "
            "Odisha · Asia's AI rout deepens · COP31's last day, still no deal")
    fnt, _ = fit_font(draw, deck, SERIF_ITALIC_CANDIDATES, 17, W - 2 * MARGIN)
    centered(draw, W // 2, 133, deck, fnt, INK_SOFT)


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
        gy = y0 + 40
        for line in lines[:2]:
            centered(draw, cx, gy, line, gloss_fnt, INK)
            gy += 10
        if i:
            draw.line([MARGIN + col_w * i, y0 + 10, MARGIN + col_w * i,
                       y1 - 10], fill=HAIR, width=1)
    rule(draw, MARGIN, W - MARGIN, y1, HAIR, 1)


REGIONS = [
    ("EUROPE", 14, NAVY),
    ("ASIA", 10, RED),
    ("MIDDLE EAST", 5, GOLD),
    ("AFRICA", 4, (150, 84, 40)),
    ("AMERICAS", 3, GREEN),
    ("OCEANIA", 2, BLUE),
    ("GLOBAL", 2, INK_SOFT),
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
    # a lit suspension bridge: two towers, sagging cables, lamps on the deck
    for tx in (x0 + 60, x0 + 150):
        draw.rectangle([tx, base - 15, tx + 5, deck_y + 2],
                       fill=(150, 158, 170))
    draw.line([x0 + 4, deck_y, x0 + 62, base - 15], fill=(170, 178, 190),
              width=1)
    draw.line([x0 + 62, base - 15, x0 + 152, base - 15], fill=(170, 178, 190),
              width=1)
    draw.line([x0 + 152, base - 15, x1 - 4, deck_y], fill=(170, 178, 190),
              width=1)
    for lx in range(x0 + 16, x1 - 10, 16):
        draw.ellipse([lx - 1, deck_y - 3, lx + 2, deck_y],
                     fill=(255, 220, 130))
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
    # cyclone spiral, drawn large so it fills the panel
    cx, cy = x0 + 92, y0 + 44
    for r, start in [(54, 20), (43, 140), (31, 260), (20, 60), (10, 150)]:
        draw.arc([cx - r, cy - r * 0.72, cx + r, cy + r * 0.72], start,
                 start + 235, fill=(52, 92, 128), width=5)
    draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(52, 92, 128))
    # rain streaks over the sea
    for i in range(5):
        rx = x0 + 18 + i * 26
        draw.line([rx, y0 + 64, rx - 8, y0 + 80], fill=(70, 110, 140),
                  width=2)
    # a flooded road on the left, with a queue picking its way along it
    draw.polygon([(x0, y1 - 16), (x0 + 132, y1 - 16), (x0 + 152, y1),
                  (x0, y1)], fill=(148, 146, 138))
    for dx in range(8, 140, 18):
        draw.line([x0 + dx, y1 - 8, x0 + dx + 9, y1 - 8],
                  fill=(240, 238, 228), width=2)
    for qx in (x0 + 26, x0 + 44, x0 + 62):
        draw.rectangle([qx, y1 - 26, qx + 12, y1 - 17], fill=(70, 84, 96))
        draw.rectangle([qx + 2, y1 - 30, qx + 9, y1 - 26], fill=(70, 84, 96))
    for fx in (x0 + 92, x0 + 104, x0 + 116):
        draw.ellipse([fx, y1 - 27, fx + 4, y1 - 23], fill=(40, 40, 40))
        draw.line([fx + 2, y1 - 23, fx + 2, y1 - 15], fill=(40, 40, 40),
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
    cy = y + 88
    chip(draw, x + 7, cy, hero["label"], sans_bold(12), RED, WHITE)
    chip_right(draw, x + w - 7, cy, hero["source"], sans(10), HAIR, INK_SOFT)
    ky = cy + 20
    draw.text((x + 7, ky), hero["kicker"], font=sans_bold(9), fill=RED_DARK)
    hy = ky + 12
    hy = draw_wrapped(draw, (x + 7, hy), hero["headline"], serif_bold(15),
                      INK, w - 14, 16, max_lines=2)
    draw_wrapped(draw, (x + 7, hy + 2), hero["body"], sans(11), INK,
                 w - 14, 12, max_lines=3)
    fact_w = text_w(draw, hero["fact"], sans_bold(10)) + 10
    draw.rounded_rectangle([x + w - fact_w - 7, y + 58, x + w - 7, y + 76],
                           radius=3, fill=NAVY)
    draw.text((x + w - fact_w - 2, y + 61), hero["fact"], font=sans_bold(10),
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


def icon_poland(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(198, 216, 232))
    # a green field along the bottom, with a darker furrow stripe
    d.rectangle([x0, y1 - 24, x1, y1], fill=(96, 142, 78))
    d.rectangle([x0, y1 - 24, x1, y1 - 18], fill=(80, 122, 64))
    # a cruise missile slanting down toward the field, nose first
    d.polygon([(x0 + 128, y0 + 8), (x0 + 142, y0 + 15), (x0 + 88, y0 + 40),
               (x0 + 76, y0 + 31)], fill=(120, 126, 134))
    d.polygon([(x0 + 76, y0 + 31), (x0 + 88, y0 + 40), (x0 + 66, y0 + 44)],
              fill=RED)
    d.polygon([(x0 + 128, y0 + 8), (x0 + 140, y0 + 2), (x0 + 142, y0 + 15)],
              fill=(90, 96, 104))
    d.polygon([(x0 + 124, y0 + 18), (x0 + 136, y0 + 22), (x0 + 128, y0 + 30)],
              fill=(90, 96, 104))
    # motion streaks behind the tail
    for off in (0, 7, 14):
        d.line([x0 + 146 + off, y0 + 4 + off // 2, x0 + 168 + off,
                y0 + 10 + off // 2], fill=(240, 244, 248), width=2)
    # a burst where the nose meets the field
    burst(d, x0 + 62, y1 - 22, 10, (240, 170, 60))


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


def icon_cancer(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(233, 238, 230))
    # a big two-tone capsule across the top of the panel
    d.rounded_rectangle([x0 + 22, y0 + 8, x0 + 118, y0 + 30], radius=11,
                        fill=WHITE, outline=INK, width=2)
    d.rounded_rectangle([x0 + 22, y0 + 8, x0 + 70, y0 + 30], radius=11,
                        fill=RED)
    d.rectangle([x0 + 59, y0 + 10, x0 + 70, y0 + 28], fill=RED)
    # tumour circles shrinking from left to right beneath the pill
    for cx, r in [(x0 + 48, 12), (x0 + 96, 9), (x0 + 136, 6)]:
        cy = y1 - 16
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED_DARK,
                  width=2)
        d.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2],
                  fill=RED)
    # a small green down-step marker at the end of the row
    d.polygon([(x0 + 158, y1 - 22), (x0 + 170, y1 - 22), (x0 + 164, y1 - 10)],
              fill=GREEN)


def icon_kenya(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(220, 232, 238))
    d.ellipse([x1 - 44, y0 + 6, x1 - 18, y0 + 32], fill=GOLD)
    # a drilling derrick: a braced triangle tower with a drill line
    apex = (x0 + 88, y0 + 8)
    d.line([x0 + 52, y1 - 10, apex[0], apex[1]], fill=INK, width=3)
    d.line([x0 + 124, y1 - 10, apex[0], apex[1]], fill=INK, width=3)
    d.line([x0 + 64, y1 - 26, x0 + 112, y1 - 26], fill=INK, width=2)
    d.line([x0 + 64, y1 - 26, x0 + 112, y1 - 10], fill=INK_SOFT, width=1)
    d.line([x0 + 112, y1 - 26, x0 + 64, y1 - 10], fill=INK_SOFT, width=1)
    d.line([apex[0], apex[1], apex[0], y1 - 26], fill=RED, width=2)
    # dry ground, and a first drop of crude beside the tower
    d.rectangle([x0, y1 - 10, x1, y1], fill=(150, 116, 74))
    d.polygon([(x0 + 150, y1 - 24), (x0 + 158, y1 - 12), (x0 + 142, y1 - 12)],
              fill=INK)
    d.ellipse([x0 + 143, y1 - 14, x0 + 157, y1 - 8], fill=INK)


def icon_iraq(d, b):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=(230, 221, 198))
    # a stronghold block on the right, with crenellations and a doorway
    d.rectangle([x0 + 128, y0 + 18, x1 - 8, y1 - 8], fill=(178, 152, 104))
    for mx in range(x0 + 132, x1 - 16, 14):
        d.rectangle([mx, y0 + 10, mx + 8, y0 + 18], fill=(178, 152, 104))
    d.rectangle([x0 + 152, y1 - 24, x0 + 166, y1 - 8], fill=(90, 70, 44))
    # a tank rolling in from the left toward the stronghold
    d.rounded_rectangle([x0 + 14, y1 - 22, x0 + 78, y1 - 8], radius=6,
                        fill=(84, 92, 62))
    d.polygon([(x0 + 22, y1 - 22), (x0 + 34, y1 - 32), (x0 + 70, y1 - 32),
               (x0 + 78, y1 - 22)], fill=(96, 104, 70))
    d.rectangle([x0 + 40, y1 - 40, x0 + 62, y1 - 32], fill=(84, 92, 62))
    d.line([x0 + 62, y1 - 36, x0 + 96, y1 - 36], fill=(60, 66, 46), width=4)
    for wx in (x0 + 26, x0 + 46, x0 + 66):
        d.ellipse([wx - 4, y1 - 19, wx + 4, y1 - 11], fill=(52, 58, 38))
    # sand along the bottom
    d.rectangle([x0, y1 - 8, x1, y1], fill=(196, 172, 122))


CARDS = [
    {"icon": icon_cop31, "label": "COP31", "source": "Draft text",
     "kicker": "4 · ANTALYA, TÜRKIYE · CLIMATE",
     "headline": "Final day at COP31 - and still no deal",
     "body": "The draft omits fossil fuels; a $120bn adaptation gap stays."},
    {"icon": icon_japan, "label": "JAPAN PRICES", "source": "Official data",
     "kicker": "5 · TOKYO, JAPAN · ECONOMY",
     "headline": "Inflation quickens: 2.3% headline, 2.2% core",
     "body": "Core up 2.2%, fastest this year; a December rise in view."},
    {"icon": icon_uk_eu, "label": "UK-EU RESET", "source": "Agreed text",
     "kicker": "6 · BRUSSELS · EUROPE",
     "headline": "Britain and the EU seal their 'reset' deal",
     "body": "Food trade, a carbon link and 100,000 youth visas a year."},
    {"icon": icon_italy, "label": "ITALY STRIKE", "source": "Union count",
     "kicker": "7 · ROME, ITALY · LABOUR",
     "headline": "General strike stops Italy over the budget",
     "body": "CGIL's 24-hour stoppage fills 100 squares; transit hit."},
    {"icon": icon_cricket, "label": "CRICKET", "source": "Scorecard · ICC",
     "kicker": "8 · WELLINGTON, NZ · SPORT",
     "headline": "Phillips hits 118 as New Zealand pile up 368",
     "body": "Against India; Nicholls made 175* in a 216-run stand."},
    {"icon": icon_poland, "label": "POLAND: MISSILE", "source": "Reuters",
     "kicker": "9 · EASTERN POLAND · SECURITY",
     "headline": "Russian cruise missile lands in Poland",
     "body": "Kh-101 in a field; two airports paused, no one hurt. (Reuters)"},
    {"icon": icon_cancer, "label": "CANCER PILL", "source": "Trial data",
     "kicker": "10 · BARCELONA, SPAIN · HEALTH",
     "headline": "Pancreatic cancer pill: 60.7% respond",
     "body": "Tumours shrank with chemo in 61 patients; chemo alone: 23-42%."},
    {"icon": icon_kenya, "label": "KENYA: OIL", "source": "allAfrica",
     "kicker": "11 · TURKANA, KENYA · ENERGY",
     "headline": "Kenya starts drilling its first oil well",
     "body": "First crude from Turkana is due on 1 December. (allAfrica)"},
    {"icon": icon_iraq, "label": "IRAQ: ARMY IN", "source": "Reuters",
     "kicker": "12 · JURF AL-SAKHAR, IRAQ · SECURITY",
     "headline": "Iraqi army enters a militia stronghold",
     "body": "Troops move into Jurf al-Sakhar, a militia base. (Reuters)"},
    {"icon": icon_ballot, "label": "BUKELE AGAIN", "source": "Filed",
     "kicker": "13 · SAN SALVADOR · POLITICS",
     "headline": "Bukele files to run for a third term",
     "body": "Filings close: Bukele is in for a third term; vote 28 Feb 2027."},
]


def draw_card(draw, x, y, w, h, card):
    draw.rectangle([x, y, x + w, y + h], outline=HAIR, width=1)
    card["icon"](draw, (x + 1, y + 1, x + w - 1, y + 68))
    chip(draw, x + 5, y + 49, card["label"], sans_bold(11), RED, WHITE,
         pad_x=5, pad_y=2)
    src_w = text_w(draw, card["source"], sans(9)) + 8
    draw.rounded_rectangle([x + w - src_w - 5, y + 49, x + w - 5, y + 64],
                           radius=3, fill=PAPER)
    draw.text((x + w - src_w - 1, y + 52), card["source"], font=sans(9),
              fill=INK_SOFT)
    draw.text((x + 6, y + 74), card["kicker"], font=sans_bold(9),
              fill=RED_DARK)
    hy = draw_wrapped(draw, (x + 6, y + 86), card["headline"], serif_bold(13),
                      INK, w - 12, 14, max_lines=2)
    draw_wrapped(draw, (x + 6, hy + 1), card["body"], sans(10), INK,
                 w - 12, 11, max_lines=2)


# --------------------------------------------------------------------------
# World map with numbered pins
# --------------------------------------------------------------------------

CONTINENTS = [
    [(8, 34), (22, 24), (38, 18), (58, 16), (70, 20), (76, 24), (74, 34),
     (66, 42), (58, 46), (54, 54), (50, 62), (42, 68), (34, 66), (28, 58),
     (18, 50), (12, 44), (8, 38)],                                 # N America
    [(52, 74), (62, 71), (70, 74), (74, 84), (72, 96), (66, 110),
     (60, 120), (57, 124), (52, 112), (48, 98), (46, 86)],         # S America
    [(126, 24), (138, 18), (150, 16), (160, 19), (168, 22), (167, 30),
     (160, 37), (152, 42), (143, 40), (136, 36), (131, 33),
     (127, 28)],                                                   # Europe
    [(132, 54), (146, 50), (158, 49), (168, 54), (174, 62), (172, 76),
     (166, 94), (159, 108), (150, 106), (142, 103), (137, 90),
     (134, 72), (132, 62)],                                        # Africa
    [(168, 20), (190, 15), (212, 13), (232, 16), (250, 22), (260, 30),
     (264, 39), (255, 48), (247, 54), (236, 53), (229, 51), (220, 58),
     (215, 64), (205, 62), (197, 60), (190, 54), (183, 49), (176, 42),
     (171, 37), (169, 28)],                                        # Asia
    [(196, 60), (204, 59), (209, 59), (206, 68), (202, 79),
     (199, 70)],                                                   # India
    [(222, 57), (230, 58), (235, 61), (233, 70), (229, 78),
     (224, 72), (220, 67)],                                        # SE Asia
    [(238, 90), (250, 86), (263, 85), (270, 90), (272, 98), (264, 105),
     (255, 109), (246, 106), (240, 102)],                          # Australia
    [(283, 116), (287, 111), (289, 112), (291, 119), (288, 123),
     (285, 124)],                                                  # New Zealand
]

# Pins: (story, anchor x, anchor y, circle x, circle y) in map coordinates.
# In crowded Europe the numbered circle is offset from its anchor point and
# joined to it by a thin leader line, so no two circles touch.
PINS = [
    (1, 160, 30, 160, 30),      # Kyiv
    (2, 203, 66, 203, 66),      # Gopalpur, Odisha
    (3, 233, 50, 233, 50),      # Asia sell-off (Taipei)
    (4, 155, 44, 167, 54),      # Antalya, COP31
    (5, 253, 38, 253, 38),      # Tokyo
    (6, 138, 26, 126, 17),      # Brussels
    (7, 145, 36, 136, 45),      # Rome
    (8, 287, 120, 287, 120),    # Wellington
    (9, 163, 25, 177, 15),      # Eastern Poland
    (10, 131, 34, 117, 41),     # Barcelona
    (11, 163, 84, 163, 84),     # Turkana, Kenya
    (12, 177, 52, 191, 59),     # Jurf al-Sakhar, Iraq
    (13, 33, 60, 33, 60),       # San Salvador
]


def draw_map(draw, x, y, w, h):
    draw.text((x, y), "WHERE IT HAPPENED — THE 13 DRAWN STORIES",
              font=sans_bold(10), fill=INK)
    my = y + 15
    draw.rounded_rectangle([x, my, x + w, my + h], radius=6, fill=NAVY)
    sx = w / 300.0
    sy = h / 132.0
    for poly in CONTINENTS:
        pts = [(x + px * sx, my + py * sy) for px, py in poly]
        draw.polygon(pts, fill=TAN)
    for num, ax, ay, cx, cy in PINS:
        px, py = x + ax * sx, my + ay * sy
        qx, qy = x + cx * sx, my + cy * sy
        if (ax, ay) != (cx, cy):
            draw.line([px, py, qx, qy], fill=(210, 205, 190), width=1)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=WHITE)
        draw.ellipse([qx - 6, qy - 6, qx + 6, qy + 6], fill=RED,
                     outline=WHITE, width=1)
        label = str(num)
        tw = text_w(draw, label, sans_bold(8))
        draw.text((qx - tw / 2, qy - 4), label, font=sans_bold(8),
                  fill=WHITE)


# --------------------------------------------------------------------------
# Briefs: 27 sourced one-liners (stories 14-40)
# --------------------------------------------------------------------------

BRIEFS = [
    (14, "BEIJING", "Loan rates held an 18th month: 3.0% / 3.5% (Xinhua)"),
    (15, "TURIN", "ATP groups end; semi-finals are Saturday (ATP)"),
    (16, "SHENZHEN", "Xi hails 'turnaround' in Australia ties (Xinhua)"),
    (17, "COX'S BAZAR", "Rohingya camps react to the ICJ ruling (AP)"),
    (18, "SPACE", "BepiColombo reaches Mercury; orbit entry Sat (ESA)"),
    (19, "DOROGOBUZH", "Plant hit by drones [CLAIM, unconfirmed]"),
    (20, "YEMEN", "Missile claim disputed by both sides [CLAIM]"),
    (21, "KHARKIV", "Drone hits a hospital; at least 4 hurt (Officials)"),
    (22, "KRYVYI RIH", "Drones cut power to hospitals (Officials)"),
    (23, "DNIPRO", "Five injured in a drone attack (Officials)"),
    (24, "SEOUL", "Court upholds Kakao founder's acquittal (Yonhap)"),
    (25, "GOLD", "Falls 2.6% to $3,526, lowest since Sep 2025 (Markets)"),
    (26, "ANTALYA", "France: fossil gap a 'black mark' on COP31 (AFP)"),
    (27, "SYDNEY", "General Pants enters administration (Filings)"),
    (28, "BEIT SHEMESH", "Haredi protesters clash with police (Press)"),
    (29, "DODOMA", "Tanzania now a top-five African gold holder (Bank)"),
    (30, "PORT-AU-PRINCE", "Raid kills 34 gang suspects (Police)"),
    (31, "RED SEA", "Gunmen fire on a cargo ship off Yemen (UKMTO)"),
    (32, "SEOUL", "Sell-off triggers a KOSPI trading curb (Exchange)"),
    (33, "LVIV", "Railway-station strike kills two (BBC)"),
    (34, "AFRICA", "AfDB: 22 countries in debt distress (allAfrica)"),
    (35, "TALLINN", "Estonia shuts Russia road border 1 Dec (Reuters)"),
    (36, "BERLIN", "Pupils strike against military service (Al Jazeera)"),
    (37, "HORMUZ", "Strait shut; 46 ships wait, Brent $92.50 (Trackers)"),
    (38, "LAS VEGAS", "Russell tops wet practice, 1:47.272 (Timing)"),
    (39, "LILONGWE", "20-litre daily fuel cap; petrol $3.24 (Ministry)"),
    (40, "SEOUL", "Ruling party moves to impeach chief justice (SBS)"),
]


def draw_briefs(draw, x, y, w):
    draw.text((x, y), "ALSO ON FRIDAY 20 NOVEMBER — %d MORE STORIES"
              % len(BRIEFS), font=serif_bold(13), fill=INK)
    col_w = (w - 16) // 2
    top = y + 19
    pitch = 10.4
    half = (len(BRIEFS) + 1) // 2
    for i, (num, place, text) in enumerate(BRIEFS):
        col = 0 if i < half else 1
        row = i if i < half else i - half
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
    "ICJ ruling on Myanmar (Rohingya) — camp reaction is story 17",
    "Tonga's drought emergency · the migrant boat lost off Senegal",
    "Wall Street's 2% fall — the sell-off's trigger, not its news",
    "GTA VI launch · Voyager 1 mark · Crimean Bridge · Senate vote",
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
        draw.text((col_x[ci], y0 + 24), heads[ci], font=sans_bold(9),
                  fill=RED_DARK)
        iy = y0 + 34
        for item in items:
            draw.text((col_x[ci], iy), "· " + item, font=sans(9), fill=INK)
            iy += 9.8


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
    draw_stats(draw, 152, 208)
    tally_end = draw_tally(draw, 214)
    hero_y = tally_end + 1
    hero_h = 190
    hero_w = (W - 2 * MARGIN - 16) // 3
    for i, hero in enumerate(HEROES):
        draw_hero(draw, MARGIN + i * (hero_w + 8), hero_y, hero_w, hero_h,
                  hero)
    card_y = hero_y + hero_h + 8
    card_h = 140
    card_w = (W - 2 * MARGIN - 32) // 5
    for r in range(2):
        for c in range(5):
            draw_card(draw, MARGIN + c * (card_w + 8),
                      card_y + r * (card_h + 6), card_w, card_h,
                      CARDS[r * 5 + c])
    band_y = card_y + 2 * card_h + 12
    draw_map(draw, MARGIN, band_y, 340, 114)
    draw_briefs(draw, MARGIN + 356, band_y, W - MARGIN - (MARGIN + 356))
    draw_date_check(draw, 916, 1002)
    draw_footer(draw)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build_page()
    img.save(os.path.join(out_dir, "entry.png"), format="PNG", optimize=True)


if __name__ == "__main__":
    main()
