#!/usr/bin/env python3
"""Create the web-ready versions of a photo: name-600/1000/1400.webp and name-1000.jpg in assets/images/.
Usage: python3 _tools/optimise-image.py path/to/photo.jpg short-name   (needs: pip install pillow)"""
import os, sys
from PIL import Image
src, name = sys.argv[1], sys.argv[2]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'images')
im = Image.open(src).convert('RGB')
for w in (600, 1000, 1400):
    r = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    r.save(os.path.join(out, '%s-%d.webp' % (name, w)), quality=82, method=6)
    if w == 1000:
        r.save(os.path.join(out, '%s-1000.jpg' % name), quality=84, optimize=True, progressive=True)
print('Done. Add an entry for "%s" (width 1400, height %d) to media.items in _content/content.json, then run build.py.' % (name, round(im.height * 1400 / im.width)))
