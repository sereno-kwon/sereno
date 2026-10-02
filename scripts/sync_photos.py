#!/usr/bin/env python3
"""Build photos/photos.json and resized images from a folder of source images.

Usage: python3 scripts/sync_photos.py <source_dir>
Each source image becomes photos/<stem>-full.jpg (max 2000px) and photos/<stem>-thumb.jpg (800px, 4:5 crop).
Caption comes from the file name: "2026-09 남양성모성지.jpg" -> "남양성모성지". Sorted newest-first by name.
"""
import json, sys, pathlib
from PIL import Image, ImageOps

src = pathlib.Path(sys.argv[1]); out = pathlib.Path(__file__).resolve().parent.parent / 'photos'
out.mkdir(exist_ok=True)
entries = []
for f in sorted(src.iterdir(), reverse=True):
    if f.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.heic', '.webp'): continue
    stem = f.stem
    im = ImageOps.exif_transpose(Image.open(f)).convert('RGB')
    full = im.copy(); full.thumbnail((2000, 2000)); full.save(out / f'{stem}-full.jpg', quality=85, optimize=True)
    thumb = ImageOps.fit(im, (800, 1000), Image.LANCZOS); thumb.save(out / f'{stem}-thumb.jpg', quality=82, optimize=True)
    caption = stem.split(' ', 1)[1] if ' ' in stem and stem[:4].isdigit() else stem
    entries.append({'full': f'{stem}-full.jpg', 'thumb': f'{stem}-thumb.jpg', 'caption': caption, 'w': 800, 'h': 1000})
(out / 'photos.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(entries)} photos')
