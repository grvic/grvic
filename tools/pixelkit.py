"""pixelkit — tiny, dependency-free helpers to draw the Future-XP pixel look as SVG.

Shared by tools/build.py (README + static assets) and .github/scripts/stats_card.py
(daily GitHub activity card). Only the Python standard library is used.
"""
from __future__ import annotations

import json
import math
import os
from xml.sax.saxutils import escape as _esc

HERE = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- fonts
FONT_UI = "Tahoma, 'Segoe UI', Verdana, system-ui, -apple-system, sans-serif"
FONT_MONO = "'Cascadia Code', 'Cascadia Mono', Consolas, 'SFMono-Regular', Menlo, ui-monospace, monospace"

# --------------------------------------------------------------------------- themes
THEMES = {
    "light": dict(
        name="light",
        sky=("#4B8DF5", "#79ABF7", "#DFF3FF"), cloud_back="#B9D4FA", cloud_front="#F9FCFF",
        hill=("#4F8F16", "#71AD18", "#3D7416"), hill_hi="#88C92C", hill_lo="#2E5D16",
        paper="#FFFDF7", paper2="#F3F0E6", ink="#0E1726", ink2="#3B4A5E", ink3="#9AA6B8",
        title_a="#1F5FD6", title_b="#4FA3F7", frame="#0B3A8C", shadow="#0E1726", shadow_op=".22",
        sparkle="#FFD23F", name_shadow="#0B2F7A", accent="#1F5FD6", accent2="#D6337F",
        taskbar=("#3F8CF3", "#245EDC", "#1D4FC0"), tray="#1A9BF0", start=("#4CB04C", "#2F8A2F"),
        chip_text="#0E1726", heat=("#E7F3D4", "#B6DD7A", "#88C92C", "#4F8F16", "#2E5D16"),
    ),
    "dark": dict(
        name="dark",
        sky=("#05081A", "#141C3D", "#22305C"), cloud_back="#1A2650", cloud_front="#2B3B70",
        hill=("#1F4A12", "#2C5E14", "#173A0E"), hill_hi="#3E7A1E", hill_lo="#0F2A09",
        paper="#18213A", paper2="#121A2E", ink="#F2EFD9", ink2="#C5CCDA", ink3="#6F7C95",
        title_a="#2A3E7A", title_b="#39D0B6", frame="#000000", shadow="#000000", shadow_op=".5",
        sparkle="#39D0B6", name_shadow="#000000", accent="#7CC0FF", accent2="#FF8AC4",
        taskbar=("#2A3E7A", "#1B2A55", "#0E1838"), tray="#24346B", start=("#3C9B5F", "#25653D"),
        chip_text="#0E1726", heat=("#161B22", "#1F4A12", "#2C6E14", "#4F8F16", "#88C92C"),
    ),
}

TRACKS = {
    "cloud": dict(label="Cloud", light="#7CC0FF", base="#1F5FD6", dark="#0B2F7A"),
    "ai": dict(label="Azure AI", light="#C7B6FF", base="#7B5CFF", dark="#33208F"),
    "data": dict(label="Data & Fabric", light="#8FF0D4", base="#12A38A", dark="#06493E"),
    "biz": dict(label="Business AI", light="#FFD0A1", base="#FF7A1A", dark="#8A3400"),
    "agent": dict(label="Agentic AI", light="#FFB3D9", base="#D6337F", dark="#6B0F3B"),
    "dev": dict(label="GitHub", light="#B9C4D6", base="#3B4A5E", dark="#0E1726"),
    "dbx": dict(label="Databricks", light="#FFB3A3", base="#E8452C", dark="#7A1606"),
}

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


def esc(s: str) -> str:
    return _esc(str(s), {'"': "&quot;"})


# --------------------------------------------------------------------------- 5x7 pixel font
_GLYPHS = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10001 10101 10001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000", ".": "00000 00000 00000 00000 00000 01100 01100",
    "-": "00000 00000 00000 11111 00000 00000 00000", "_": "00000 00000 00000 00000 00000 00000 11111",
    "!": "00100 00100 00100 00100 00100 00000 00100", "?": "01110 10001 00001 00010 00100 00000 00100",
    ":": "00000 01100 01100 00000 01100 01100 00000", "/": "00001 00010 00010 00100 01000 01000 10000",
    "&": "01100 10010 10100 01000 10101 10010 01101", "@": "01110 10001 10111 10101 10111 10000 01110",
    ">": "01000 00100 00010 00001 00010 00100 01000", "<": "00010 00100 01000 10000 01000 00100 00010",
    "#": "01010 01010 11111 01010 11111 01010 01010", "+": "00000 00100 00100 11111 00100 00100 00000",
    "'": "00100 00100 01000 00000 00000 00000 00000", "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000", "*": "00000 10101 01110 11111 01110 10101 00000",
    ",": "00000 00000 00000 00000 01100 00100 01000", "%": "11001 11010 00010 00100 01000 01011 10011",
}
GLYPHS = {k: [row for row in v.split()] for k, v in _GLYPHS.items()}


def ptext_width(s: str, scale: float = 1) -> float:
    return (len(s) * 6 - 1) * scale


def ptext_path(s: str) -> str:
    """Path data (in glyph units, 1 unit = 1 pixel) for a string in the 5x7 font."""
    d = []
    for i, ch in enumerate(s.upper()):
        g = GLYPHS.get(ch, GLYPHS["?"])
        ox = i * 6
        for y, row in enumerate(g):
            x = 0
            while x < 5:
                if row[x] == "1":
                    x0 = x
                    while x < 5 and row[x] == "1":
                        x += 1
                    d.append(f"M{ox + x0} {y}h{x - x0}v1h-{x - x0}z")
                else:
                    x += 1
    return "".join(d)


def ptext(s: str, x: float, y: float, scale: float, fill: str, extra: str = "") -> str:
    return (f'<path d="{ptext_path(s)}" fill="{fill}" transform="translate({x} {y}) scale({scale})" '
            f'shape-rendering="crispEdges" {extra}/>')


# --------------------------------------------------------------------------- 16x16 pixel icons
PAL = {
    "k": "#0E1726", "w": "#FFFFFF", "b": "#1F5FD6", "l": "#7CC0FF", "y": "#FFD23F", "o": "#FF7A1A",
    "g": "#2F9E44", "G": "#8FD16A", "r": "#E0482C", "p": "#D6337F", "v": "#7B5CFF", "s": "#C5CCDA",
    "d": "#3B4A5E", "t": "#F3F0E6", "n": "#8A5A2B", "h": "#3A2416", "S": "#F2C6A0", "m": "#C2185B",
    "c": "#1F5FD6", "B": "#DCEEFF", "e": "#0E1726", "T": "#12A38A",
}

ICONS = {
    "doc": [
        "..kkkkkkkkk.....", "..kwwwwwwwkk....", "..kwwwwwwwkwk...", "..kwbbbbwwkkkk..",
        "..kwwwwwwwwwwk..", "..kwllllllllwk..", "..kwwwwwwwwwwk..", "..kwllllllllwk..",
        "..kwwwwwwwwwwk..", "..kwlllllwwwwk..", "..kwwwwwwwwwwk..", "..kwooooooowwk..",
        "..kwwwwwwwwwwk..", "..kwwwwwwwwwwk..", "..kkkkkkkkkkkk..", "................",
    ],
    "medal": [
        "...kkk....kkk...", "...kbbk..krrk...", "....kbbkkrrk....", ".....kbbrrk.....",
        "......kbrk......", ".....kkkkkk.....", "....kyyyyyyk....", "...kyywwyyyyk...",
        "...kywyyyyyok...", "...kyyyykyyok...", "...kyyykkkyok...", "...kyyyykyyok...",
        "...kyyyyyyook...", "....kyoooook....", ".....kkkkkk.....", "................",
    ],
    "folder": [
        "................", ".kkkkk..........", "kyyyyyk.........", "kyyyyyykkkkkkkk.",
        "kyyyyyyyyyyyyyk.", "kowwwwwwwwwwwwok", "koyyyyyyyyyyyyok", "koyyyyyyyyyyyyok",
        "koyyyyyyyyyyyyok", "koyyyyyyyyyyyyok", "koyyyyyyyyyyyyok", "koyyyyyyyyyyyyok",
        "kooooooooooooook", ".kkkkkkkkkkkkkk.", "................", "................",
    ],
    "mic": [
        "......kkkk......", ".....kssssk.....", ".....ksddsk.....", ".....kssssk.....",
        ".....ksddsk.....", ".....kssssk.....", "...k.ksddsk.k...", "...k.kssssk.k...",
        "...kk.kkkk.kk...", "....kk....kk....", ".....kkkkkk.....", ".......kk.......",
        ".......kk.......", ".....kkkkkk.....", "................", "................",
    ],
    "pen": [
        "............kkk.", "...........kwwk.", "..........kwwvk.", ".........kwwvk..",
        "........kwwvk...", ".......kwwvk....", "......kwwvk.....", ".....kwwvk......",
        "....kwwvk.......", "...kyyvk........", "...kyyk.........", "..kkkk..........",
        "..kk............", ".k..............", "................", "................",
    ],
    "chart": [
        "................", ".k..............", ".k..........kkk.", ".k..........kgk.",
        ".k......kkk.kgk.", ".k......kbk.kgk.", ".k......kbk.kgk.", ".k..kkk.kbk.kgk.",
        ".k..kok.kbk.kgk.", ".k..kok.kbk.kgk.", ".k..kok.kbk.kgk.", ".k..kok.kbk.kgk.",
        ".kkkkkkkkkkkkkkk", "................", "................", "................",
    ],
    "cpu": [
        "................", ".....k.k.k.k....", "....kkkkkkkkk...", "....kdddddddk...",
        "...kkdllllldkk..", "....kdlbbbldk...", "...kkdlbvbldkk..", "....kdlbbbldk...",
        "...kkdllllldkk..", "....kdddddddk...", "....kkkkkkkkk...", ".....k.k.k.k....",
        "................", "................", "................", "................",
    ],
    "book": [
        "................", "..kkkkkk.kkkkkk.", ".kwwwwwwkwwwwwwk", ".kwllllwkwllllwk",
        ".kwwwwwwkwwwwwwk", ".kwllllwkwllllwk", ".kwwwwwwkwwwwwwk", ".kwlllwwkwlllwwk",
        ".kwwwwwwkwwwwwwk", ".kbbbbbbkbbbbbbk", "..kkkkkkkkkkkkk.", "................",
        "................", "................", "................", "................",
    ],
    "star": [
        ".......k........", "......kyk.......", "......kyk.......", ".....kyyyk......",
        "kkkkkyyyyykkkkk.", ".kyyyyywyyyyyk..", "..kyyyywyyyyk...", "...kyyyyyyyk....",
        "...kyyyyyyyk....", "..kyyyykyyyyk...", "..kyyk...kyyk...", ".kyk.......kyk..",
        ".kk.........kk..", "................", "................", "................",
    ],
    "card": [
        "................", ".kkkkkkkkkkkkkk.", ".kbbbbbbbbbbbbk.", ".kwwwwwwwwwwwwk.",
        ".kwwkkwwwwwwwwk.", ".kwkbbkwwddddwk.", ".kwkbbkwwwwwwwk.", ".kwwkkwwwddddwk.",
        ".kwkbbkwwwwwwwk.", ".kkbbbbkwwddwwk.", ".kwwwwwwwwwwwwk.", ".kkkkkkkkkkkkkk.",
        "................", "................", "................", "................",
    ],
    "globe": [
        ".....kkkkkk.....", "...kkbbGGbbkk...", "..kbbGGGGbbbbk..", ".kbbbGGGbbbGGbk.",
        ".kbbbbGbbbGGGbk.", "kbbbbbbbbbGGGbbk", "kbGGbbbbbbbGbbbk", "kGGGGbbbbbbbbbbk",
        "kbGGGGbbbbbbbbbk", "kbbGGGbbbbGGbbbk", ".kbbGbbbbGGGGbk.", ".kbbbbbbbbGGbbk.",
        "..kbbbbbbbbbbk..", "...kkbbbbbbkk...", ".....kkkkkk.....", "................",
    ],
    "computer": [
        "................", ".kkkkkkkkkkkkkk.", ".kssssssssssssk.", ".ksdddddddddddk.",
        ".ksdTTddddddddk.", ".ksddddddddddsk.", ".ksdTTTTdddddsk.", ".ksddddddddddsk.",
        ".kssssssssssssk.", ".kkkkkkkkkkkkkk.", "......kssk......", "....kkkkkkkk....",
        "...kssssssssk...", "...kkkkkkkkkk...", "................", "................",
    ],
    "heart": [
        "................", "..kkk....kkk....", ".krrrk..krrrk...", "krrwrrkkrrrrrk..",
        "krwrrrrrrrrrrk..", "krrrrrrrrrrrrk..", ".krrrrrrrrrrk...", "..krrrrrrrrk....",
        "...krrrrrrk.....", "....krrrrk......", ".....krrk.......", "......kk........",
        "................", "................", "................", "................",
    ],
}
for _n, _rows in ICONS.items():
    assert len(_rows) == 16 and all(len(r) == 16 for r in _rows), (_n, [len(r) for r in _rows])


def pixel_art(rows, palette=PAL) -> str:
    """Return <path> elements (one per colour) drawing rows of palette chars, 1 unit per pixel."""
    by = {}
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            if ch == "." or ch not in palette:
                x += 1
                continue
            x0 = x
            while x < len(row) and row[x] == ch:
                x += 1
            by.setdefault(palette[ch], []).append(f"M{x0} {y}h{x - x0}v1h-{x - x0}z")
    return "".join(f'<path d="{"".join(d)}" fill="{c}"/>' for c, d in by.items())


def icon(name: str, x: float, y: float, scale: float = 1, extra: str = "") -> str:
    return (f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges" {extra}>'
            f'{pixel_art(ICONS[name])}</g>')


AVATAR = [
    "bbbbbbbbbbbbbbbb", "bbbbbhhhhhhbbbbb", "bbbbhhhhhhhhbbbb", "bbbhhhhhhhhhhbbb",
    "bbbhhSSSSSSShbbb", "bbhhSSeeSSeeShbb", "bbhhSSSSSSSSSShb", "bbhhSSSSSSSSShhb",
    "bbhhSSSmmmSShhbb", "bbhhhSSSSSSShhbb", "bbhhhhSSSSShhhbb", "bbhhhccccccchhbb",
    "bbbhcccwwccchhbb", "bbbcccccccccccbb", "bbccccccccccccbb", "bbccccccccccccbb",
]


# --------------------------------------------------------------------------- svg document
def svg_doc(w, h, body, *, title, desc="", style="", defs="") -> str:
    style_block = f"<style>{style}{REDUCED_MOTION}</style>" if style else f"<style>{REDUCED_MOTION}</style>"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-labelledby="title desc">'
        f'<title id="title">{esc(title)}</title><desc id="desc">{esc(desc or title)}</desc>'
        f"{style_block}<defs>{defs}</defs>{body}</svg>"
    )


def grad_defs(t: dict, prefix: str = "") -> str:
    """Gradients every window needs (title bar, highlight)."""
    return (
        f'<linearGradient id="{prefix}tb" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["title_a"]}"/><stop offset="1" stop-color="{t["title_b"]}"/></linearGradient>'
        f'<linearGradient id="{prefix}tbhi" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#FFFFFF" stop-opacity=".38"/><stop offset=".45" stop-color="#FFFFFF" stop-opacity=".08"/>'
        f'<stop offset="1" stop-color="#000000" stop-opacity=".12"/></linearGradient>'
        f'<linearGradient id="{prefix}shine" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/><stop offset=".5" stop-color="#FFFFFF" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
    )


def title_buttons(x_right: float, y: float, size: float = 22) -> str:
    """Minimise / maximise / close buttons; x_right is the right edge."""
    out = []
    gap = 4
    xs = [x_right - 3 * size - 2 * gap, x_right - 2 * size - gap, x_right - size]
    for i, bx in enumerate(xs):
        close = i == 2
        fill = "#E0482C" if close else "#FFFFFF"
        fo = "1" if close else ".2"
        out.append(f'<rect x="{bx}" y="{y}" width="{size}" height="{size}" rx="4" fill="{fill}" fill-opacity="{fo}" '
                   f'stroke="#FFFFFF" stroke-opacity=".85" stroke-width="1.5"/>')
        u = size / 11
        gx, gy = bx + 3 * u, y + 3 * u
        if i == 0:
            out.append(f'<rect x="{gx}" y="{gy + 4 * u}" width="{5 * u}" height="{1.2 * u}" fill="#FFFFFF"/>')
        elif i == 1:
            out.append(f'<rect x="{gx}" y="{gy}" width="{5 * u}" height="{5 * u}" fill="none" stroke="#FFFFFF" stroke-width="{1.1 * u}"/>')
        else:
            pts = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (4, 0), (3, 1), (1, 3), (0, 4)]
            for (px, py) in pts:
                out.append(f'<rect x="{gx + px * u * 1.25:.2f}" y="{gy + py * u * 1.25:.2f}" width="{1.3 * u:.2f}" height="{1.3 * u:.2f}" fill="#FFFFFF"/>')
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def window(x, y, w, h, title, t, *, icon_name=None, title_h=34, body=None, prefix="", radius=9,
           shadow=6, subtitle="", shine=True, title_size=16) -> str:
    """Future-XP window chrome. Returns svg string. Body colour = theme paper unless body given."""
    body = body or t["paper"]
    parts = []
    if shadow:
        parts.append(f'<rect x="{x + shadow}" y="{y + shadow}" width="{w}" height="{h}" rx="{radius}" '
                     f'fill="{t["shadow"]}" fill-opacity="{t["shadow_op"]}"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{body}" '
                 f'stroke="{t["frame"]}" stroke-width="2"/>')
    # title bar: rounded top only
    r = radius
    tb = (f"M{x + 1} {y + title_h}V{y + r}Q{x + 1} {y + 1} {x + r} {y + 1}H{x + w - r}"
          f"Q{x + w - 1} {y + 1} {x + w - 1} {y + r}V{y + title_h}Z")
    parts.append(f'<path d="{tb}" fill="url(#{prefix}tb)"/><path d="{tb}" fill="url(#{prefix}tbhi)"/>')
    parts.append(f'<rect x="{x + 1}" y="{y + title_h}" width="{w - 2}" height="2" fill="{t["frame"]}" fill-opacity=".55"/>')
    tx = x + 12
    if icon_name:
        isz = (title_h - 12) / 16
        parts.append(icon(icon_name, x + 10, y + 6, isz))
        tx = x + 16 + 16 * isz
    parts.append(f'<text x="{tx + 1}" y="{y + title_h / 2 + title_size * 0.36 + 1}" font-family="{FONT_UI}" font-size="{title_size}" '
                 f'font-weight="700" fill="#000000" fill-opacity=".35">{esc(title)}</text>')
    parts.append(f'<text x="{tx}" y="{y + title_h / 2 + title_size * 0.36}" font-family="{FONT_UI}" font-size="{title_size}" '
                 f'font-weight="700" fill="#FFFFFF">{esc(title)}</text>')
    bsize = title_h - 12
    btn_right = x + w - 8
    if subtitle:
        parts.append(f'<text x="{btn_right - 3 * bsize - 8 - 14}" y="{y + title_h / 2 + 5}" text-anchor="end" font-family="{FONT_UI}" '
                     f'font-size="{title_size - 2}" fill="#FFFFFF" fill-opacity=".88">{esc(subtitle)}</text>')
    parts.append(title_buttons(btn_right, y + 6, bsize))
    if shine:
        cid = f"{prefix}tbclip{int(x)}{int(y)}"
        parts.append(f'<clipPath id="{cid}"><path d="{tb}"/></clipPath>'
                     f'<g clip-path="url(#{cid})"><rect class="tbshine" x="{x - 160}" y="{y}" width="120" height="{title_h}" '
                     f'fill="url(#{prefix}shine)" transform="skewX(-20)"/></g>')
    return "".join(parts)


TB_SHINE_CSS = (".tbshine{animation:tbshine 9s ease-in-out infinite}"
                "@keyframes tbshine{0%,70%{transform:translateX(0) skewX(-20deg)}100%{transform:translateX(1700px) skewX(-20deg)}}")


# --------------------------------------------------------------------------- pixel badge generator
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def shape_mask(tier: int, x: int, y: int) -> bool:
    cx = cy = 11.5
    dx, dy = x - cx, y - cy
    if tier == 1:
        return dx * dx + dy * dy <= 11.4 * 11.4
    if tier == 2:
        if y < 1:
            return False
        hw = (9.6 if y == 1 else 10.6) if y <= 10 else 10.6 * (1 - math.pow((y - 10) / 13.2, 1.8))
        return abs(dx) <= hw
    r = math.hypot(dx, dy)
    a = math.atan2(dy, dx)
    return r <= 10.4 + 1.2 * math.cos(8 * a + math.pi / 8)


def _mix(c1: str, c2: str, k: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] * (1 - k) + b[i] * k):02X}" for i in range(3))


def _desaturate(c: str, k: float = .75) -> str:
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    lum = round(.3 * r + .59 * g + .11 * b)
    gray = f"#{lum:02X}{lum:02X}{lum:02X}"
    return _mix(c, gray, k)


def badge_art(tier: int, track: str, code: str, legacy: bool = False):
    """Return (inner svg markup in a 24x24 space, clip path data of the shape)."""
    t = dict(TRACKS[track])
    if legacy:
        t = {k: (_desaturate(v) if isinstance(v, str) and v.startswith("#") else v) for k, v in t.items()}
    N = 24
    grid = [[shape_mask(tier, x, y) for x in range(N)] for y in range(N)]

    def inside(x, y):
        return 0 <= x < N and 0 <= y < N and grid[y][x]

    rects, mask = [], []
    for y in range(N):
        run = None
        mrun = None
        for x in range(N + 1):
            c = None
            if x < N and grid[y][x]:
                edge = not inside(x - 1, y) or not inside(x + 1, y) or not inside(x, y - 1) or not inside(x, y + 1)
                inner = (not edge) and (not inside(x - 2, y) or not inside(x + 2, y) or not inside(x, y - 2) or not inside(x, y + 2))
                if edge:
                    c = t["dark"]
                elif inner and (x + y) < 20:
                    c = "#FFFFFF"
                elif inner and tier != 3:
                    c = t["dark"]
                elif inner:
                    c = t["base"]
                else:
                    g = ((y - 3) / (N - 8)) * 17
                    c = t["base"] if g > BAYER[y % 4][x % 4] else t["light"]
                if (not edge) and c != "#FFFFFF" and 4 < x < 8 and 4 < y < 7 and tier != 3:
                    c = "#FFFFFF"
            if run and run[2] == c:
                run[1] += 1
            else:
                if run and run[2]:
                    rects.append(f'<rect x="{run[0]}" y="{y}" width="{run[1]}" height="1" fill="{run[2]}"/>')
                run = [x, 1, c]
            on = x < N and grid[y][x]
            if on and mrun is None:
                mrun = x
            if not on and mrun is not None:
                mask.append(f"M{mrun} {y}h{x - mrun}v1h-{x - mrun}z")
                mrun = None
    if tier == 3:
        ribbon = (f'<rect x="1" y="14" width="22" height="5" fill="{t["dark"]}"/><rect x="0" y="15" width="1" height="3" fill="{t["dark"]}"/>'
                  f'<rect x="23" y="15" width="1" height="3" fill="{t["dark"]}"/><rect x="1" y="14" width="22" height="1" fill="#FFFFFF" fill-opacity=".35"/>')
        ty = 17.9
    else:
        ribbon = (f'<rect x="0" y="13" width="24" height="5" fill="{t["dark"]}"/>'
                  f'<rect x="0" y="13" width="24" height="1" fill="#FFFFFF" fill-opacity=".35"/>')
        ty = 16.9
    label = code if len(code) <= 6 else code[:3]
    fs = 3.6 if len(label) > 5 else 4
    text = (f'<text x="12" y="{ty}" text-anchor="middle" font-family="{FONT_MONO}" font-weight="800" '
            f'font-size="{fs}" fill="#FFFFFF" shape-rendering="geometricPrecision">{esc(label)}</text>')
    return "".join(rects) + ribbon + text, "".join(mask)


# --------------------------------------------------------------------------- cat sprites
CAT_FRAMES, CAT_W, CAT_H, CAT_CYCLE = 6, 80, 68, 0.66
_CATS = None


def _cats():
    global _CATS
    if _CATS is None:
        with open(os.path.join(HERE, "sprites", "cats.json"), encoding="utf-8") as f:
            _CATS = json.load(f)
    return _CATS


def cat_frames(name_png: str) -> str:
    """The 6 running frames of a cat as vector pixels; CSS shows one frame at a time."""
    data = _cats()[name_png]
    out = []
    for k, fr in enumerate(data["frames"]):
        delay = -((CAT_FRAMES - k) % CAT_FRAMES) * CAT_CYCLE / CAT_FRAMES
        paths = "".join(f'<path d="{d}" fill="{c}"/>' for c, d in fr.items())
        out.append(f'<g class="cf" opacity="{1 if k == 0 else 0}" style="animation-delay:{delay:.3f}s">{paths}</g>')
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def cat(name_png: str, x: float, y: float, cls: str, delay: float, scale: float = 1, uid: str = "", base_x: float = 0) -> str:
    """A running cat: the outer group walks across (CSS), the frames flip in place (CSS).
    base_x is the resting position used when animations are off (prefers-reduced-motion)."""
    return (f'<g transform="translate({x} {y}) scale({scale})"><g class="{cls}" transform="translate({base_x} 0)" '
            f'style="animation-delay:{delay}s">{cat_frames(name_png)}</g></g>')


CAT_CSS = (".cf{animation:cf .66s steps(1,end) infinite}"
           "@keyframes cf{0%{opacity:1}16.667%,100%{opacity:0}}")


# --------------------------------------------------------------------------- misc helpers
def wrap(text: str, max_chars: int):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        if len(cur) + len(w_) + (1 if cur else 0) <= max_chars:
            cur = f"{cur} {w_}".strip()
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_w(s: str, size: float, bold: bool = False) -> float:
    """Rough width estimate for Tahoma/Segoe-like UI fonts (used only for layout padding)."""
    narrow = set("iljtfr.,:;'!|() ")
    wide = set("mwMW@%&")
    w_ = 0.0
    for ch in s:
        if ch in narrow:
            w_ += .32
        elif ch in wide:
            w_ += .86
        elif ch.isupper() or ch.isdigit():
            w_ += .64
        else:
            w_ += .55
    return w_ * size * (1.2 if bold else 1.08)
