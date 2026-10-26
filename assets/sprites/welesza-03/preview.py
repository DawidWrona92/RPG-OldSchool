"""Podgląd klatek na tle leśnej ziemi: arkusz 1× oraz powiększenie nearest.

Użycie: python3 preview.py <wzorzec glob> <plik wyjściowy> [powiększenie]
"""
import glob
import sys

from PIL import Image, ImageDraw

GROUND = (35, 41, 31, 255)

if __name__ == "__main__":
    pattern, out = sys.argv[1], sys.argv[2]
    scale = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    paths = sorted(glob.glob(pattern))
    frames = [Image.open(p).convert("RGBA") for p in paths]
    w, h = frames[0].size
    label = 14
    sheet = Image.new("RGBA", (w * len(frames), h + label), GROUND)
    draw = ImageDraw.Draw(sheet)
    for i, (path, frame) in enumerate(zip(paths, frames)):
        sheet.alpha_composite(frame, (i * w, label))
        draw.text((i * w + 4, 1), path.split("/")[-1].replace(".png", "").replace("drwal_rozlupanie_", ""), fill=(200, 200, 190, 255))
    if scale > 1:
        sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    sheet.save(out)
    print(out, sheet.size)
