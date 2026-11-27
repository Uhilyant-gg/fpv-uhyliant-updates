from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'fpv-uhyliant.ico'
OUT.parent.mkdir(parents=True, exist_ok=True)
S = 1024
im = Image.new('RGBA', (S, S), (5, 13, 24, 255))
d = ImageDraw.Draw(im)
d.rounded_rectangle((42, 42, 982, 982), radius=190, fill=(8, 24, 43, 255), outline=(45, 144, 255, 255), width=34)
d.arc((98, 98, 926, 926), 205, 335, fill=(255, 214, 0, 255), width=34)
d.rounded_rectangle((205, 337, 819, 683), radius=110, outline=(245, 248, 252, 255), width=55)
d.line((512, 355, 512, 665), fill=(245, 248, 252, 255), width=34)
d.arc((292, 185, 732, 515), 190, 350, fill=(245, 248, 252, 255), width=42)
d.arc((147, 425, 318, 708), 80, 280, fill=(245, 248, 252, 255), width=42)
d.arc((706, 425, 877, 708), 260, 100, fill=(245, 248, 252, 255), width=42)
for cx in (310, 714):
    d.ellipse((cx - 76, 200, cx + 76, 240), fill=(255, 214, 0, 255))
    d.ellipse((cx - 18, 144, cx + 18, 296), fill=(45, 144, 255, 255))
d.line((310, 220, 714, 220), fill=(245, 248, 252, 255), width=28)
d.rounded_rectangle((450, 177, 574, 270), radius=30, fill=(245, 248, 252, 255))
d.rounded_rectangle((214, 748, 810, 900), radius=55, fill=(13, 41, 70, 255), outline=(255, 214, 0, 255), width=18)
# FPV monogram
for xy in [
    ((285, 790), (285, 858)),
    ((285, 790), (365, 790)),
    ((285, 824), (350, 824)),
    ((425, 790), (425, 858)),
    ((425, 790), (492, 790)),
    ((492, 790), (492, 824)),
    ((425, 824), (492, 824)),
]:
    d.line((*xy[0], *xy[1]), fill=(245, 248, 252, 255), width=25)
d.line((558, 790, 606, 858), fill=(45, 144, 255, 255), width=25)
d.line((606, 858, 654, 790), fill=(255, 214, 0, 255), width=25)
d.line((676, 790, 724, 858), fill=(45, 144, 255, 255), width=25)
d.line((724, 858, 772, 790), fill=(255, 214, 0, 255), width=25)
im.save(OUT, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(OUT)
