#!/usr/bin/env python3
"""Host-side (PIL only): assemble sagittal tiles (sagittal-slices.py output, *.u8) into labelled sheets, ID order.
usage: render-montage.py tile_dir out_prefix [W H]   -> out_prefix-1.png, -2.png, ... (7 columns x 6 rows)
W H: tile size in pixels, as printed by sagittal-slices.py (width height); default 256 176. All tiles must share it."""
import sys, glob, os
from PIL import Image, ImageDraw
tdir, oprefix = sys.argv[1:3]
tiles = sorted(glob.glob(f"{tdir}/*.u8"), key=os.path.basename)
W, H = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) >= 5 else (256, 176)
COLS, ROWS = 7, 6
for si in range(0, len(tiles), COLS * ROWS):
    chunk = tiles[si:si + COLS * ROWS]
    sheet = Image.new("L", (COLS * W, ROWS * H), 0); dr = ImageDraw.Draw(sheet)
    for k, p in enumerate(chunk):
        im = Image.frombytes("L", (W, H), open(p, "rb").read())
        x, y = (k % COLS) * W, (k // COLS) * H
        sheet.paste(im, (x, y)); dr.rectangle([x, y, x + 52, y + 11], fill=0); dr.text((x + 3, y), os.path.basename(p)[:-3], fill=255); dr.rectangle([x, y, x + W - 1, y + H - 1], outline=90)
    f = f"{oprefix}-{si // (COLS * ROWS) + 1}.png"; sheet.save(f); print(f, sheet.size)
