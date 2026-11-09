#!/usr/bin/env python3
"""One-off helper: turn the cat sprite sheets (PNG, 6 frames x 80x68) into tools/sprites/cats.json.

Only needed if a sprite PNG changes (requires Pillow: pip install pillow). build.py reads the JSON,
so the profile build itself stays dependency-free and the SVGs contain pure vector pixels
(no embedded bitmaps, which GitHub's image sandbox may block).
"""
import glob
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES, FW = 6, 80
out = {}
for png in sorted(glob.glob(os.path.join(HERE, "*.png"))):
    im = Image.open(png).convert("RGBA")
    px = im.load()
    W, H = im.size
    frames = []
    for f in range(FRAMES):
        by = {}
        for y in range(H):
            x = f * FW
            while x < (f + 1) * FW:
                c = px[x, y]
                if c[3] == 0:
                    x += 1
                    continue
                x0 = x
                while x < (f + 1) * FW and px[x, y] == c:
                    x += 1
                key = "#%02X%02X%02X" % c[:3]
                by.setdefault(key, []).append(f"M{x0 - f * FW} {y}h{x - x0}v1h-{x - x0}z")
        frames.append({k: "".join(v) for k, v in by.items()})
    out[os.path.basename(png)] = {"w": FW, "h": H, "frames": frames}
with open(os.path.join(HERE, "cats.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, separators=(",", ":"))
print("wrote cats.json with", list(out))
