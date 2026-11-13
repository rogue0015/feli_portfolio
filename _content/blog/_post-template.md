---
title: Your post title goes here
description: One clear sentence summarising the article. It is used on cards, in search results and in the RSS feed.
date: 2026-01-01
tags: [Data Science, Learning]
---

Write the article below the closing `---`. Standard Markdown is supported:
headings, **bold**, *italic*, `inline code`, links, images, lists, quotes
and fenced code blocks.

## A section heading

Open with the point you want to make, then support it.

> Use a blockquote for a definition, a quotation or a key takeaway.

### A smaller heading

- Keep one idea per list item.
- Bullet lists and numbered lists are both supported.

1. First step.
2. Second step.

```python
# Fenced code blocks are rendered verbatim.
print("Hello, world")
```

## How to publish

1. Duplicate this file and rename it to the URL slug you want, in lowercase
   with hyphens, for example `why-data-cleaning-matters.md`.
2. Fill in the front matter. `title` and `date` (YYYY-MM-DD) are required.
3. Run `python3 _tools/build.py`. The post page, its cover graphic, the blog
   index, the RSS feed and the sitemap update automatically.
