# Felicia Chuma: portfolio website

A static website. The whole portfolio is one page (`index.html`) with anchored
sections; the blog lives in `blogs/` as individual pages. No framework or server
is needed. Upload this folder to any static host (GitHub Pages, Netlify,
Cloudflare Pages).

```
_content/content.json   all editable text and lists for the whole site
_content/blog/*.md      blog posts (Markdown + front matter)
_tools/build.py         the builder (Python 3, standard library only)
css/site.css            styles
js/site.js, js/blog.js  behaviour
```

## 1. Set your details (once)
Run from this folder (needs Python 3):

    python3 _tools/build.py \
      --site-url https://YOUR-REAL-ADDRESS \
      --email you@example.com \
      --linkedin https://www.linkedin.com/in/your-profile \
      --github https://github.com/your-username \
      --form-endpoint https://formspree.io/f/xxxxxxxx

* `--site-url` fills canonical links, social previews, `feed.xml` and `sitemap.xml` (important for SEO).
* `--form-endpoint` (optional) is a Formspree-style address so the contact form sends without opening an email app. Without it the form opens the visitor's email app addressed to `--email`.
* Settings are saved back into `_content/content.json`; re-run `python3 _tools/build.py` any time to regenerate the site.

## 2. Publish
GitHub Pages: create a repository, upload everything in this folder, then Settings → Pages → deploy from the main branch. Afterwards submit `sitemap.xml` in Google Search Console.

## Updating content (then run `python3 _tools/build.py`)
* **Anything on the portfolio page**: hero, about, journey, skills, education, learning, work, community, media and contact all live in `_content/content.json`. Edit the text there and rebuild; no HTML editing required.
* **A blog post**: copy `_content/blog/_post-template.md`, rename it to the URL
  slug you want (lowercase-with-hyphens), fill in the front matter (`title` and
  `date` are required) and write the article in Markdown. The post page, cover
  graphic, blog index, RSS feed and sitemap update on rebuild. Files starting
  with `_` are ignored by the builder.
* **A photo**: run `python3 _tools/optimise-image.py photo.jpg short-name`, move
  the generated files into `assets/images/`, then add an entry to the
  `media.items` list in `_content/content.json`.
* **A project**: add an entry to the `work.projects` list in `_content/content.json`.

## What the build produces
`index.html`, `blogs/index.html` (plus `page2.html` and so on once there are
more than six posts), one page per post, `404.html`, `feed.xml`, `sitemap.xml`,
`robots.txt` and the favicon.

## Notes
* Motion is progressive: reveals, load-in animations, the marquee and the
  circuit pulse all respect `prefers-reduced-motion`. The site is fully
  readable with JavaScript off.
* `_tools/` and `_content/` are build sources; `robots.txt` asks search engines to skip them.
