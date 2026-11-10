# pdf-book-exporter

Export a [Hugo](https://gohugo.io) book — a directory of page bundles with YAML
front matter — to a print-quality PDF.

The pipeline is deliberately short: **Markdown → Pandoc → Typst → PDF**. A
1,000-page book compiles in well under ten seconds. No LaTeX, no browser, no
image conversion step.

- Chapters ordered by `weight`, nested sub-chapters, optional *parts* from the
  book's `_index.md`, and an appendix part with `A`, `A.1`, `图 A-1` numbering
- Hugo shortcodes mapped to print equivalents (`callout`, `table`, `figure`,
  `details`, `inline-codes`, `youtube`/`bilibili`); web-only ones removed
- SVG, PNG, JPEG, GIF and WebP images embedded natively; remote images
  downloaded once and cached under `~/.cache/pdf-book-exporter/`
- Cover and back-cover images (local file, URL, or discovered from the Hugo
  site), optional title overlay, colophon page, table of contents with page
  numbers, PDF outline, running headers
- Syntax-highlighted code blocks (Typst built-in), zebra tables that break
  across pages, callouts, task lists, footnotes, math
- Chinese and English typography presets; colour emoji through system fonts

![Pages from the example book](example/example-screenshot.jpg)

## Install

Requirements: Python ≥ 3.10, [Pandoc](https://pandoc.org) ≥ 3.1.7 and
[Typst](https://typst.app) ≥ 0.13.

```bash
brew install pandoc typst            # macOS
uv tool install git+https://github.com/rootsongjc/pdf-book-exporter
pdf-book-exporter --check
```

Fonts: the Chinese preset looks for *Noto Sans CJK SC* (or *Source Han Sans*,
*PingFang SC*), the English preset for *Noto Sans*; code uses *JetBrains
Mono* or *Menlo*. Typst falls back per glyph, so missing families only produce
a warning. Override with `--font` / `--monofont` or `book.font` in front
matter, and point Typst at extra font directories with `--font-path`.

## Usage

```bash
pdf-book-exporter content/zh/book/my-book                    # -> ./my-book-zh.pdf
pdf-book-exporter content/en/book/my-book -o dist/book.pdf
pdf-book-exporter content/zh/book/my-book --cover cover.jpg --backcover back.jpg
pdf-book-exporter content/zh/book/my-book --keep -v           # keep body.md / body.typ for debugging
```

| Flag | Purpose |
|------|---------|
| `-o, --output` | Output path (default `./<book>-<lang>.pdf`) |
| `--cover`, `--backcover` | Image path or URL; overrides front matter and site lookup |
| `--no-cover` | Skip the cover even if one is found |
| `--font`, `--monofont` | Comma-separated font families, in fallback order |
| `--font-path DIR` | Extra font directory for Typst (repeatable) |
| `--include-drafts` | Include pages with `draft: true` |
| `--offline` | Never download; use cached remote images only |
| `--keep`, `--workdir DIR` | Keep the intermediate Markdown and Typst files |
| `--check` | Verify that pandoc and typst are installed |

## Book layout

```text
my-book/
├── _index.md            # book metadata (title, authors, parts, book: {...})
├── cover.jpg            # optional, referenced from book.cover
├── chapter-a/
│   └── index.md         # title, weight, part_id, draft, export_pdf
└── chapter-b/
    ├── _index.md        # chapter intro
    └── section/
        └── index.md     # sub-chapter (one level of nesting)
```

Pages with `draft: true` (unless `--include-drafts`), `export_pdf: false`
or `status: offline` are skipped. Headings inside a page are re-levelled so
the smallest one sits directly under the chapter title; Hugo's "start at
`##`" convention therefore needs no special handling.

### Cover lookup

The first match wins:

1. `--cover` on the command line
2. `book.cover` (or top-level `cover`) in `_index.md` — a path relative to the
   book directory or an `http(s)` URL
3. `cover-<lang>.{webp,jpg,jpeg,png}` or `cover.*` inside the book directory
4. In a Hugo site (a parent directory with `hugo.toml`/`config/` and
   `content/`): `static/images/book-covers/<slug>.webp`, then the URL under
   `<slug>` in `data/<lang>/book_covers.yaml`

Generated covers usually already carry the title, so the text overlay is off
unless `cover_overlay_enabled: true` is set. Back covers follow the same rules
with `backcover*` / `back-cover*` names (no site lookup).

### `_index.md` front matter

Top-level Hugo fields are used as-is; the optional `book:` block overrides them
and carries PDF-only settings.

```yaml
title: AI 原生基础设施
authors: [Jimmy Song]
publisher: jimmysong.io
description: 一段用于版权页的简介
parts:
  - { id: part-i, title: "Part I · 定义", order: 1 }
  - { id: part-appendix, title: 附录，order: 2 }   # id/title matching appendix|附录 → A, B, ...
book:
  language: zh-hans            # inferred from the path (/zh/, /en/) when omitted
  website: https://jimmysong.io/book/ai-native-infra
  cover: cover.jpg             # path relative to the book directory, or a URL
  backcover: back-cover.jpg
  cover_title_text: 封面标题    # defaults to title
  cover_subtitle_text: 副标题
  cover_author_text: 作者
  cover_title_color: "#FFFFFF"
  cover_title_font_size: 40
  cover_title_position: center # top | center | bottom
  cover_author_position: bottom
  cover_overlay_enabled: true  # default false: image only
  show_chapter_prefix: true    # 第 1 章 / Chapter 1 above chapter titles
  show_section_numbers: true   # 1.1, 1.2 ...
  show_toc_numbers: true
  show_figure_numbers: true    # 图 1-1 / Figure 1-1
  toc_depth: 2
  papersize: a4                # or us-letter
  font: "Noto Sans CJK SC, Noto Sans"
  monofont: "JetBrains Mono, Menlo"
```

### Shortcode mapping

| Hugo | PDF |
|------|-----|
| `{{< callout note "标题" >}}…{{< /callout >}}` | Tinted callout block (`note`, `tip`, `warning`, `caution`, `info`, `important`) |
| `{{< table title="…" >}}…{{< /table >}}` | Table with caption, numbered 表 1-1 |
| `{{< figure src=… caption=… >}}` | Figure with caption |
| `{{< details "标题" >}}…{{< /details >}}` | Bold title + content |
| `{{< inline-codes file=… lang=… >}}` | Fenced code block from the file |
| `{{< youtube ID >}}`, `{{< bilibili ID >}}` | Link to the video |
| `section-toc`, `quiz`, `cta`, `markmap`, `whimsical`, `podcast`, slides | Removed |
| Any other paired shortcode | Tags removed, inner content kept |

Internal links (`{{< relref >}}` and relative paths) become plain text; external
links stay clickable.

## Development

```bash
uv sync
uv run pytest
uv run pdf-book-exporter example -o example.pdf
```

`src/pdf_book_exporter/templates/book.typ` holds the whole visual design
(fonts, colours, page furniture, callouts, figures, tables). `hugo.lua` is the
only Pandoc filter. `markdown.py` does the Hugo-specific text rewriting before
Pandoc runs.

The previous Pandoc + LaTeX implementation is preserved on the `legacy/v1`
branch and the `v1.0.0` tag.

## License

Apache-2.0
