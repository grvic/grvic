#!/usr/bin/env python3
"""Build the grvic profile: every SVG in assets/ + README.md, from data/profile.json.

Usage:
    python tools/build.py               # rebuild assets and README
    python tools/build.py --readme-only # only README (used by the guestbook workflow)

Standard library only. Edit data/profile.json (or data/guestbook.json), never README.md by hand.
"""
from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelkit import (AVATAR, CAT_CSS, FONT_MONO, FONT_UI, ICONS, PAL, TB_SHINE_CSS, THEMES, TRACKS,  # noqa: E402
                      _mix, badge_art, cat, cat_frames, esc, grad_defs, icon, pixel_art, ptext, ptext_path, ptext_width,
                      svg_doc, text_w, title_buttons, window, wrap)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
LANG_COLORS = {"Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "PowerShell": "#012456",
               "Java": "#B07219", "Kotlin": "#A97BFF", "HTML": "#E34C26", "CSS": "#663399"}


def load(path, default=None):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(rel, content):
    p = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def counts(P):
    shown = [c for c in P["certs"] if c.get("show", True)]
    return {"certs": len(shown), "issuers": len({c["issuer"] for c in shown}), "talks": len(P.get("talks", []))}


def fmt(s, P):
    return s.format(**counts(P))


def slug(code):
    return code.lower()


# =========================================================================== landscape pieces
def dither_pattern(pid, a, b):
    return (f'<pattern id="{pid}" width="8" height="8" patternUnits="userSpaceOnUse">'
            f'<rect width="8" height="8" fill="{a}"/><rect width="4" height="4" fill="{b}"/>'
            f'<rect x="4" y="4" width="4" height="4" fill="{b}"/></pattern>')


def sky(t, W, H, bands=(150, 250), prefix=""):
    s0, s1, s2 = t["sky"]
    defs = dither_pattern(f"{prefix}d01", s0, s1) + dither_pattern(f"{prefix}d12", s1, s2)
    b0, b1 = bands
    body = (f'<rect width="{W}" height="{H}" fill="{s2}"/><rect width="{W}" height="{b1}" fill="{s1}"/>'
            f'<rect width="{W}" height="{b0}" fill="{s0}"/>'
            f'<rect y="{b0 - 4}" width="{W}" height="8" fill="url(#{prefix}d01)"/>'
            f'<rect y="{b1 - 4}" width="{W}" height="8" fill="url(#{prefix}d12)"/>')
    return defs, body


def cloud(x, y, w, fill, op=1):
    u = w / 12
    rects = [(0, 2, 12, 2), (1, 1, 9, 1), (2, 0, 4, 1), (7, 0.4, 3, 1), (11, 3, 2, 1), (-1, 3, 2, 1)]
    return "".join(f'<rect x="{x + a * u:.1f}" y="{y + b * u:.1f}" width="{c * u:.1f}" height="{d * u:.1f}" fill="{fill}" fill-opacity="{op}"/>'
                   for a, b, c, d in rects)


def cloud_layer(t, W, ys, widths, fill, op, cls, seed):
    rnd = random.Random(seed)
    one = "".join(cloud(rnd.randint(0, W - 200) + i * 0, ys[i % len(ys)], widths[i % len(widths)], fill, op)
                  for i in range(len(ys)))
    return f'<g class="{cls}" shape-rendering="crispEdges">{one}<g transform="translate({W} 0)">{one}</g></g>'


def hill(W, H, y_base, amp, step, seed, fill):
    rnd = random.Random(seed)
    d = [f"M0 {H}V{y_base}"]
    x = 0
    while x < W:
        x += rnd.choice([step, step * 2, step * 3])
        y = y_base + rnd.randint(-amp, amp) // 4 * 4
        d.append(f"H{min(x, W)}V{y}")
    d.append(f"H{W}V{H}Z")
    return f'<path d="{"".join(d)}" fill="{fill}"/>'


def hills(t, W, H, top, seed=3):
    h0, h1, h2 = t["hill"]
    rnd = random.Random(seed)
    out = [hill(W, H, top, 16, 40, seed, h0), hill(W, H, top + 34, 14, 48, seed + 1, h1), hill(W, H, top + 74, 10, 56, seed + 2, h2)]
    for _ in range(9):
        out.append(f'<rect x="{rnd.randint(0, W - 120)}" y="{rnd.randint(top + 44, top + 66) // 4 * 4}" width="{rnd.randint(50, 120) // 4 * 4}" height="8" fill="{t["hill_hi"]}"/>')
    for _ in range(7):
        out.append(f'<rect x="{rnd.randint(0, W - 160)}" y="{rnd.randint(top + 84, H - 12) // 4 * 4}" width="{rnd.randint(70, 160) // 4 * 4}" height="8" fill="{t["hill_lo"]}"/>')
    # pixel flowers
    for _ in range(18):
        fx, fy = rnd.randint(10, W - 10) // 4 * 4, rnd.randint(top + 40, H - 8) // 4 * 4
        col = rnd.choice(["#FFD23F", "#FF8AC4", "#FFFFFF", "#C7B6FF"])
        out.append(f'<rect x="{fx}" y="{fy}" width="4" height="4" fill="{col}"/>'
                   f'<rect x="{fx}" y="{fy + 4}" width="4" height="4" fill="{t["hill_lo"]}"/>')
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def pixel_disc(cx, cy, r, fill, unit=4):
    out = []
    for yy in range(-r, r + 1, unit):
        half = int(((r * r - yy * yy) ** .5) // unit * unit)
        if half > 0:
            out.append(f'<rect x="{cx - half}" y="{cy + yy}" width="{2 * half}" height="{unit}" fill="{fill}"/>')
    return "".join(out)


def sun_or_moon(t, cx, cy):
    if t["name"] == "light":
        return (f'<g shape-rendering="crispEdges"><g class="halo">{pixel_disc(cx, cy, 52, "#FFF3B0")}</g>'
                f'{pixel_disc(cx, cy, 36, "#FFD23F")}{pixel_disc(cx - 8, cy - 8, 16, "#FFE680")}</g>')
    return (f'<g shape-rendering="crispEdges"><g class="halo">{pixel_disc(cx, cy, 48, "#22305C")}</g>'
            f'{pixel_disc(cx, cy, 32, "#F2EFD9")}{pixel_disc(cx + 14, cy - 10, 26, t["sky"][0])}</g>')


def stars(W, top, bottom, n, seed, color="#F2EFD9"):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x, y = rnd.randint(0, W) // 2 * 2, rnd.randint(top, bottom) // 2 * 2
        s = rnd.choice([2, 2, 3, 4])
        out.append(f'<rect class="tw" style="animation-delay:{-rnd.random() * 4:.2f}s" x="{x}" y="{y}" width="{s}" height="{s}" fill="{color}"/>')
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def pollen(t, W, top, bottom, n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.randint(20, W - 20), rnd.randint(top, bottom)
        out.append(f'<g transform="translate({x} {y})"><rect class="pollen" style="animation-delay:{-rnd.random() * 8:.2f}s;animation-duration:{6 + rnd.random() * 5:.1f}s" '
                   f'width="4" height="4" fill="{t["sparkle"]}"/></g>')
    return "".join(out)


LAND_CSS = (".drift-a{animation:drift 140s linear infinite}.drift-b{animation:drift 80s linear infinite}"
            "@keyframes drift{to{transform:translateX(-1280px)}}"
            ".halo{animation:halo 4s steps(2) infinite}@keyframes halo{50%{opacity:.35}}"
            ".tw{animation:tw 3.2s steps(2) infinite}@keyframes tw{50%{opacity:.15}}"
            ".pollen{animation:pollen 8s linear infinite}"
            "@keyframes pollen{0%{transform:translate(0,0);opacity:0}15%{opacity:1}85%{opacity:1}100%{transform:translate(18px,-70px);opacity:0}}")


# =========================================================================== typing effect
def typing(phrases, x, y, char_w, fs, fill, bg, caret, slot=6.0, prefix="ty"):
    n_ph = len(phrases)
    T = n_ph * slot
    max_w = max(len(p) for p in phrases) * char_w
    css, els = [f".{prefix}caret{{animation:{prefix}blink 1s steps(1,end) infinite}}@keyframes {prefix}blink{{50%{{opacity:0}}}}"], []

    def pc(sec):
        return f"{max(0.0, min(100.0, sec / T * 100)):.3f}%"

    for i, ph in enumerate(phrases):
        n = len(ph)
        W = n * char_w
        st = i * slot
        te = st + min(2.4, 0.055 * n + 0.5)
        ds, de = st + slot - 1.1, st + slot - 0.3
        if n_ph > 1:
            if i == 0:
                css.append(f"@keyframes {prefix}v{i}{{0%,{pc(st + slot - 0.02)}{{opacity:1}}{pc(st + slot)},100%{{opacity:0}}}}")
            else:
                css.append(f"@keyframes {prefix}v{i}{{0%,{pc(st - 0.02)}{{opacity:0}}{pc(st)},{pc(st + slot - 0.02)}{{opacity:1}}{pc(st + slot)},100%{{opacity:0}}}}")
        css.append(f"@keyframes {prefix}c{i}{{0%,{pc(st)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
                   f"{pc(te)},{pc(ds)}{{transform:translateX({W}px);animation-timing-function:steps({n},end)}}"
                   f"{pc(de)},100%{{transform:translateX(0)}}}}")
        vis = f' style="animation:{prefix}v{i} {T}s linear infinite"' if n_ph > 1 else ""
        els.append(
            f'<g opacity="{1 if i == 0 else 0}"{vis}>'
            f'<text x="{x}" y="{y}" font-family="{FONT_MONO}" font-size="{fs}" fill="{fill}" textLength="{W}" lengthAdjust="spacingAndGlyphs">{esc(ph)}</text>'
            f'<g transform="translate({W} 0)" style="animation:{prefix}c{i} {T}s linear infinite">'
            f'<rect x="{x}" y="{y - fs * 1.05}" width="{max_w + char_w * 2}" height="{fs * 1.5}" fill="{bg}"/>'
            f'<rect class="{prefix}caret" x="{x + 2}" y="{y - fs * .9}" width="{char_w * .75}" height="{fs * 1.12}" fill="{caret}"/></g></g>')
    clip = (f'<clipPath id="{prefix}clip"><rect x="{x - 2}" y="{y - fs * 1.1}" width="{max_w + char_w * 1.6}" height="{fs * 1.6}"/></clipPath>')
    return clip + f'<g clip-path="url(#{prefix}clip)">{"".join(els)}</g>', "".join(css)


# =========================================================================== header
def header(t, P):
    W, H = 1280, 420
    prefix = t["name"][0]
    sky_defs, sky_body = sky(t, W, H, prefix=prefix)
    defs = [grad_defs(t), sky_defs]
    body = [sky_body]
    if t["name"] == "dark":
        body.append(stars(W, 6, 240, 46, 11))
    body.append(sun_or_moon(t, 1186, 70))
    body.append(cloud_layer(t, W, [44, 92, 64, 118], [150, 110, 190, 120], t["cloud_back"], .9, "drift-a", 5))
    body.append(cloud_layer(t, W, [150, 200, 176], [170, 130, 210], t["cloud_front"], .95 if t["name"] == "light" else .7, "drift-b", 9))
    body.append(hills(t, W, H, 318, seed=4))
    body.append(pollen(t, W, 120, 330, 16, 21))

    # desktop icons + cycling selection
    icons = [("doc", "cv.pdf"), ("medal", "achievements.exe"), ("folder", "projects/"), ("mic", "talks/")]
    sel = (f'<g class="sel"><rect x="14" y="22" width="104" height="80" rx="4" fill="#1F5FD6" fill-opacity=".35" '
           f'stroke="#FFFFFF" stroke-opacity=".7" stroke-dasharray="2 2"/></g>')
    body.append(sel)
    for i, (ic, label) in enumerate(icons):
        y = 28 + i * 84
        body.append(icon(ic, 42, y, 3))
        lx, ly = 66, y + 66
        body.append(f'<text x="{lx + 1}" y="{ly + 1}" text-anchor="middle" font-family="{FONT_UI}" font-size="13" fill="#000" fill-opacity=".6">{esc(label)}</text>'
                    f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="{FONT_UI}" font-size="13" fill="#FFFFFF">{esc(label)}</text>')

    # main window
    wx, wy, ww, wh = 150, 28, 800, 300
    body.append(window(wx, wy, ww, wh, "victoria.exe — Future-XP Research Desktop", t, icon_name="computer"))
    bx = wx + 28
    body.append(f'<text x="{bx}" y="{wy + 72}" font-family="{FONT_MONO}" font-size="16" fill="{t["accent"]}">&gt; hello world, I&apos;m</text>')
    name = P["name"].upper()
    sc = 6
    ny = wy + 88
    body.append(ptext(name, bx + 5, ny + 5, sc, t["name_shadow"], f'fill-opacity="{".3" if t["name"] == "light" else ".9"}"'))
    body.append(ptext(name, bx, ny, sc, "url(#namegrad)"))
    if t["name"] == "light":
        stops = ("#1F5FD6", "#7B5CFF", "#12A38A")
    else:
        stops = ("#7CC0FF", "#C7B6FF", "#8FF0D4")
    defs.append(f'<linearGradient id="namegrad" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect">'
                f'<stop offset="0" stop-color="{stops[0]}"/><stop offset=".5" stop-color="{stops[1]}"/><stop offset="1" stop-color="{stops[2]}"/>'
                f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;1 0;0 0" dur="12s" repeatCount="indefinite"/></linearGradient>')
    # typing line
    ty_y = wy + 184
    body.append(f'<text x="{bx}" y="{ty_y}" font-family="{FONT_MONO}" font-size="20" font-weight="700" fill="{t["accent2"]}">&gt;</text>')
    ty_svg, ty_css = typing(P["typing"], bx + 24, ty_y, 12, 20, t["ink"], t["paper"], t["accent2"])
    body.append(ty_svg)
    # chips
    cx, cy = bx, wy + 212
    for ch in P["chips"]:
        txt = fmt(ch["text"], P)
        tr = TRACKS[ch["track"]]
        w_ = text_w(txt, 14, True) + 34
        body.append(f'<g><rect x="{cx + 3}" y="{cy + 3}" width="{w_}" height="30" rx="7" fill="{t["shadow"]}" fill-opacity="{t["shadow_op"]}"/>'
                    f'<rect x="{cx}" y="{cy}" width="{w_}" height="30" rx="7" fill="{tr["light"]}" stroke="#0E1726" stroke-width="2"/>'
                    f'<rect x="{cx + 10}" y="{cy + 11}" width="8" height="8" fill="{tr["base"]}" shape-rendering="crispEdges"/>'
                    f'<text x="{cx + 24}" y="{cy + 20}" font-family="{FONT_UI}" font-size="14" font-weight="700" fill="#0E1726">{esc(txt)}</text></g>')
        cx += w_ + 10
    # avatar
    ax, ay = wx + ww - 28 - 124, wy + 52
    body.append(f'<rect x="{ax + 4}" y="{ay + 4}" width="124" height="124" rx="6" fill="{t["shadow"]}" fill-opacity="{t["shadow_op"]}"/>'
                f'<rect x="{ax}" y="{ay}" width="124" height="124" rx="6" fill="#DCEEFF" stroke="#0E1726" stroke-width="2"/>')
    body.append(f'<g transform="translate({ax + 6} {ay + 6}) scale(7)" shape-rendering="crispEdges"><g class="bob">{pixel_art(AVATAR)}'
                f'<g class="blink"><rect x="6" y="5" width="2" height="1" fill="#F2C6A0"/><rect x="10" y="5" width="2" height="1" fill="#F2C6A0"/></g></g></g>')
    # status bar
    sy = wy + wh - 30
    body.append(f'<rect x="{wx + 2}" y="{sy}" width="{ww - 4}" height="28" fill="{t["paper2"]}"/>'
                f'<rect x="{wx + 2}" y="{sy}" width="{ww - 4}" height="1.5" fill="{t["ink3"]}"/>')
    body.append(f'<rect class="online" x="{wx + 16}" y="{sy + 9}" width="10" height="10" fill="#2F9E44" shape-rendering="crispEdges"/>')
    sb = [("Ready · online", wx + 34, "start"), ("Cloud · Data · AI · Agents", wx + ww / 2, "middle"),
          (" · ".join(c["name"] for c in P["cats"]) + " ♥", wx + ww - 16, "end")]
    for txt, x_, anchor in sb:
        body.append(f'<text x="{x_}" y="{sy + 19}" text-anchor="{anchor}" font-family="{FONT_UI}" font-size="13" fill="{t["ink2"]}">{esc(txt)}</text>')

    # mini achievements window
    mx, my, mw, mh = 980, 140, 272, 188
    body.append(window(mx, my, mw, mh, "achievements.exe", t, icon_name="medal", title_h=30, title_size=14, prefix=""))
    picks = [c for c in P["certs"] if c.get("show", True)]
    picks = [next(c for c in picks if c["tier"] == 3)] + [c for c in picks if c["tier"] == 2][:1] + [c for c in picks if c["tier"] == 1][-3:-2]
    for i, c in enumerate(picks[:3]):
        art, mask = badge_art(c["tier"], c["track"], c["code"], c.get("legacy", False))
        gx, gy = mx + 18 + i * 84, my + 46
        defs.append(f'<clipPath id="mb{i}"><path d="{mask}"/></clipPath>')
        body.append(f'<g transform="translate({gx} {gy}) scale(2.75)" shape-rendering="crispEdges"><g class="float" style="animation-delay:{-i * .7}s">{art}'
                    f'<g clip-path="url(#mb{i})"><rect class="bshine" style="animation-delay:{i * .6}s" x="-10" y="-4" width="5" height="32" fill="#FFFFFF" fill-opacity=".65" transform="skewX(-20)"/></g></g></g>')
        body.append(f'<text x="{gx + 33}" y="{my + 138}" text-anchor="middle" font-family="{FONT_MONO}" font-size="12" font-weight="700" fill="{t["ink"]}">{esc(c["code"])}</text>')
    body.append(f'<text x="{mx + mw / 2}" y="{my + mh - 16}" text-anchor="middle" font-family="{FONT_UI}" font-size="13" font-weight="700" fill="{t["accent"]}">'
                f'{counts(P)["certs"]} unlocked ▸</text>')

    # cats running on the grass
    for i, c in enumerate(P["cats"]):
        body.append(cat(c["sprite"], 0, 344, "walk", -i * 6.4, uid=f"h{i}", base_x=1080 - i * 110))

    css = (LAND_CSS + TB_SHINE_CSS + CAT_CSS + ty_css +
           ".walk{animation:walk 19.2s linear infinite}@keyframes walk{from{transform:translateX(1300px)}to{transform:translateX(-100px)}}"
           ".sel{animation:sel 10s steps(1,end) infinite}@keyframes sel{0%{transform:translateY(0)}25%{transform:translateY(84px)}50%{transform:translateY(168px)}75%{transform:translateY(252px)}}"
           ".bob{animation:bob 2.4s steps(1,end) infinite}@keyframes bob{50%{transform:translateY(-1px)}}"
           ".blink{opacity:0;animation:blinkeye 4.5s steps(1,end) infinite}@keyframes blinkeye{0%,93%{opacity:0}94%,97%{opacity:1}98%{opacity:0}}"
           ".online{animation:online 1.6s steps(1,end) infinite}@keyframes online{50%{opacity:.25}}"
           ".float{animation:float 2.6s steps(1,end) infinite}@keyframes float{50%{transform:translateY(-1px)}}"
           ".bshine{animation:bshine 4.5s ease-in infinite}@keyframes bshine{0%,70%{transform:translateX(0) skewX(-20deg)}100%{transform:translateX(44px) skewX(-20deg)}}")
    return svg_doc(W, H, "".join(body), defs="".join(defs), style=css,
                   title=f"{P['name']} — {P['role']} at {P['company']}",
                   desc="Pixel-art desktop: a retro window introduces Victoria Faranna with a typing tagline, a mini achievements window with pixel badges, "
                        "and her three cats Coco, Nemo and Tofu running across a green hill.")


# =========================================================================== footer
def footer(t, P):
    W, H = 1280, 210
    defs = [grad_defs(t)]
    body = []
    # hills on transparent background
    h0, h1, h2 = t["hill"]
    body.append(f'<g shape-rendering="crispEdges">{hill(W, H, 92, 12, 48, 31, h0)}{hill(W, H, 118, 10, 56, 32, h1)}</g>')
    rnd = random.Random(5)
    flowers = []
    for _ in range(26):
        fx, fy = rnd.randint(10, W - 10) // 4 * 4, rnd.randint(132, 156) // 4 * 4
        col = rnd.choice(["#FFD23F", "#FF8AC4", "#FFFFFF", "#C7B6FF"])
        flowers.append(f'<rect x="{fx}" y="{fy}" width="4" height="4" fill="{col}"/>')
    body.append(f'<g shape-rendering="crispEdges">{"".join(flowers)}</g>')
    body.append(pollen(t, W, 70, 150, 10, 77))
    # pixel thank-you text
    msg = "THANKS FOR VISITING!"
    sc = 4
    tw_ = ptext_width(msg, sc)
    body.append(ptext(msg, (W - tw_) / 2 + 3, 26 + 3, sc, t["name_shadow"], 'fill-opacity=".3"'))
    body.append(ptext(msg, (W - tw_) / 2, 26, sc, t["accent"]))
    body.append(f'<text x="{W / 2}" y="78" text-anchor="middle" font-family="{FONT_MONO}" font-size="14" fill="{t["ink2"]}">'
                f'{esc(P["tagline"])}</text>')
    for i, c in enumerate(P["cats"]):
        body.append(cat(c["sprite"], 0, 96, "walk", -i * 6.4, uid=f"f{i}", base_x=180 + i * 110))
    # taskbar
    ty = H - 46
    tb = t["taskbar"]
    defs.append(f'<linearGradient id="task" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{tb[0]}"/>'
                f'<stop offset=".12" stop-color="{tb[1]}"/><stop offset="1" stop-color="{tb[2]}"/></linearGradient>'
                f'<linearGradient id="startg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["start"][0]}"/>'
                f'<stop offset="1" stop-color="{t["start"][1]}"/></linearGradient>')
    body.append(f'<rect x="0" y="{ty}" width="{W}" height="46" fill="url(#task)"/><rect x="0" y="{ty}" width="{W}" height="2" fill="#FFFFFF" fill-opacity=".35"/>')
    body.append(f'<path d="M0 {ty}H112Q132 {ty} 132 {ty + 23}Q132 {ty + 46} 112 {ty + 46}H0Z" fill="url(#startg)"/>'
                f'<path d="M0 {ty}H112Q132 {ty} 132 {ty + 23}" fill="none" stroke="#FFFFFF" stroke-opacity=".4" stroke-width="2"/>')
    body.append(icon("star", 12, ty + 9, 1.75))
    body.append(f'<text x="45" y="{ty + 30}" font-family="{FONT_UI}" font-size="20" font-weight="700" font-style="italic" fill="#000" fill-opacity=".3">start</text>'
                f'<text x="44" y="{ty + 29}" font-family="{FONT_UI}" font-size="20" font-weight="700" font-style="italic" fill="#FFFFFF">start</text>')
    tasks = [("computer", "victoria.exe", True), ("medal", "achievements.exe", False), ("pen", "guestbook.exe", False)]
    x = 150
    for ic, label, active in tasks:
        fill_op = ".28" if active else ".12"
        body.append(f'<rect x="{x}" y="{ty + 7}" width="190" height="32" rx="4" fill="#FFFFFF" fill-opacity="{fill_op}" stroke="#FFFFFF" stroke-opacity=".35"/>')
        body.append(icon(ic, x + 8, ty + 12, 1.4))
        body.append(f'<text x="{x + 38}" y="{ty + 28}" font-family="{FONT_UI}" font-size="14" fill="#FFFFFF">{esc(label)}</text>')
        x += 198
    trx = W - 250
    body.append(f'<rect x="{trx}" y="{ty + 2}" width="250" height="44" fill="{t["tray"]}"/><rect x="{trx}" y="{ty + 2}" width="2" height="44" fill="#000" fill-opacity=".25"/>')
    body.append(icon("globe", trx + 14, ty + 13, 1.25) + f'<g class="online">{icon("heart", trx + 42, ty + 14, 1.25)}</g>')
    body.append(f'<text x="{W - 16}" y="{ty + 29}" text-anchor="end" font-family="{FONT_UI}" font-size="14" fill="#FFFFFF">EN · ES  |  Madrid</text>')
    css = (LAND_CSS + CAT_CSS +
           ".walk{animation:walk 19.2s linear infinite}@keyframes walk{from{transform:translateX(1300px)}to{transform:translateX(-100px)}}"
           ".online{animation:online 1.6s steps(1,end) infinite}@keyframes online{50%{opacity:.35}}")
    return svg_doc(W, H, "".join(body), defs="".join(defs), style=css, title="Thanks for visiting!",
                   desc="Retro taskbar footer with a start button, open windows and three pixel cats running over a hill.")


# =========================================================================== section title bar
def bar(title, subtitle, icon_name):
    t = THEMES["light"]
    W, H = 1280, 50
    defs = grad_defs(t)
    r = 10
    tb = f"M1 {H - 2}V{r}Q1 1 {r} 1H{W - r}Q{W - 1} 1 {W - 1} {r}V{H - 2}Z"
    body = [f'<path d="{tb}" fill="url(#tb)" stroke="{t["frame"]}" stroke-width="2"/><path d="{tb}" fill="url(#tbhi)"/>',
            f'<rect x="0" y="{H - 3}" width="{W}" height="3" fill="{t["frame"]}"/>',
            icon(icon_name, 14, 9, 2),
            f'<text x="57" y="{H / 2 + 8}" font-family="{FONT_UI}" font-size="21" font-weight="700" fill="#000" fill-opacity=".35">{esc(title)}</text>',
            f'<text x="56" y="{H / 2 + 7}" font-family="{FONT_UI}" font-size="21" font-weight="700" fill="#FFFFFF">{esc(title)}</text>',
            f'<text x="{W - 128}" y="{H / 2 + 6}" text-anchor="end" font-family="{FONT_UI}" font-size="16" fill="#FFFFFF" fill-opacity=".9">{esc(subtitle)}</text>',
            title_buttons(W - 12, 11, 26),
            f'<clipPath id="bc"><path d="{tb}"/></clipPath><g clip-path="url(#bc)"><rect class="tbshine" x="-160" y="0" width="120" height="{H}" fill="url(#shine)" transform="skewX(-20)"/></g>']
    return svg_doc(W, H, "".join(body), defs=defs, style=TB_SHINE_CSS, title=title, desc=f"{title} — {subtitle}")


# =========================================================================== nav button
def nav_button(label, icon_name):
    tw_ = text_w(label, 17, True)
    W, H = int(14 + 26 + 10 + tw_ + 18), 46
    defs = ('<linearGradient id="btn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/>'
            '<stop offset=".85" stop-color="#ECE9D8"/><stop offset="1" stop-color="#D6D0BC"/></linearGradient>')
    body = (f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="7" fill="url(#btn)" stroke="#003C74" stroke-width="2"/>'
            f'<rect class="glow" x="3" y="3" width="{W - 6}" height="{H - 6}" rx="5" fill="none" stroke="#FFD23F" stroke-width="2"/>'
            + icon(icon_name, 14, 10, 1.6) +
            f'<text x="50" y="{H / 2 + 6}" font-family="{FONT_UI}" font-size="17" font-weight="700" fill="#0E1726">{esc(label)}</text>')
    css = ".glow{opacity:0;animation:glow 5s steps(1,end) infinite}@keyframes glow{0%,80%{opacity:0}81%,100%{opacity:.9}}"
    return svg_doc(W, H, body, defs=defs, style=css, title=label)


# =========================================================================== terminal (about)
def terminal(P):
    t = dict(THEMES["dark"])
    t["paper"] = "#0B0F1A"
    W = 1280
    lines = P["terminal"]
    lh, top = 28, 92
    H = top + lh * (len(lines) * 2 + 1) + 12
    body = [window(8, 8, W - 22, H - 22, "C:\\WINDOWS\\system32\\cmd.exe — whoami", t, icon_name="computer", body="#0B0F1A", shadow=6)]
    prompt = "C:\\Users\\grvic>"
    cw, fs = 10.2, 17
    T = 22.0
    css = []

    def pc(sec):
        return f"{sec / T * 100:.3f}%"

    tcur = 0.6
    x0 = 36
    y = top
    for i, ln in enumerate(lines):
        cmd = ln["cmd"]
        out = fmt(ln["out"], P)
        n = len(cmd)
        pw = len(prompt) * cw
        cwid = n * cw
        st, te = tcur, tcur + 0.35 + n * 0.07
        to = te + 0.35
        css.append(f"@keyframes tp{i}{{0%,{pc(st)}{{opacity:0}}{pc(st + .01)},97%{{opacity:1}}100%{{opacity:0}}}}")
        css.append(f"@keyframes tc{i}{{0%,{pc(st + .2)}{{transform:translateX(0);animation-timing-function:steps({n},end)}}{pc(te)},100%{{transform:translateX({cwid}px)}}}}")
        css.append(f"@keyframes to{i}{{0%,{pc(to)}{{opacity:0}}{pc(to + .01)},97%{{opacity:1}}100%{{opacity:0}}}}")
        css.append(f"@keyframes tk{i}{{0%,{pc(st)}{{opacity:0}}{pc(st + .01)},{pc(to)}{{opacity:1}}{pc(to + .01)},100%{{opacity:0}}}}")
        body.append(f'<g style="animation:tp{i} {T}s linear infinite">'
                    f'<text x="{x0}" y="{y}" font-family="{FONT_MONO}" font-size="{fs}" fill="#39D0B6" textLength="{pw}" lengthAdjust="spacingAndGlyphs">{esc(prompt)}</text>'
                    f'<clipPath id="tclip{i}"><rect x="{x0 + pw + cw - 2}" y="{y - 20}" width="{cwid + cw * 2}" height="28"/></clipPath>'
                    f'<g clip-path="url(#tclip{i})"><text x="{x0 + pw + cw}" y="{y}" font-family="{FONT_MONO}" font-size="{fs}" fill="#F2EFD9" textLength="{cwid}" lengthAdjust="spacingAndGlyphs">{esc(cmd)}</text>'
                    f'<g transform="translate({cwid} 0)" style="animation:tc{i} {T}s linear infinite"><rect x="{x0 + pw + cw}" y="{y - 19}" width="{cwid + cw * 2}" height="26" fill="#0B0F1A"/>'
                    f'<rect opacity="0" style="animation:tk{i} {T}s linear infinite" x="{x0 + pw + cw + 1}" y="{y - 15}" width="{cw * .8}" height="19" fill="#F2EFD9" fill-opacity=".85"/></g></g></g>')
        y += lh
        color = "#FFD23F" if ln.get("highlight") else "#C5CCDA"
        body.append(f'<text style="animation:to{i} {T}s linear infinite" x="{x0 + 20}" y="{y}" font-family="{FONT_MONO}" font-size="{fs}" fill="{color}">{esc(out)}</text>')
        y += lh
        tcur = to + 0.9
    pw = len(prompt) * cw
    css.append(f"@keyframes tpf{{0%,{pc(tcur)}{{opacity:0}}{pc(tcur + .01)},97%{{opacity:1}}100%{{opacity:0}}}}")
    body.append(f'<g style="animation:tpf {T}s linear infinite"><text x="{x0}" y="{y}" font-family="{FONT_MONO}" font-size="{fs}" fill="#39D0B6" textLength="{pw}" lengthAdjust="spacingAndGlyphs">{esc(prompt)}</text>'
                f'<rect class="caret" x="{x0 + pw + cw}" y="{y - 15}" width="{cw * .8}" height="19" fill="#F2EFD9"/></g>')
    css.append(".caret{animation:blink 1s steps(1,end) infinite}@keyframes blink{50%{opacity:0}}")
    # scanlines (retro CRT, subtle)
    defs = grad_defs(t) + ('<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="2" fill="#FFFFFF" fill-opacity=".025"/></pattern>')
    body.append(f'<rect x="10" y="44" width="{W - 26}" height="{H - 58}" fill="url(#scan)" pointer-events="none"/>')
    return svg_doc(W, H, "".join(body), defs=defs, style=TB_SHINE_CSS + "".join(css), title="about_me — terminal",
                   desc=" / ".join(f"{l['cmd']}: {fmt(l['out'], P)}" for l in lines))


# =========================================================================== stack panel
def stack(t, P):
    W = 1280
    x0, y0 = 8, 8
    rows, y = [], y0 + 34 + 30
    chip_i = 0
    for gi, g in enumerate(P["stack"]):
        tr = TRACKS[g["track"]]
        gy = y
        rows.append(icon(g["icon"], 34, gy - 4, 1.75))
        rows.append(f'<text x="72" y="{gy + 19}" font-family="{FONT_UI}" font-size="17" font-weight="700" fill="{t["ink"]}">{esc(g["group"])}</text>')
        cx, cy = 260, gy
        for item in g["items"]:
            w_ = text_w(item, 15) + 46
            if cx + w_ > W - 40:
                cx, cy = 260, cy + 46
            rows.append(f'<g transform="translate({cx} {cy})"><g class="chip" style="animation-delay:{chip_i * .045:.3f}s">'
                        f'<rect x="3" y="3" width="{w_}" height="34" rx="8" fill="{t["shadow"]}" fill-opacity="{t["shadow_op"]}"/>'
                        f'<rect width="{w_}" height="34" rx="8" fill="{tr["light"]}" stroke="#0E1726" stroke-width="2"/>'
                        f'<rect x="12" y="13" width="8" height="8" fill="{tr["base"]}" shape-rendering="crispEdges"/>'
                        f'<text x="28" y="22.5" font-family="{FONT_UI}" font-size="15" fill="#0E1726">{esc(item)}</text></g></g>')
            cx += w_ + 10
            chip_i += 1
        y = cy + 46 + 16
        if gi < len(P["stack"]) - 1:
            rows.append(f'<rect x="34" y="{y - 14}" width="{W - 84}" height="2" fill="{t["ink3"]}" fill-opacity=".45" shape-rendering="crispEdges"/>')
    H = y + 6
    body = window(x0, y0, W - 22, H - 22, "control_panel.exe — tech stack", t, icon_name="cpu",
                  subtitle=f'{sum(len(g["items"]) for g in P["stack"])} items') + "".join(rows)
    css = (TB_SHINE_CSS + ".chip{animation:pop .5s cubic-bezier(.2,.9,.3,1.4) both}"
           "@keyframes pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}")
    return svg_doc(W, H, body, defs=grad_defs(t), style=css, title="Tech stack",
                   desc="; ".join(f'{g["group"]}: {", ".join(g["items"])}' for g in P["stack"]))


# =========================================================================== badge card
def badge_card(c, idx):
    W, H = 152, 236
    tr = TRACKS[c["track"]]
    legacy = c.get("legacy", False)
    art, mask = badge_art(c["tier"], c["track"], c["code"], legacy)
    ink, ink2, paper = "#0E1726", "#3B4A5E", "#FFFDF7"
    body = [f'<rect x="6" y="6" width="{W - 10}" height="{H - 10}" rx="10" fill="#0E1726" fill-opacity=".22"/>',
            f'<rect x="2" y="2" width="{W - 10}" height="{H - 10}" rx="10" fill="{paper}" stroke="{ink}" stroke-width="2"/>',
            f'<rect x="3" y="3" width="{W - 12}" height="22" rx="9" fill="{tr["light"] if not legacy else "#E3E3E3"}"/>'
            f'<rect x="3" y="16" width="{W - 12}" height="9" fill="{tr["light"] if not legacy else "#E3E3E3"}"/>'
            f'<rect x="3" y="25" width="{W - 12}" height="2" fill="{ink}" fill-opacity=".8"/>',
            f'<text x="{(W - 8) / 2}" y="19" text-anchor="middle" font-family="{FONT_UI}" font-size="10.5" font-weight="700" letter-spacing="1.6" fill="{tr["dark"]}">{esc(c["issuer"].upper())}</text>',
            f'<clipPath id="bm"><path d="{mask}"/></clipPath>',
            f'<g transform="translate({(W - 8) / 2 - 48} 36) scale(4)" shape-rendering="crispEdges"><g class="float" style="animation-delay:{-idx * .35:.2f}s">{art}'
            f'<g clip-path="url(#bm)"><rect class="bshine" style="animation-delay:{idx * .45:.2f}s" x="-10" y="-4" width="5" height="32" fill="#FFFFFF" fill-opacity=".7" transform="skewX(-20)"/></g></g></g>',
            f'<text x="{(W - 8) / 2}" y="156" text-anchor="middle" font-family="{FONT_MONO}" font-size="18" font-weight="800" fill="{ink}">{esc(c["code"])}</text>']
    for j, line in enumerate(wrap(c["short"], 21)[:2]):
        body.append(f'<text x="{(W - 8) / 2}" y="{175 + j * 15}" text-anchor="middle" font-family="{FONT_UI}" font-size="12" fill="{ink2}">{esc(line)}</text>')
    pill = "LEGACY" if legacy else c["level"].upper()
    pw = len(pill) * 7 + 16
    pfill, ptext_c = (tr["light"], tr["dark"]) if not legacy else ("#E3E3E3", "#4A4A4A")
    body.append(f'<rect x="{(W - 8) / 2 - pw / 2}" y="{H - 34}" width="{pw}" height="20" rx="10" fill="{pfill}" stroke="{ptext_c}" stroke-width="1.5"/>'
                f'<text x="{(W - 8) / 2}" y="{H - 20}" text-anchor="middle" font-family="{FONT_MONO}" font-size="11" font-weight="700" fill="{ptext_c}">{esc(pill)}</text>')
    css = (".float{animation:float 2.6s steps(1,end) infinite}@keyframes float{50%{transform:translateY(-1px)}}"
           ".bshine{animation:bshine 5s ease-in infinite}@keyframes bshine{0%,72%{transform:translateX(0) skewX(-20deg)}100%{transform:translateX(44px) skewX(-20deg)}}")
    level = c["level"] + (", legacy — " + c["note"] if legacy and c.get("note") else "")
    return svg_doc(W, H, "".join(body), style=css, title=f'{c["code"]} — {c["name"]}', desc=f'{c["issuer"]} · {level}')


# =========================================================================== project card
def project_card(t, p, idx):
    W, H = 620, 236
    body = [window(4, 4, W - 14, H - 14, p["repo"], t, icon_name="folder", title_h=34, subtitle="public repo", title_size=16, shadow=5)]
    for j, line in enumerate(wrap(p["desc"], 66)[:4]):
        body.append(f'<text x="26" y="{74 + j * 23}" font-family="{FONT_UI}" font-size="15.5" fill="{t["ink"]}">{esc(line)}</text>')
    by = H - 42
    lc = LANG_COLORS.get(p["lang"], "#9AA6B8")
    body.append(f'<circle class="dot" cx="32" cy="{by}" r="7" fill="{lc}" stroke="#0E1726" stroke-width="1.5"/>'
                f'<text x="46" y="{by + 5}" font-family="{FONT_UI}" font-size="14" fill="{t["ink2"]}">{esc(p["lang"])}</text>')
    x = 46 + text_w(p["lang"], 14) + 20
    for tag in p.get("tags", []):
        w_ = text_w(tag, 13) + 20
        body.append(f'<rect x="{x}" y="{by - 12}" width="{w_}" height="24" rx="12" fill="{t["paper2"]}" stroke="{t["ink3"]}" stroke-width="1.5"/>'
                    f'<text x="{x + 10}" y="{by + 4.5}" font-family="{FONT_UI}" font-size="13" fill="{t["ink2"]}">{esc(tag)}</text>')
        x += w_ + 8
    body.append(f'<text x="{W - 30}" y="{by + 5}" text-anchor="end" font-family="{FONT_MONO}" font-size="14" font-weight="700" fill="{t["accent"]}">open ↗</text>')
    css = TB_SHINE_CSS + ".dot{animation:dot 2s steps(1,end) infinite}@keyframes dot{50%{opacity:.45}}"
    return svg_doc(W, H, "".join(body), defs=grad_defs(t), style=css, title=f'{p["repo"]} — {p["lang"]}', desc=p["desc"])


# =========================================================================== talk card
def talk_card(t, tk):
    W, H = 1280, 276
    body = [window(8, 8, W - 22, H - 22, "talks/ — on stage", t, icon_name="mic")]
    body.append(f'<rect x="34" y="66" width="112" height="112" rx="10" fill="#DCEEFF" stroke="#0E1726" stroke-width="2"/>')
    body.append(icon("mic", 42, 74, 6))
    body.append(f'<g class="onair"><rect x="34" y="192" width="112" height="32" rx="6" fill="#E0482C" stroke="#0E1726" stroke-width="2"/>'
                f'<text x="90" y="214" text-anchor="middle" font-family="{FONT_UI}" font-size="16" font-weight="700" fill="#FFFFFF" letter-spacing="2">ON AIR</text></g>')
    ev = tk["pixel"]
    sc = 4
    body.append(ptext(ev, 186 + 3, 70 + 3, sc, t["name_shadow"], 'fill-opacity=".3"'))
    body.append(ptext(ev, 186, 70, sc, t["accent"]))
    for j, line in enumerate(wrap(f'«{tk["title"]}»', 58)[:2]):
        body.append(f'<text x="186" y="{138 + j * 30}" font-family="{FONT_UI}" font-size="22" font-style="italic" fill="{t["ink"]}">{esc(line)}</text>')
    body.append(f'<text x="186" y="216" font-family="{FONT_MONO}" font-size="15" fill="{t["ink2"]}">{esc(tk["role"])}  ·  {esc(tk["date"])}</text>')
    s1, s2 = tk.get("stamp", ["SPEAKER", ""])
    ink = "#C2185B" if t["name"] == "light" else "#FF8AC4"
    body.append(f'<g transform="translate(1110 142) rotate(-12)"><g class="stamp">'
                f'<circle r="82" fill="none" stroke="{ink}" stroke-width="5"/><circle r="70" fill="none" stroke="{ink}" stroke-width="2" stroke-dasharray="4 4"/>'
                f'<text y="-6" text-anchor="middle" font-family="{FONT_UI}" font-size="23" font-weight="700" letter-spacing="1.5" fill="{ink}">{esc(s1)}</text>'
                f'<text y="24" text-anchor="middle" font-family="{FONT_MONO}" font-size="17" font-weight="700" fill="{ink}">{esc(s2)}</text>'
                f'<g transform="translate(-8 40) scale(1)">{icon("star", 0, 0, 1)}</g></g></g>')
    css = (TB_SHINE_CSS + ".onair{animation:onair 1.4s steps(1,end) infinite}@keyframes onair{50%{opacity:.45}}"
           ".stamp{opacity:.92;transform-box:fill-box;transform-origin:center;animation:stamp .7s cubic-bezier(.2,.9,.3,1.3) 1s both}"
           "@keyframes stamp{from{opacity:0;transform:scale(1.7)}to{opacity:.92;transform:scale(1)}}")
    return svg_doc(W, H, "".join(body), defs=grad_defs(t), style=css, title=f'{tk["event"]} — {tk["role"]}',
                   desc=f'{tk["title"]} · {tk["date"]}')


# =========================================================================== guestbook button
def guestbook_button():
    W, H = 440, 76
    defs = ('<linearGradient id="btn" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF"/>'
            '<stop offset=".85" stop-color="#ECE9D8"/><stop offset="1" stop-color="#D6D0BC"/></linearGradient>')
    body = (f'<rect class="halo2" x="2" y="2" width="{W - 4}" height="{H - 4}" rx="12" fill="none" stroke="#FFD23F" stroke-width="4"/>'
            f'<rect x="8" y="8" width="{W - 16}" height="{H - 16}" rx="9" fill="url(#btn)" stroke="#003C74" stroke-width="2"/>'
            + icon("pen", 24, 18, 2.5) +
            f'<text x="76" y="40" font-family="{FONT_UI}" font-size="22" font-weight="700" fill="#0E1726">Sign my guestbook</text>'
            f'<text x="76" y="58" font-family="{FONT_MONO}" font-size="12" fill="#3B4A5E">1 click · your avatar shows up here</text>')
    css = ".halo2{animation:halo2 2.2s steps(1,end) infinite}@keyframes halo2{50%{opacity:.15}}"
    return svg_doc(W, H, body, defs=defs, style=css, title="Sign my guestbook")


# =========================================================================== crew (cats)
def crew(t, P):
    W, H = 1280, 286
    body = [window(8, 8, W - 22, H - 22, "cats.exe — the crew", t, icon_name="heart")]
    n = len(P["cats"])
    for i, c in enumerate(P["cats"]):
        cx = 220 + i * 420
        body.append(f'<rect x="{cx - 110}" y="196" width="220" height="8" fill="{t["hill"][1]}" shape-rendering="crispEdges"/>')
        body.append(f'<g transform="translate({cx - 80} 66) scale(2)">{cat_frames(c["sprite"])}</g>')
        body.append(f'<text x="{cx}" y="234" text-anchor="middle" font-family="{FONT_UI}" font-size="20" font-weight="700" fill="{t["ink"]}">{esc(c["name"])}</text>')
    return svg_doc(W, H, "".join(body), defs=grad_defs(t), style=TB_SHINE_CSS + CAT_CSS, title="The crew: " + ", ".join(c["name"] for c in P["cats"]))


# =========================================================================== README
def cert_status(x):
    if x.get("status"):
        return x["status"]
    if x.get("legacy"):
        return "Legacy — " + x.get("note", "exam retired")
    if x["level"] == "Fundamentals":
        return "No expiry"
    if x["issuer"] == "Microsoft" and x["level"] in ("Associate", "Expert"):
        return "Annual renewal"
    return "Active"


def picture(name, alt, width="100%", raw=None):
    if raw:
        light, dark = raw.format(theme="light"), raw.format(theme="dark")
    else:
        light, dark = f"assets/{name}-light.svg", f"assets/{name}-dark.svg"
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{dark}">\n'
            f'  <img src="{light}" width="{width}" alt="{esc(alt)}">\n</picture>')


def readme(P, G):
    login = P["login"]
    c = counts(P)
    certs = [x for x in P["certs"] if x.get("show", True)]
    nav = [("about", "about", "doc"), ("achievements", "achievements", "medal"), ("projects", "projects", "folder"),
           ("talks", "talks", "mic"), ("activity", "activity", "chart"), ("guestbook", "guestbook", "pen")]
    L = []
    a = L.append
    a("<!-- ⚠️ Generated by tools/build.py from data/profile.json + data/guestbook.json. Edit those files, not this one. -->")
    a('<a id="top"></a>\n')
    a('<div align="center">\n')
    a(picture("header", f"victoria.exe — {P['name']}, {P['role']} at {P['company']}. Pixel desktop with three running cats."))
    a("")
    a(" ".join(f'<a href="#{anchor}"><img src="assets/nav/{anchor}.svg" height="38" alt="{label}"></a>' for anchor, label, _ in nav))
    a("\n</div>\n")

    # about
    a('<a id="about"></a>\n')
    a('<img src="assets/terminal.svg" width="100%" alt="Terminal: whoami → Victoria Faranna, Cloud &amp; AI Data Solution Engineer at Microsoft">\n')
    a(P["intro"] + "\n")
    a(f"> 🔎 *{P['tagline'].rstrip('.')}* — quality, cost, emissions and governance included.\n")
    for f_ in P["focus"]:
        a(f"- {f_}")
    a("")
    a("<details>\n<summary><b>🎓 education.log</b> — where I learned (and keep learning)</summary>\n")
    for e in P["education"]:
        a(f"- {e}")
    a("\n</details>\n")
    a(picture("stack", "control_panel.exe — tech stack"))
    a("")
    a('<p align="center">')
    a(f'  <img src="https://skillicons.dev/icons?i={P["skillicons"]}&perline=12" height="40" alt="Skill icons">')
    a("</p>\n")

    # achievements
    a('<a id="achievements"></a>\n')
    a(f'<img src="assets/bars/achievements.svg" width="100%" alt="achievements.exe — {c["certs"]} unlocked">\n')
    a('<p align="center">')
    for i, x in enumerate(certs):
        a(f'  <a href="{x["url"]}"><img src="assets/badges/{slug(x["code"])}.svg" width="128" alt="{esc(x["code"])} — {esc(x["name"])}"></a>')
        if i == 5:
            a("  <br>")
    a("</p>\n")
    verify = f' · <a href="{P["verify_url"]}">verify on Microsoft Learn ↗</a>' if P.get("verify_url") else ""
    a(f'<p align="center"><sub>Click a badge to open the official certification page{verify}</sub></p>\n')
    a("<details>\n<summary><b>📜 full_list.csv</b> — every credential, level and status</summary>\n")
    a("| | Credential | Issuer | Level | Status |\n|---|---|---|---|---|")
    for x in certs:
        status = cert_status(x)
        a(f'| **{x["code"]}** | [{x["name"]}]({x["url"]}) | {x["issuer"]} | {x["level"]} | {status} |')
    a("\n</details>\n")
    a("<details>\n<summary><b>🗺️ skill_map.mmd</b> — how the credentials stack up (pan &amp; zoom me)</summary>\n")
    a("```mermaid")
    a("%%{init: {'theme':'base','themeVariables':{'fontFamily':'Tahoma, Segoe UI, sans-serif','primaryColor':'#DCEEFF','primaryTextColor':'#0E1726','primaryBorderColor':'#0B3A8C','lineColor':'#3B4A5E'}}}%%")
    a("flowchart LR")
    tiers = {1: "Fundamentals &amp; Beginner", 2: "Associate &amp; Intermediate", 3: "Expert"}
    for tier in (1, 2, 3):
        a(f'  subgraph T{tier}["{tiers[tier]}"]')
        for x in [y for y in certs if y["tier"] == tier]:
            nid = x["code"].replace("-", "")
            a(f'    {nid}["{x["code"]}<br/><small>{x["short"]}</small>"]:::{x["track"]}')
        a("  end")
    a("  T1 --> T2 --> T3")
    for k, tr in TRACKS.items():
        a(f"  classDef {k} fill:{tr['light']},stroke:{tr['dark']},stroke-width:2px,color:#0E1726")
    a("```\n")
    a("<sub>Levels as published by each issuer · arrows show the learning path, not official prerequisites.</sub>\n")
    a("</details>\n")

    # projects
    a('<a id="projects"></a>\n')
    a(f'<img src="assets/bars/projects.svg" width="100%" alt="projects/ — {len(P["projects"])} featured">\n')
    a('<p align="center">')
    for i, p in enumerate(P["projects"]):
        a(f'  <a href="https://github.com/{login}/{p["repo"]}">')
        a(f'    <picture><source media="(prefers-color-scheme: dark)" srcset="assets/projects/{p["repo"]}-dark.svg">'
          f'<img src="assets/projects/{p["repo"]}-light.svg" width="49%" alt="{esc(p["repo"])}: {esc(p["desc"])}"></picture>')
        a("  </a>")
    a("</p>\n")
    if P.get("more_repos"):
        a("<details>\n<summary><b>📂 more public repos</b></summary>\n")
        for r in P["more_repos"]:
            a(f'- [`{r["repo"]}`](https://github.com/{login}/{r["repo"]}) · {r["lang"]}')
        a("\n</details>\n")

    # talks
    a('<a id="talks"></a>\n')
    for tk in P.get("talks", []):
        a(picture("talk", f'{tk["event"]} — {tk["role"]}: «{tk["title"]}» · {tk["date"]}'))
        a("")

    # activity
    a('<a id="activity"></a>\n')
    a('<img src="assets/bars/activity.svg" width="100%" alt="system_monitor.exe — GitHub activity">\n')
    raw = f"https://raw.githubusercontent.com/{login}/{login}/output/{{name}}-{{theme}}.svg"
    a('<p align="center">')
    a(picture("", "GitHub activity: contributions, streaks, repos and top languages", raw=raw.replace("{name}", "stats")))
    a("</p>\n")
    a('<p align="center">')
    a(picture("", "Snake eating my contribution graph", raw=raw.replace("{name}", "snake")))
    a("</p>\n")

    # guestbook
    a('<a id="guestbook"></a>\n')
    a('<img src="assets/bars/guestbook.svg" width="100%" alt="guestbook.exe — sign it!">\n')
    a('<p align="center">')
    a(f'  <a href="https://github.com/{login}/{login}/issues/new?template=guestbook.yml"><img src="assets/guestbook-button.svg" height="68" alt="Sign my guestbook"></a>')
    a("</p>")
    a('<p align="center"><sub>Click → <b>Create</b> → a friendly bot adds your avatar below and closes the issue. Only your public avatar is shown.</sub></p>\n')
    a("<!-- GUESTBOOK:START -->")
    signers = (G or {}).get("signers", [])
    if signers:
        a('<p align="center">')
        for s in signers[:24]:
            u = s["login"]
            a(f'  <a href="https://github.com/{u}"><img src="https://github.com/{u}.png?size=88" width="44" height="44" alt="@{u}" title="@{u}"></a>')
        a("</p>")
        a(f'<p align="center"><sub>{len(signers)} visitor{"s" if len(signers) != 1 else ""} signed so far ✨</sub></p>')
    else:
        a('<p align="center"><sub>No signatures yet — be the first! ✨</sub></p>')
    a("<!-- GUESTBOOK:END -->\n")

    # cats + contact + footer
    a("<details>\n<summary><b>🐈 cats.exe</b> — meet the crew running around this page</summary>\n")
    a(picture("crew", "Coco, Nemo and Tofu, three pixel cats"))
    a("\n</details>\n")
    a('<div align="center">\n')
    links = [f'<a href="{P["linkedin"]}"><img src="assets/nav/linkedin.svg" height="38" alt="LinkedIn"></a>']
    if P.get("portfolio"):
        links.append(f'<a href="{P["portfolio"]}"><img src="assets/nav/portfolio.svg" height="38" alt="Portfolio"></a>')
    links.append('<a href="#top"><img src="assets/nav/top.svg" height="38" alt="Back to top"></a>')
    a(" ".join(links))
    a("")
    a(f'<img src="https://komarev.com/ghpvc/?username={login}&style=pixel&color=1F5FD6&label=VISITORS" alt="Profile visitors">\n')
    a(picture("footer", "Thanks for visiting! Retro taskbar with three running cats."))
    a("\n</div>")
    return "\n".join(L) + "\n"


# =========================================================================== main
def main():
    P = load("data/profile.json")
    G = load("data/guestbook.json", {"signers": []})
    if "--readme-only" not in sys.argv:
        for th in ("light", "dark"):
            t = THEMES[th]
            write(f"assets/header-{th}.svg", header(t, P))
            write(f"assets/footer-{th}.svg", footer(t, P))
            write(f"assets/stack-{th}.svg", stack(t, P))
            write(f"assets/crew-{th}.svg", crew(t, P))
            for i, p in enumerate(P["projects"]):
                write(f"assets/projects/{p['repo']}-{th}.svg", project_card(t, p, i))
            for tk in P.get("talks", [])[:1]:
                write(f"assets/talk-{th}.svg", talk_card(t, tk))
        write("assets/terminal.svg", terminal(P))
        c = counts(P)
        bars = {"achievements": (f"achievements.exe", f"{c['certs']} unlocked · {c['issuers']} issuers", "medal"),
                "projects": ("projects/", f"{len(P['projects'])} featured", "folder"),
                "activity": ("system_monitor.exe", "GitHub activity · refreshed daily", "chart"),
                "guestbook": ("guestbook.exe", "sign it!", "pen")}
        for k, (title, sub, ic) in bars.items():
            write(f"assets/bars/{k}.svg", bar(title, sub, ic))
        for label, ic in [("about", "doc"), ("achievements", "medal"), ("projects", "folder"), ("talks", "mic"),
                          ("activity", "chart"), ("guestbook", "pen"), ("linkedin", "card"), ("portfolio", "globe"), ("top", "star")]:
            write(f"assets/nav/{label}.svg", nav_button("back to top" if label == "top" else label, ic))
        for i, x in enumerate([y for y in P["certs"] if y.get("show", True)]):
            write(f"assets/badges/{slug(x['code'])}.svg", badge_card(x, i))
        write("assets/guestbook-button.svg", guestbook_button())
    write("README.md", readme(P, G))
    print("built", "README only" if "--readme-only" in sys.argv else "assets + README")


if __name__ == "__main__":
    main()
