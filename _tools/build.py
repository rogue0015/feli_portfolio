#!/usr/bin/env python3
"""Static site builder for Felicia Chuma: single-page portfolio + markdown blog.

One command builds everything:

    python3 _tools/build.py

Output:
  index.html            the whole portfolio as a single page (sections are anchors)
  blogs/index.html      the blog index (paginated: page2.html, page3.html …)
  blogs/<slug>.html     one page per blog post
  404.html, sitemap.xml, robots.txt, feed.xml

All editable content (site details, hero, about, work, community, media,
contact) lives in _content/content.json. Blog posts are markdown files in
_content/blog/*.md, using the front-matter template at
_content/blog/_post-template.md.

Set your details once (saved back into _content/content.json):

    python3 _tools/build.py \
      --site-url https://YOUR-REAL-ADDRESS \
      --email you@example.com \
      --linkedin https://www.linkedin.com/in/your-profile \
      --github https://github.com/your-username \
      --form-endpoint https://formspree.io/f/xxxxxxxx
"""
import argparse, datetime, html, json, os, re, sys
from email.utils import format_datetime
from datetime import datetime as dt, timezone
from urllib.parse import urljoin

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
CONTENT = os.path.join(ROOT, '_content')
BLOG_SRC = os.path.join(CONTENT, 'blog')
BLOG_OUT = os.path.join(ROOT, 'blogs')
CFG_PATH = os.path.join(CONTENT, 'content.json')
TODAY = datetime.date.today()
PER_PAGE = 6

e = html.escape


# ---------------------------------------------------------------- content
cfg = json.load(open(CFG_PATH, encoding='utf-8'))
ap = argparse.ArgumentParser()
for k in cfg['site']:
    ap.add_argument('--' + k.replace('_', '-'), dest=k)
for k, v in vars(ap.parse_args()).items():
    if v is not None:
        cfg['site'][k] = v.strip()
json.dump(cfg, open(CFG_PATH, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

SITE = cfg['site']['url'].rstrip('/')
NAME = cfg['site']['name']


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(text)


def rel(depth):
    return '../' * depth


def abs_url(path):
    return SITE + '/' + path


def pretty_date(d):
    return '%d %s %d' % (d.day, d.strftime('%B'), d.year)


# ---------------------------------------------------------------- icons
ICON = {
    'linkedin': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9.75h4v11.5H3zM9.5 9.75h3.8v1.6h.06c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.77 2.65 4.77 6.1v5.85h-4v-5.2c0-1.24-.02-2.84-1.73-2.84-1.73 0-2 1.35-2 2.75v5.29h-4z"/></svg>',
    'github': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5a11.5 11.5 0 0 0-3.64 22.41c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.19 1.76 1.19 1.03 1.76 2.7 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.42-2.69 5.4-5.25 5.68.41.36.78 1.06.78 2.13v3.16c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .5z"/></svg>',
    'mail': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    'up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 19V5M5 12l7-7 7 7"/></svg>',
    'menu': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    'close': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
    'arrow': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
}


def social_links(cls='social'):
    s = cfg['site']
    out = []
    if s['linkedin']:
        out.append('<li><a class="icon-btn" href="%s" rel="me noopener" target="_blank" aria-label="Felicia Chuma on LinkedIn">%s</a></li>' % (e(s['linkedin']), ICON['linkedin']))
    if s['github']:
        out.append('<li><a class="icon-btn" href="%s" rel="me noopener" target="_blank" aria-label="Felicia Chuma on GitHub">%s</a></li>' % (e(s['github']), ICON['github']))
    return '<ul class="%s">%s</ul>' % (cls, ''.join(out)) if out else ''


# ---------------------------------------------------------------- blog markdown
CODE_SPAN = re.compile(r"`([^`]+)`")


def _rel(url):
    """Rewrite root-absolute internal URLs relative to blogs/."""
    if url.startswith(SITE):
        url = url[len(SITE):] or "/"
    if url == "/" or url.startswith("/#"):
        return "../index.html" + url[1:]
    if url in ("/blogs/", "/blogs"):
        return "index.html"
    if url.startswith("/blogs/"):
        return url[len("/blogs/"):]
    if url.startswith("/"):
        return ".." + url
    return url


def _link(m):
    text, url = m.group(1), m.group(2)
    external = url.startswith("http") and not url.startswith(SITE)
    attrs = ' target="_blank" rel="noopener"' if external else ""
    return '<a href="%s"%s>%s</a>' % (_rel(url), attrs, text)


def inline(text):
    spans = []

    def stash(m):
        spans.append(html.escape(m.group(1), quote=False))
        return "\x00%d\x00" % (len(spans) - 1)
    text = CODE_SPAN.sub(stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                  lambda m: '<img src="%s" alt="%s" loading="lazy">' % (_rel(m.group(2)), m.group(1)), text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", _link, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: "<code>%s</code>" % spans[int(m.group(1))], text)


BLOCK_START = re.compile(r"^(#{1,6}\s|>|```|[-*]\s|\d+\.\s)|^(-{3,}|\*{3,})\s*$")


def md_to_html(md):
    lines = md.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf), quote=False))
            continue
        m = re.match(r"(#{1,6})\s+(.*)", line)
        if m:
            lvl = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2).strip()), lvl))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            paras = "\n".join(buf).split("\n\n")
            inner = "".join("<p>%s</p>" % inline(" ".join(p.split())) for p in paras if p.strip())
            out.append("<blockquote>%s</blockquote>" % inner)
            continue
        for marker, tag in ((r"^\s*[-*]\s+", "ul"), (r"^\s*\d+\.\s+", "ol")):
            if re.match(marker, line):
                items = []
                while i < n and lines[i].strip():
                    if re.match(marker, lines[i]):
                        items.append(re.sub(marker, "", lines[i]).strip())
                    elif lines[i].startswith("  ") and items:
                        items[-1] += " " + lines[i].strip()
                    else:
                        break
                    i += 1
                out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(it) for it in items), tag))
                break
        else:
            buf = [line.strip()]
            i += 1
            while i < n and lines[i].strip() and not BLOCK_START.match(lines[i].lstrip()):
                buf.append(lines[i].strip())
                i += 1
            out.append("<p>%s</p>" % inline(" ".join(buf)))
    return "\n".join(out)


def parse_front_matter(text, path):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        sys.exit("ERROR: %s is missing its front matter block (--- ... ---)." % path)
    meta, body = {}, text[m.end():]
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip()] = val.strip().strip('"').strip("'")
    tags = meta.get("tags", "")
    if tags.startswith("[") and tags.endswith("]"):
        tags = tags[1:-1]
    meta["tags"] = [t.strip().strip('"').strip("'") for t in tags.split(",") if t.strip()]
    for req in ("title", "date"):
        if not meta.get(req):
            sys.exit("ERROR: %s front matter is missing '%s'." % (path.name, req))
    meta["date_obj"] = datetime.date.fromisoformat(meta["date"])
    return meta, body


def load_posts():
    if not os.path.isdir(BLOG_SRC):
        return []
    posts = []
    for name in sorted(os.listdir(BLOG_SRC)):
        if not name.endswith('.md') or name.startswith('_'):
            continue
        path = os.path.join(BLOG_SRC, name)
        meta, body = parse_front_matter(open(path, encoding='utf-8').read(), path)
        slug = os.path.splitext(name)[0]
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            sys.exit("ERROR: %s: slug must be lowercase-with-hyphens." % name)
        content = md_to_html(body)
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", content)))
        posts.append({
            'slug': slug, 'title': meta['title'],
            'description': meta.get('description') or truncate(re.sub(r"<[^>]+>", "", re.search(r"<p>(.*?)</p>", content, re.S).group(1)) if re.search(r"<p>(.*?)</p>", content, re.S) else ''),
            'date': meta['date_obj'], 'tags': meta['tags'], 'content': content,
            'words': words, 'minutes': max(1, words // 200 + 1),
            'cover': 'assets/images/covers/%s.svg' % slug,
            'href': '%s.html' % slug, 'url': abs_url('blogs/%s.html' % slug),
        })
    posts.sort(key=lambda p: p['date'])
    return posts


def truncate(s, limit=180):
    s = " ".join(s.split())
    return s if len(s) <= limit else s[:limit - 1].rstrip() + "…"


def cover_svg(slug, cat=''):
    import hashlib
    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)

    def r(i, lo, hi):
        return lo + ((h >> (i * 7)) % 1000) / 1000 * (hi - lo)
    c = '#B69AF7'
    shapes = ''.join('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="%s" opacity="%.2f"/>'
                     % (r(i, 100, 1100), r(i + 8, 60, 580), r(i + 16, 30, 190), c if i % 2 == 0 else '#D6C8FF', r(i + 24, .08, .3))
                     for i in range(7))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#101114"/><stop offset="1" stop-color="#262033"/></linearGradient></defs>'
            '<rect width="1200" height="630" fill="url(#g)"/>%s'
            '<path d="M80 470 C 300 360, 420 540, 640 430 S 980 330, 1120 440" fill="none" stroke="%s" stroke-width="3" opacity=".8"/></svg>'
            % (shapes, c))


# ---------------------------------------------------------------- shared chrome
HEAD_JS = "<script>(function(){document.documentElement.classList.add('js')})();</script>"


def head(title, desc, canon, r, og_type='website', og_image='assets/images/og-image.jpg', jsonld=None, extra=''):
    img = abs_url(og_image)
    ld = ''
    if jsonld:
        items = jsonld if isinstance(jsonld, list) else [jsonld]
        ld = ''.join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False) for x in items)
    return '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="author" content="Felicia Chuma">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta name="theme-color" content="#0D0E12">
<link rel="canonical" href="%(canon)s">
<link rel="icon" href="%(r)sassets/icons/favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="Felicia Chuma">
<meta property="og:type" content="%(og_type)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canon)s">
<meta property="og:image" content="%(img)s">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<meta name="twitter:image" content="%(img)s">
%(headjs)s
<link rel="stylesheet" href="%(r)scss/site.css">
%(extra)s
%(ld)s''' % dict(title=e(title), desc=e(desc), canon=canon, r=r, og_type=og_type, img=img,
                 headjs=HEAD_JS, extra=extra, ld=ld)


def person_ld():
    s = cfg['site']
    return [
        {'@context': 'https://schema.org', '@type': 'Person', 'name': NAME, 'url': abs_url(''),
         'image': abs_url('assets/images/portrait-1000.jpg'),
         'description': 'Felicia Chuma studies data science at Midlands State University after three years in IT support. Portfolio, projects and writing.',
         'knowsAbout': ['Data analytics', 'Data science', 'Python', 'Computer vision', 'Machine learning', 'Power BI', 'Information technology'],
         'alumniOf': [{'@type': 'CollegeOrUniversity', 'name': 'Midlands State University'}, {'@type': 'EducationalOrganization', 'name': 'Gweru Polytechnic College'}],
         'sameAs': [u for u in (s['linkedin'], s['github']) if u]},
        {'@context': 'https://schema.org', '@type': 'WebSite', 'name': NAME, 'url': abs_url(''), 'inLanguage': 'en'},
    ]


# Circuit traces drawn behind the page, with a light pulse travelling along them.
CIRCUIT_TRACES = [
    "M-60 150 H300 L380 230 H700",
    "M700 230 L780 310 H1080",
    "M1120 -40 V120 L1180 180 H1500",
    "M1500 340 H1200 L1120 420 V620 L1060 680 H760",
    "M-60 460 H180 L260 540 V760 L320 820 H560",
    "M560 820 L620 880 H920",
    "M240 960 V700 L300 640 V480",
    "M920 880 V760 L980 700 H1300",
    "M480 600 H760 L820 660",
    "M60 300 H220 L280 360 V520",
    "M1300 40 H1080 L1020 120 V220",
    "M900 -40 V80 L960 140 H1200",
]
CIRCUIT_NODES = [
    (300, 150), (380, 230), (780, 310), (1120, 120), (1180, 180), (1200, 340),
    (1120, 420), (1120, 620), (1060, 680), (180, 460), (260, 540), (260, 760),
    (320, 820), (240, 700), (300, 640), (300, 480), (980, 700), (760, 600),
    (220, 300), (280, 360), (280, 520), (1080, 60), (1020, 120), (900, 80),
]
# (trace index, cycle seconds, start offset)
CIRCUIT_PULSES = [(0, 5.2, 0), (3, 7.4, -2.4), (4, 6.1, -4.2), (7, 8.2, -1.1), (10, 6.7, -3.6), (1, 9.0, -5.5)]


def circuit_bg():
    traces = ''.join('<path d="%s"/>' % d for d in CIRCUIT_TRACES)
    nodes = ''.join('<circle cx="%d" cy="%d" r="3"/>' % (x, y) for x, y in CIRCUIT_NODES)
    pulses = ''.join('<path class="pulse" pathLength="100" style="--dur:%ss;animation-delay:%ss" d="%s"/>'
                     % (dur, delay, CIRCUIT_TRACES[i]) for i, dur, delay in CIRCUIT_PULSES)
    return ('<div class="circuit" aria-hidden="true">'
            '<svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" focusable="false">'
            '<g class="traces">%s</g><g class="nodes">%s</g><g class="pulses">%s</g>'
            '</svg></div>' % (traces, nodes, pulses))


def site_header(active=None):
    nav = ''.join('<li><a href="%s"%s>%s</a></li>' % (e(item['href']), ' aria-current="page"' if item['label'] == active else '', e(item['label']))
                  for item in cfg['nav'])
    tools = social_links('social hide-sm')
    return '''<header class="site-header">
  <div class="inner">
    <a class="brand" href="#top" aria-label="%(name)s, back to top"><span class="mark" aria-hidden="true">FC</span><span class="name">%(name)s</span></a>
    <nav class="nav" id="site-nav" aria-label="Main navigation"><ul>%(nav)s</ul></nav>
    <div class="header-tools">
      %(tools)s
      <button type="button" class="icon-btn menu-btn" id="menu-btn" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">%(menu)s</button>
    </div>
  </div>
</header>
<div class="progress-bar" id="progress-bar" aria-hidden="true"></div>''' % dict(name=e(NAME), nav=nav, tools=tools, menu=ICON['menu'])


def site_footer(r=''):
    s = cfg['site']
    credit = s.get('photo_credit', '').strip()
    fine = '<div class="fine"><span>&copy; %d Felicia Chuma. All rights reserved.</span>%s</div>' % (
        TODAY.year, ('<span>Portraits by %s</span>' % e(credit)) if credit else '')
    explore = ''.join('<li><a href="%s%s">%s</a></li>' % (r, e(i['href']), e(i['label'])) for i in cfg['nav'])
    connect = []
    if s['linkedin']:
        connect.append('<li><a href="%s" rel="me noopener" target="_blank">LinkedIn</a></li>' % e(s['linkedin']))
    if s['github']:
        connect.append('<li><a href="%s" rel="me noopener" target="_blank">GitHub</a></li>' % e(s['github']))
    connect.append('<li><a href="%s#contact">Send a message</a></li>' % r)
    return '''<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <p class="footer-tag">%(tag)s</p>
        <p class="muted">%(note)s</p>
        %(social)s
      </div>
      <div><h2>Explore</h2><ul>%(explore)s</ul></div>
      <div><h2>Connect</h2><ul>%(connect)s</ul></div>
    </div>
    %(fine)s
  </div>
</footer>
<button type="button" class="icon-btn to-top" id="to-top" aria-label="Back to top">%(up)s</button>''' % dict(
        tag=e(s['footer_tag']), note=e(s['footer_note']), social=social_links('social footer-social'),
        explore=explore, connect=''.join(connect), fine=fine, up=ICON['up'])


def picture(base, alt, sizes, depth, eager=False, cls='', width=1000, height=1454):
    r = rel(depth)
    return ('<picture><source type="image/webp" srcset="%sassets/images/%s-600.webp 600w, %sassets/images/%s-1000.webp 1000w, %sassets/images/%s-1400.webp 1400w" sizes="%s">'
            '<img src="%sassets/images/%s-1000.jpg" alt="%s" width="%d" height="%d" %s%s></picture>'
            % (r, base, r, base, r, base, sizes, r, base, e(alt), width, height,
               'fetchpriority="high" ' if eager else 'loading="lazy" decoding="async" ', ('class="%s"' % cls) if cls else ''))


# ---------------------------------------------------------------- single page
def vision_svg():
    frames = ''
    for x, y, rot in [(30, 60, -6), (70, 100, 0), (110, 140, 6)]:
        frames += ('<g transform="translate(%d %d) rotate(%d 60 60)"><rect width="120" height="120" rx="14" fill="#292C36" stroke="#B69AF7" stroke-width="1.5"/>'
                   '<circle cx="60" cy="72" r="20" fill="none" stroke="#D6C8FF" stroke-width="3"/>'
                   '<path d="M44 58V34M54 52V26M64 52V24M74 56V32M84 66l14-16" stroke="#D6C8FF" stroke-width="6" stroke-linecap="round"/></g>' % (x, y, rot))
    nodes = ''
    pts = [(330, 130), (330, 200), (330, 270), (400, 165), (400, 235), (470, 200)]
    for a, b in [(0, 3), (0, 4), (1, 3), (1, 4), (2, 3), (2, 4), (3, 5), (4, 5)]:
        nodes += '<path d="M%d %dL%d %d" stroke="#B69AF7" stroke-opacity=".55"/>' % (pts[a][0], pts[a][1], pts[b][0], pts[b][1])
    for x, y in pts:
        nodes += '<circle cx="%d" cy="%d" r="9" fill="#101114" stroke="#D6C8FF" stroke-width="2"/>' % (x, y)
    return ('<svg viewBox="10 40 630 320" role="img" aria-label="Concept illustration: three example photographs feed a recognition model, which outputs a sign label">'
            '<title>Concept illustration of Vision-SL</title>%s'
            '<path d="M262 215h40" stroke="#D6C8FF" stroke-width="2.5" stroke-linecap="round"/><path d="M294 207l10 8-10 8" fill="none" stroke="#D6C8FF" stroke-width="2.5" stroke-linecap="round"/>'
            '%s<path d="M498 200h40" stroke="#D6C8FF" stroke-width="2.5" stroke-linecap="round"/><path d="M530 192l10 8-10 8" fill="none" stroke="#D6C8FF" stroke-width="2.5" stroke-linecap="round"/>'
            '<rect x="548" y="176" width="80" height="48" rx="24" fill="#B69AF7"/><text x="588" y="206" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="700" fill="#101114">SIGN</text>'
            '<text x="90" y="335" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="#A5A5B0">3 example photos</text>'
            '<text x="400" y="335" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" fill="#A5A5B0">prototype model</text></svg>' % (frames, nodes))


def cta_row(ctas):
    return '<div class="btn-row">%s</div>' % ''.join(
        '<a class="btn%s" href="%s">%s</a>' % (' ghost' if c.get('ghost') else '', e(c['href']), e(c['label'])) for c in ctas)


def section_head(label, heading, lede=''):
    l = '<p class="chapter-label">%s</p>' % e(label) if label else ''
    d = '<p class="lede">%s</p>' % e(lede) if lede else ''
    return '<div class="section-head reveal">%s<h2>%s</h2>%s</div>' % (l, e(heading), d)


def build_hero():
    h = cfg['hero']
    title = ''.join('<span%s>%s</span>' % (' class="accent"' if t.get('accent') else '', e(t['text'])) for t in h['title'])
    p = h['portrait']
    marquee = ('<div class="marquee reveal" aria-hidden="true"><div class="marquee-track">%s</div></div>'
               % ''.join('<span>%s</span><i>◆</i>' % e(h['marquee']) for _ in range(2)))
    return '''
<section class="hero-section" id="top">
  <div class="container hero">
    <div class="hero-copy">
      <p class="eyebrow rise">%(eyebrow)s</p>
      <h1 class="rise d1">%(title)s</h1>
      <p class="tagline rise d2">%(tagline)s</p>
      <p class="intro rise d2">%(intro)s</p>
      %(ctas)s
      <div class="rise d4 hero-social">%(social)s</div>
      <p class="scroll-hint rise d4" aria-hidden="true">Scroll to explore <i></i></p>
    </div>
    <div class="portrait-wrap fade-in"><div class="portrait">%(pic)s</div>
      <div class="portrait-chip"><b>%(cb)s</b>%(ct)s</div></div>
  </div>
  %(marquee)s
</section>''' % dict(eyebrow=h['eyebrow'], title=title, tagline=e(h['tagline']), intro=e(h['intro']),
                    ctas=cta_row(h['ctas']), social=social_links(), pic=picture(p['src'], p['alt'], '(min-width:1024px) 420px, 78vw', 0, eager=True),
                    cb=e(p['chip_bold']), ct=e(p['chip_text']), marquee=marquee)


def build_about():
    ident = cfg['identity']
    pillars = ''.join('<a class="pillar reveal" href="%s"><span class="num">%s</span><h3>%s</h3><p>%s</p><span class="go">%s %s</span></a>'
                      % (e(p['href']), e(p['num']), e(p['title']), e(p['text']), e(p['go']), ICON['arrow']) for p in ident['pillars'])
    ab = cfg['about']
    story = ''.join('<p>%s</p>' % e(x) for x in ab['story'])
    j = cfg['journey']
    steps = ''.join('<li class="reveal"><span class="when">%s</span><h3>%s</h3><p>%s</p></li>' % (e(s['when']), e(s['title']), e(s['text'])) for s in j['steps'])
    sk = cfg['skills']
    skg = ''.join('<div class="card reveal"><h3>%s</h3><ul class="tag-list">%s</ul></div>' % (e(g['title']), ''.join('<li>%s</li>' % e(i) for i in g['items'])) for g in sk['groups'])
    ed = cfg['education']
    edc = ''.join('<div class="card reveal">%s<h3>%s</h3><p class="muted">%s</p></div>'
                  % (('<span class="status">%s</span>' % e(x['status'])) if x['status'] else '', e(x['title']), e(x['place'])) for x in ed['items'])
    le = cfg['learning']
    learn = ''
    for it in le['items']:
        right = e(it['date']) if it['date'] else 'Details added as credentials are verified'
        if it['link']:
            right += ' &middot; <a href="%s" rel="noopener" target="_blank">View credential</a>' % e(it['link'])
        learn += '<li class="reveal"><div><b>%s</b><small>%s</small></div><div class="muted">%s</div></li>' % (e(it['title']), e(it['provider']), right)
    ph = cfg['philosophy']
    return '''
<section class="section" id="about">
  <div class="container">
    %(identity_head)s
    <div class="two-col">
      <div class="pillars">%(pillars)s</div>
      <div class="prose about-story reveal"><h3>%(story_head)s</h3>%(story)s</div>
    </div>
  </div>
</section>

<section class="section alt" id="journey">
  <div class="container">
    %(journey_head)s
    <ol class="timeline">%(steps)s</ol>
  </div>
</section>

<section class="section" id="skills">
  <div class="container">
    %(skills_head)s
    <div class="skill-grid">%(skg)s</div>
  </div>
</section>

<section class="section alt" id="education">
  <div class="container">
    %(edu_head)s
    <div class="grid cols-3">%(edc)s</div>
  </div>
</section>

<section class="section" id="learning">
  <div class="container">
    %(learn_head)s
    <ul class="learning">%(learn)s</ul>
  </div>
</section>

<section class="section alt"><div class="container narrow reveal">
  <p class="eyebrow">%(ph_label)s</p>
  <p class="pull">%(ph_quote)s</p>
  %(ph_ctas)s
</div></section>''' % dict(
        identity_head=section_head(ident['label'], ident['heading'], ident['lede']),
        pillars=pillars, story_head=e(ab['story_heading']), story=story,
        journey_head=section_head(j['label'], j['heading'], j['lede']), steps=steps,
        skills_head=section_head(sk['label'], sk['heading']), skg=skg,
        edu_head=section_head(ed['label'], ed['heading']), edc=edc,
        learn_head=section_head(le['label'], le['heading'], le['lede']), learn=learn,
        ph_label=e(ph['label']), ph_quote=ph['quote'], ph_ctas=cta_row(ph['ctas']))


def build_work():
    w = cfg['work']
    f = w['flagship']
    tags = ''.join('<li>%s</li>' % e(t) for t in f['tags'])
    obj = ''.join('<li>%s</li>' % e(o) for o in f['objectives'])
    proc = ''.join('<li>%s</li>' % e(p) for p in f['process'])
    ev = ''.join('<div class="placeholder reveal"><strong>%s</strong>%s <span class="status">In preparation</span></div>' % (e(x['title']), e(x['text'])) for x in f['evidence'])
    cards = ''
    for p in w['projects']:
        cards += ('<article class="card reveal">%s<h3>%s</h3><p>%s</p><p class="muted"><b>Technologies:</b> %s</p>'
                  '<p class="muted"><b>Problem:</b> %s</p><p class="muted"><b>Approach:</b> %s</p><p class="muted"><b>Results:</b> %s</p>%s</article>'
                  % (('<span class="status">%s</span>' % e(p.get('category', ''))) if p.get('category') else '', e(p['title']), e(p.get('description', '')),
                     e(', '.join(p.get('technologies', []))), e(p.get('problem', '')), e(p.get('approach', '')), e(p.get('results', '')),
                     ''.join('<a class="btn ghost" href="%s" rel="noopener">%s</a> ' % (e(l['url']), e(l['label'])) for l in p.get('links', []))))
    if not cards:
        cards = '<div class="placeholder reveal">%s</div>' % w['empty']
    contribution = ''.join('<p>%s</p>' % x for x in f['contribution'])
    return '''
<section class="section" id="work">
  <div class="container">
    <div class="section-head reveal"><p class="chapter-label">%(label)s</p><h2>%(heading)s</h2><p class="lede">%(lede)s</p></div>
    <div class="two-col flagship">
      <div class="reveal">
        <span class="status">%(status)s</span>
        <h3 class="flagship-title">%(title)s</h3>
        <p class="lede">%(flede)s</p>
        <ul class="tag-list" style="margin-top:1.2rem">%(tags)s</ul>
      </div>
      <div class="feature reveal"><div class="visual">%(vis)s</div></div>
    </div>
  </div>
</section>

<section class="section alt"><div class="container grid cols-2">
  <div class="reveal"><p class="eyebrow">%(plabel)s</p><h2>%(pheading)s</h2><p>%(problem)s</p></div>
  <div class="reveal"><p class="eyebrow">%(olabel)s</p><h2>%(oheading)s</h2><ul class="checks">%(obj)s</ul></div>
</div></section>

<section class="section"><div class="container grid cols-2">
  <div class="reveal"><p class="eyebrow">%(prlabel)s</p><h2>%(prheading)s</h2><ol class="steps">%(proc)s</ol></div>
  <div class="reveal"><p class="eyebrow">%(clabel)s</p><h2>%(cheading)s</h2>%(contribution)s</div>
</div></section>

<section class="section alt" id="evidence"><div class="container">
  %(evhead)s
  <div class="grid cols-3">%(ev)s</div>
</div></section>

<section class="section" id="more"><div class="container">
  %(morehead)s
  <div class="grid cols-2">%(cards)s</div>
</div></section>''' % dict(
        label=e(w['label']), heading=e(w['heading']), lede=e(w['lede']),
        status=e(f['status']), title=e(f['title']), flede=e(f['lede']), tags=tags, vis=vision_svg(),
        plabel=e(f['problem_label']), pheading=e(f['problem_heading']), problem=e(f['problem']),
        olabel=e(f['objectives_label']), oheading=e(f['objectives_heading']), obj=obj,
        prlabel=e(f['process_label']), prheading=e(f['process_heading']), proc=proc,
        clabel=e(f['contribution_label']), cheading=e(f['contribution_heading']), contribution=contribution,
        evhead=section_head(f['evidence_label'], f['evidence_heading'], f['evidence_lede']), ev=ev,
        morehead=section_head(w['more_label'], w['more_heading']), cards=cards)


def build_community():
    c = cfg['community']
    blocks = ''.join('<div class="reveal"><p class="eyebrow">%s</p><h3>%s</h3><p>%s</p></div>' % (e(b['label']), e(b['heading']), e(b['text'])) for b in c['blocks'])
    tl = ''.join('<details class="tl reveal"><summary><span>%s</span><span class="status">%s</span></summary><div class="more">%s</div></details>'
                 % (e(it['title']), e(it['when']), e(it['detail'])) for it in c['timeline'])
    mt = ''.join('<div class="card metric reveal"><strong>&ndash;</strong><span>%s</span></div>' % e(m) for m in c['metrics'])
    return '''
<section class="section" id="community">
  <div class="container">
    <div class="section-head reveal"><p class="chapter-label">%(label)s</p><h2>%(heading)s</h2><p class="lede">%(lede)s</p></div>
    <div class="grid cols-2" style="align-items:start">
      <div class="reveal"><p class="eyebrow">Leadership</p><h3>%(lh)s</h3><p class="lede">%(ls)s</p><p>%(lt)s</p></div>
      <div class="reveal"><p class="pull" style="font-size:clamp(1.4rem,2.6vw,2rem)">%(lq)s</p>
        <div class="placeholder" style="margin-top:1.6rem"><strong>Chapter initiatives and outcomes</strong>Objectives, initiatives, events, programmes and student engagement are published here as they are confirmed, with measurable outcomes added only when they can be verified.</div></div>
    </div>
  </div>
</section>

<section class="section alt"><div class="container grid cols-2" style="align-items:start">%(blocks)s</div></section>

<section class="section" id="timeline"><div class="container narrow">
  %(tlhead)s
  <div class="stack">%(tl)s</div>
</div></section>

<section class="section alt" id="impact"><div class="container">
  %(imhead)s
  <div class="grid cols-3">%(mt)s</div>
</div></section>''' % dict(
        label=e(c['label']), heading=e(c['heading']), lede=e(c['lede']),
        lh=e(c['leadership_heading']), ls=e(c['leadership_sub']), lt=e(c['leadership_text']), lq=c['leadership_quote'],
        blocks=blocks, tlhead=section_head(c['timeline_label'], c['timeline_heading'], c['timeline_lede']), tl=tl,
        imhead=section_head(c['impact_label'], c['impact_heading'], c['impact_lede']), mt=mt)


def build_media():
    m = cfg['media']
    chips = ''.join('<button type="button" class="chip" data-collection-filter="%s" aria-pressed="false">%s</button>' % (e(x), e(x)) for x in m['collections'])
    figs = ''
    for it in m['items']:
        credit = it.get('credit', '').strip()
        figs += ('<figure data-collection="%s" class="reveal"><button type="button" data-large="assets/images/%s-1400.webp" data-alt="%s" aria-label="Enlarge photo: %s">'
                 '<img src="assets/images/%s-600.webp" srcset="assets/images/%s-600.webp 600w, assets/images/%s-1000.webp 1000w" sizes="(min-width:900px) 380px, 90vw" alt="%s" width="600" height="%d" loading="lazy" decoding="async"></button>'
                 '<figcaption><b>%s</b><br>%s &middot; <span>%s</span>%s</figcaption></figure>'
                 % (e(it['collection']), it['src'], e(it['alt']), e(it['title']), it['src'], it['src'], it['src'], e(it['alt']),
                    round(600 * it['height'] / it['width']), e(it['title']), e(it['caption']), e(it['date']),
                    (' &middot; Photo: %s' % e(credit)) if credit else ''))
    feat_item = next((x for x in m['items'] if x['src'] == m['featured']), m['items'][0] if m['items'] else None)
    feat = ''
    if feat_item:
        feat = '<div class="photo-frame">%s</div>' % picture(feat_item['src'], feat_item['alt'], '(min-width:900px) 420px, 90vw', 0, width=feat_item['width'], height=feat_item['height'])
    v = m['videos_placeholder']
    return '''
<section class="section" id="media">
  <div class="container">
    <div class="section-head reveal"><p class="chapter-label">%(label)s</p><h2>%(heading)s</h2><p class="lede">%(lede)s</p></div>
    <div class="two-col media-featured">
      <div class="reveal"><p class="eyebrow">Featured</p><h3>%(fh)s</h3><p class="lede">%(fl)s</p></div>
      <div style="max-width:420px;justify-self:center">%(feat)s</div>
    </div>
  </div>
</section>

<section class="section alt" id="photos"><div class="container">
  %(ghead)s
  <div class="chips" role="group" aria-label="Filter photos by collection" style="margin-bottom:28px">
    <button type="button" class="chip" data-collection-filter="" aria-pressed="true">All</button>%(chips)s</div>
  <div class="gallery" id="gallery">%(figs)s</div>
  <p class="empty" id="gallery-empty" hidden>Nothing in this collection yet. Photographs are added as they are approved.</p>
</div></section>

<section class="section" id="videos"><div class="container">
  %(vhead)s
  <div class="grid cols-2"><div class="video-card reveal"><div><strong>%(vt)s</strong><br>%(vx)s<br><span class="status">%(vs)s</span></div></div></div>
</div></section>

<section class="section alt" id="press"><div class="container">
  %(phead)s
  <div class="placeholder reveal">%(pe)s</div>
</div></section>

<dialog class="lightbox" id="lightbox" aria-label="Photo viewer">
  <button type="button" class="icon-btn close" aria-label="Close photo viewer">%(close)s</button>
  <figure><img src="" alt="" width="900" height="1300"><figcaption></figcaption></figure>
  <div class="btn-row" style="justify-content:center"><button type="button" class="btn ghost" data-prev>&larr; Previous</button><button type="button" class="btn ghost" data-next>Next &rarr;</button></div>
</dialog>''' % dict(
        label=e(m['label']), heading=e(m['heading']), lede=e(m['lede']),
        fh=e(m['featured_heading']), fl=e(m['featured_lede']), feat=feat,
        ghead=section_head(m['gallery_label'], m['gallery_heading']), chips=chips, figs=figs,
        vhead=section_head(m['videos_label'], m['videos_heading']), vt=e(v['title']), vx=e(v['text']), vs=e(v['status']),
        phead=section_head(m['press_label'], m['press_heading']), pe=m['press_empty'], close=ICON['close'])


def build_blog_teaser():
    b = cfg['blog']
    return '''
<section class="section" id="blog"><div class="container">
  <div class="section-head reveal"><p class="chapter-label">%(label)s</p><h2>%(heading)s</h2><p class="lede">%(lede)s</p></div>
  <div class="blog-teaser reveal">
    <div class="blog-teaser-copy"><p class="muted">%(empty)s</p>
      <div class="btn-row"><a class="btn" href="%(url)s">Visit the blog</a><a class="btn ghost" href="%(url)sindex.html#feed">Subscribe via RSS</a></div>
    </div>
  </div>
</div></section>''' % dict(label=e(b['label']), heading=e(b['heading']), lede=e(b['lede']), empty=e(b['empty']), url=e(b['url']))


def build_contact():
    c = cfg['contact']
    s = cfg['site']
    contacts = ''
    if s['email']:
        contacts += '<li><a href="mailto:%s">%s<span>%s</span></a></li>' % (e(s['email']), ICON['mail'], e(s['email']))
    if s['linkedin']:
        contacts += '<li><a href="%s" rel="me noopener" target="_blank">%s<span>LinkedIn</span></a></li>' % (e(s['linkedin']), ICON['linkedin'])
    if s['github']:
        contacts += '<li><a href="%s" rel="me noopener" target="_blank">%s<span>GitHub</span></a></li>' % (e(s['github']), ICON['github'])
    interests = ''.join('<li>%s</li>' % e(i) for i in c['interests'])
    return '''
<section class="section alt" id="contact"><div class="container">
  <div class="section-head reveal"><p class="chapter-label">%(label)s</p><h2>%(heading)s</h2><p class="lede">%(lede)s</p></div>
  <div class="contact-grid">
    <div class="reveal">
      %(contacts_block)s
      <h3 style="font-size:1.3rem">Open to</h3>
      <ul class="checks">%(interests)s</ul>
    </div>
    <form class="form reveal" id="contact-form" novalidate data-endpoint="%(endpoint)s" data-mailto="%(mailto)s" aria-label="Contact form">
      <div class="field"><label for="name">Name</label><input id="name" name="name" type="text" autocomplete="name" required aria-describedby="e-name"><p class="err" id="e-name">Please enter your name.</p></div>
      <div class="field"><label for="email">Email address</label><input id="email" name="email" type="email" autocomplete="email" required aria-describedby="e-email"><p class="err" id="e-email">Please enter a valid email address.</p></div>
      <div class="field"><label for="organisation">Organisation <span class="opt">(optional)</span></label><input id="organisation" name="organisation" type="text" autocomplete="organization"></div>
      <div class="field"><label for="subject">Subject</label><input id="subject" name="subject" type="text" required aria-describedby="e-subject"><p class="err" id="e-subject">Please add a subject.</p></div>
      <div class="field"><label for="message">Message</label><textarea id="message" name="message" required aria-describedby="e-message"></textarea><p class="err" id="e-message">Please write a message of at least 10 characters.</p></div>
      <div class="hp" aria-hidden="true"><label>Leave this empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
      <button class="btn" type="submit">Send message</button>
      <div class="form-status" id="form-status" role="status" aria-live="polite"></div>
    </form>
  </div>
</div></section>
<section class="section"><div class="container narrow reveal" style="text-align:center">
  <p class="pull">%(quote)s</p>
</div></section>''' % dict(label=e(c['label']), heading=e(c['heading']), lede=e(c['lede']), quote=c['quote'],
                           contacts_block=('<ul class="contact-list">%s</ul>' % contacts) if contacts else '',
                           interests=interests, endpoint=e(s['form_endpoint']), mailto=e(s['email']))


def build_index():
    s = cfg['site']
    body = (build_hero() + build_about() + build_work() + build_community() + build_media() + build_blog_teaser() + build_contact())
    page = '''<!doctype html>
<html lang="en">
<head>
%(head)s
</head>
<body class="home">
%(circuit)s
<a class="skip" href="#main">Skip to content</a>
%(header)s
<main id="main">
%(body)s
</main>
%(footer)s
<noscript><style>.reveal{opacity:1!important;transform:none!important}</style></noscript>
<script src="js/site.js" defer></script>
</body>
</html>
''' % dict(circuit=circuit_bg(), head=head(s['meta_title'], s['meta_description'], abs_url(''), '', jsonld=person_ld()),
           header=site_header(), body=body, footer=site_footer())
    write('index.html', page)
    PAGES.append('')


def build_404():
    body = '''<section class="notfound"><div class="container"><p class="eyebrow">404</p><h1>This page wandered off.</h1><p class="lede" style="margin-inline:auto">The page you are looking for does not exist or has moved.</p><div class="btn-row" style="justify-content:center"><a class="btn" href="%(site)s/">Back to home</a><a class="btn ghost" href="%(site)s/blogs/">Visit the blog</a></div></div></section>''' % dict(site=SITE)
    page = '''<!doctype html>
<html lang="en">
<head>
%(head)s
</head>
<body>
%(circuit)s
<a class="skip" href="#main">Skip to content</a>
%(header)s
<main id="main">%(body)s</main>
%(footer)s
</body>
</html>
''' % dict(circuit=circuit_bg(), head=head('Page not found | %s' % NAME, 'Page not found.', abs_url('404.html'), SITE + '/'),
           header=site_header(), body=body, footer=site_footer(SITE + '/'))
    write('404.html', page)


# ---------------------------------------------------------------- blog pages
def blog_chrome(active, depth):
    r = rel(depth)
    home = r + 'index.html'

    def nav_href(href):
        return (home + href) if href.startswith('#') else (r + href)
    nav = ''.join('<li><a href="%s"%s>%s</a></li>' % (e(nav_href(i['href'])), ' aria-current="page"' if i['label'] == active else '', e(i['label']))
                  for i in cfg['nav'])
    return ('<header class="site-header"><div class="inner">'
            '<a class="brand" href="%s" aria-label="Felicia Chuma, home"><span class="mark" aria-hidden="true">FC</span><span class="name">%s</span></a>'
            '<nav class="nav" id="site-nav" aria-label="Main navigation"><ul>%s</ul></nav>'
            '<div class="header-tools">%s'
            '<button type="button" class="icon-btn menu-btn" id="menu-btn" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">%s</button>'
            '</div></div></header><div class="progress-bar" id="progress-bar" aria-hidden="true"></div>'
            % (home, e(NAME), nav, social_links('social hide-sm'), ICON['menu']))


def post_card(p, depth):
    r = rel(depth)
    return ('<li data-tags="%s"><a class="post-card reveal" href="%s" hreflang="en"><div class="cover"><img src="%s%s" alt="Cover graphic for %s" width="1200" height="630" loading="lazy" decoding="async"></div>'
            '<div class="body"><div class="meta"><time datetime="%s">%s</time><span>%d min read</span></div>'
            '<h3>%s</h3><p>%s</p><span class="read">Read post %s</span></div></a></li>'
            % (e(' '.join(p['tags'])), p['href'], r, p['cover'], e(p['title']), p['date'].isoformat(), pretty_date(p['date']), p['minutes'],
               e(p['title']), e(p['description']), ICON['arrow']))


def blog_page_href(n):
    return 'index.html' if n == 1 else 'page%d.html' % n


def build_blog(posts):
    tag_options = sorted({t for p in posts for t in p['tags']})
    for p in posts:
        write(p['cover'], cover_svg(p['slug']))
    # ---- post pages
    for i, p in enumerate(posts):
        older = posts[i - 1] if i > 0 else None
        newer = posts[i + 1] if i + 1 < len(posts) else None
        tags = ''.join('<li>#%s</li>' % e(t) for t in p['tags'])
        pager = '<div class="post-pager">'
        pager += ('<a class="pager-link" href="%s"><span class="mono">&larr; Older</span><strong>%s</strong></a>' % (older['href'], e(older['title']))) if older else '<span></span>'
        pager += ('<a class="pager-link next" href="%s"><span class="mono">Newer &rarr;</span><strong>%s</strong></a>' % (newer['href'], e(newer['title']))) if newer else '<span></span>'
        pager += '</div>'
        li = 'https://www.linkedin.com/sharing/share-offsite/?url=' + p['url']
        head_html = '''<section class="page-hero"><div class="container">
  <p class="crumbs"><a href="../index.html">Home</a> / <a href="index.html">Blog</a></p>
  <h1 class="rise d1">%(title)s</h1>
  <p class="lede rise d2">%(desc)s</p>
  <p class="muted post-meta">By Felicia Chuma &middot; <time datetime="%(iso)s">%(date)s</time> &middot; %(min)d min read</p>
</div></section>''' % dict(title=e(p['title']), desc=e(p['description']), iso=p['date'].isoformat(), date=pretty_date(p['date']), min=p['minutes'])
        body = ('<article>' + head_html +
                '<div class="narrow"><figure class="cover-fig"><img src="../%s" alt="" width="1200" height="630" fetchpriority="high"></figure></div>'
                '<div class="narrow"><div class="prose" id="article-body">%s</div>'
                '<div class="article-foot"><ul class="tag-list" aria-label="Tags">%s</ul>'
                '<div class="btn-row"><a class="btn" href="%s" target="_blank" rel="noopener">Share on LinkedIn</a><a class="btn ghost" href="index.html">All posts</a></div>'
                '%s</div></div></article>' % (p['cover'], p['content'], tags, e(li), pager))
        ld = {'@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': p['title'], 'description': p['description'],
              'datePublished': p['date'].isoformat(), 'dateModified': p['date'].isoformat(),
              'author': {'@type': 'Person', 'name': NAME, 'url': abs_url('')}, 'image': abs_url(p['cover']),
              'mainEntityOfPage': p['url'], 'keywords': ', '.join(p['tags']), 'wordCount': p['words']}
        page = '''<!doctype html>
<html lang="en">
<head>
%(head)s
</head>
<body class="blog-post">
%(circuit)s
<a class="skip" href="#main">Skip to content</a>
%(header)s
<main id="main">
%(body)s
</main>
%(footer)s
<script src="%(r)sjs/site.js" defer></script>
</body>
</html>
''' % dict(circuit=circuit_bg(), head=head('%s | %s' % (p['title'], NAME), p['description'], p['url'], '../', og_type='article', jsonld=ld), header=blog_chrome('Blogs', 1), body=body, footer=site_footer('../'), r='../')
        write('blogs/%s' % p['href'], page)

    # ---- index pages
    newest_first = list(reversed(posts))
    chunks = [newest_first[i:i + PER_PAGE] for i in range(0, len(newest_first), PER_PAGE)] or [[]]
    total = len(chunks)
    for n, chunk in enumerate(chunks, start=1):
        cards = ''.join(post_card(p, 1) for p in chunk)
        all_cards = ''.join(post_card(p, 1) for p in newest_first)
        if not posts:
            listing = '<div class="empty">%s</div>' % e(cfg['blog']['empty'])
            pager = ''
        else:
            listing = '<ul class="post-list" id="post-list">%s</ul><template id="all-posts">%s</template>' % (cards, all_cards)
            pager = ''
            if total > 1:
                nums = ''.join(('<span class="pager-page" aria-current="page">%d</span>' % i) if i == n else ('<a class="pager-page" href="%s">%d</a>' % (blog_page_href(i), i)) for i in range(1, total + 1))
                pager = '<nav class="index-pager">%s<span class="pager-pages mono">%s</span>%s</nav>' % (
                    ('<a class="pager-btn" href="%s">&larr; Newer</a>' % blog_page_href(n - 1)) if n > 1 else '<span></span>',
                    nums,
                    ('<a class="pager-btn next" href="%s">Older &rarr;</a>' % blog_page_href(n + 1)) if n < total else '<span></span>')
        filter_row = ''
        if tag_options:
            opts = ''.join('<option value="%s">%s</option>' % (e(t), e(t)) for t in tag_options)
            filter_row = ('<div class="tag-filter-row"><label class="mono" for="tag-filter">Filter by tag</label>'
                          '<select id="tag-filter" class="mono"><option value="">All posts</option>%s</select></div>'
                          '<p class="filter-note mono" id="filter-note" hidden></p>' % opts)
        title = ('Writing | %s' % NAME) if n == 1 else ('Writing, page %d | %s' % (n, NAME))
        body = '''<section class="page-hero"><div class="container">
  <p class="eyebrow rise">Blog</p>
  <h1 class="rise d1">%(heading)s</h1>
  <p class="lede rise d2">%(lede)s</p>
</div></section>
<section class="section"><div class="container">
  %(filter)s
  %(listing)s
  %(pager)s
  <p id="feed" class="muted" style="margin-top:2rem"><a href="../feed.xml">RSS feed</a></p>
</div></section>''' % dict(heading=e(cfg['blog']['heading']), lede=e(cfg['blog']['lede']), filter=filter_row, listing=listing, pager=pager)
        ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'Writing', 'url': abs_url('blogs/'), 'author': {'@type': 'Person', 'name': NAME},
              'description': cfg['blog']['lede']}
        page = '''<!doctype html>
<html lang="en">
<head>
%(head)s
</head>
<body class="page-blog">
%(circuit)s
<a class="skip" href="#main">Skip to content</a>
%(header)s
<main id="main">
%(body)s
</main>
%(footer)s
<script src="%(_r)sjs/site.js" defer></script>
<script src="%(_r)sjs/blog.js" defer></script>
</body>
</html>
''' % dict(circuit=circuit_bg(), head=head(title, cfg['blog']['lede'], abs_url('blogs/') if n == 1 else abs_url('blogs/%s' % blog_page_href(n)), '../', jsonld=ld),
           header=blog_chrome('Blogs', 1), body=body, footer=site_footer('../'), _r='../')
        write('blogs/%s' % blog_page_href(n), page)
    # drop stale pages
    for name in os.listdir(BLOG_OUT) if os.path.isdir(BLOG_OUT) else []:
        m = re.fullmatch(r'page(\d+)\.html', name)
        if m and int(m.group(1)) > total:
            os.remove(os.path.join(BLOG_OUT, name))
    PAGES.append('blogs/')
    for n in range(2, total + 1):
        PAGES.append('blogs/%s' % blog_page_href(n))
    for p in newest_first:
        PAGES.append('blogs/%s' % p['href'])
    return posts


def build_feed(posts):
    def rfc822(d):
        return format_datetime(dt(d.year, d.month, d.day, tzinfo=timezone.utc))
    items = []
    for p in list(reversed(posts))[:20]:
        abs_content = re.sub(r'(href|src)="([^"]+)"', lambda m: '%s="%s"' % (m.group(1), urljoin(p['url'], m.group(2))), p['content'])
        tags = ''.join('<category>%s</category>' % e(t) for t in p['tags'])
        items.append('<item><title>%s</title><link>%s</link><guid isPermaLink="true">%s</guid><pubDate>%s</pubDate>'
                     '<description>%s</description><content:encoded>%s</content:encoded>%s</item>'
                     % (e(p['title']), p['url'], p['url'], rfc822(p['date']), e(p['description']), e(abs_content), tags))
    last = rfc822(posts[-1]['date']) if posts else rfc822(TODAY)
    write('feed.xml', ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n'
            '<channel><title>%s</title><link>%s/blogs/</link><description>%s</description><language>en</language>'
            '<lastBuildDate>%s</lastBuildDate><atom:link href="%s/feed.xml" rel="self" type="application/rss+xml"/>%s</channel>\n</rss>\n'
            % (e(cfg['blog']['feed_title']), SITE, e(cfg['blog']['lede']), last, SITE, ''.join(items))))


# ---------------------------------------------------------------- sitemap
def build_sitemap():
    urls = ''
    for path in PAGES:
        pr = '1.0' if path == '' else '0.8' if path.startswith('blogs/') else '0.6'
        urls += '  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n' % (abs_url(path), TODAY.isoformat(), pr)
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % urls)


def build_robots():
    write('robots.txt', 'User-agent: *\nAllow: /\nDisallow: /_content/\nDisallow: /_tools/\n\nSitemap: %s/sitemap.xml\n' % SITE)


def build_favicon():
    write('assets/icons/favicon.svg', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#101114"/><circle cx="32" cy="32" r="22" fill="none" stroke="#B69AF7" stroke-width="2.5"/><text x="32" y="40" text-anchor="middle" font-family="Georgia,serif" font-size="22" font-weight="700" fill="#B69AF7">FC</text></svg>')


# ---------------------------------------------------------------- run
PAGES = []
POSTS = load_posts()
build_index()
build_blog(POSTS)
build_404()
build_feed(POSTS)
build_sitemap()
build_robots()
build_favicon()

print('Built single-page portfolio + %d blog post(s). Site URL: %s' % (len(POSTS), SITE))
missing = [k for k in ('email', 'linkedin', 'github') if not cfg['site'][k]]
if 'YOUR-DOMAIN' in cfg['site']['url'] or missing or not cfg['site']['form_endpoint']:
    print('NOTE: still to configure ->', ', '.join(
        (['site_url'] if 'YOUR-DOMAIN' in cfg['site']['url'] else []) + missing + ([] if cfg['site']['form_endpoint'] else ['form_endpoint (optional)'])))
