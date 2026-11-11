"""Book discovery: walk a Hugo book directory and build an ordered chapter tree."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n?(.*)\Z", re.S)
SKIP_DIRS = {"image-caches", "drawio", "images", "img", "static", "assets"}
# GitBook leftovers that sometimes sit next to Hugo bundles.
SKIP_FILES = {"readme.md", "summary.md"}


class BookError(Exception):
    pass


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, m.group(2)


def read_page(path: Path) -> tuple[dict[str, Any], str]:
    return split_front_matter(path.read_text(encoding="utf-8"))


def _truthy(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


@dataclass
class Chapter:
    path: Path
    title: str
    body: str
    weight: float
    part_id: str | None
    draft: bool
    children: list["Chapter"] = field(default_factory=list)

    @property
    def directory(self) -> Path:
        return self.path.parent


@dataclass
class Part:
    id: str
    title: str
    chapters: list[Chapter] = field(default_factory=list)
    intro: str = ""  # Markdown shown under the title on the part page
    directory: Path | None = None  # resolves images in the intro


@dataclass
class BookConfig:
    title: str
    subtitle: str
    author: str
    language: str
    description: str
    website: str
    publisher: str
    date: str
    cover: str | None  # local path or URL
    backcover: str | None
    cover_text: dict[str, Any]
    show_chapter_prefix: bool
    show_section_numbers: bool
    show_toc_numbers: bool
    show_figure_numbers: bool
    toc_depth: int
    papersize: str
    font: str | None
    monofont: str | None
    raw: dict[str, Any]


@dataclass
class Book:
    directory: Path
    config: BookConfig
    intro: str
    parts: list[Part]
    loose_chapters: list[Chapter]

    def iter_chapters(self):
        yield from self.loose_chapters
        for part in self.parts:
            yield from part.chapters


def infer_language(book_dir: Path, explicit: str | None) -> str:
    if explicit:
        return str(explicit).strip().lower()
    parts = {p.lower() for p in book_dir.resolve().parts}
    if "en" in parts:
        return "en"
    if "zh" in parts or "zh-hans" in parts or "zh-cn" in parts:
        return "zh-hans"
    return "zh-hans"


IMAGE_SUFFIXES = (".webp", ".jpg", ".jpeg", ".png")
SITE_CONFIG_MARKERS = ("hugo.toml", "hugo.yaml", "hugo.yml", "config.toml", "config.yaml", "config.yml", "config")


def _resolve_asset(book_dir: Path, value: Any) -> str | None:
    """Return a local path or an http(s) URL for a front-matter image value."""
    if not value:
        return None
    text = str(value).strip()
    if text.startswith(("http://", "https://")):
        return text
    p = Path(text).expanduser()
    if not p.is_absolute():
        p = book_dir / p
    return str(p) if p.exists() else None


def _first_existing(directory: Path, stems: tuple[str, ...]) -> str | None:
    for stem in stems:
        for suffix in IMAGE_SUFFIXES:
            candidate = directory / f"{stem}{suffix}"
            if candidate.is_file():
                return str(candidate)
    return None


def find_site_root(book_dir: Path) -> Path | None:
    for parent in book_dir.parents:
        if any((parent / m).exists() for m in SITE_CONFIG_MARKERS) and (parent / "content").is_dir():
            return parent
    return None


def _content_lang(book_dir: Path, site_root: Path) -> str | None:
    try:
        rel = book_dir.relative_to(site_root / "content").parts
    except ValueError:
        return None
    return rel[0] if len(rel) > 1 else None


CONTENT_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^ )]+)\)")


def _content_cover(book_dir: Path, intro: str) -> str | None:
    """First image in the book's index page whose Markdown (alt text or path) says it is a cover."""
    for m in CONTENT_IMAGE_RE.finditer(intro):
        if "cover" in m.group(0).lower() or "封面" in m.group(0):
            found = _resolve_asset(book_dir, m.group(1))
            if found:
                return found
    return None


def discover_cover(book_dir: Path, language: str, intro: str = "") -> str | None:
    """Default cover lookup, in order:

    1. cover.<ext> / cover-<lang>.<ext> inside the book directory
    2. Hugo site: static/images/book-covers/<slug>.webp
    3. Hugo site: data/<lang>/book_covers.yaml → URL keyed by slug
    4. the cover image shown in the book's index page
    """
    short = language.split("-")[0]
    local = _first_existing(book_dir, (f"cover-{short}", "cover"))
    if local:
        return local
    return _site_cover(book_dir, short) or _content_cover(book_dir, intro)


def _site_cover(book_dir: Path, short: str) -> str | None:
    site = find_site_root(book_dir)
    if site is None:
        return None
    slug = book_dir.name
    static = _first_existing(site / "static" / "images" / "book-covers", (slug,))
    if static:
        return static
    lang = _content_lang(book_dir, site) or short
    data = site / "data" / lang / "book_covers.yaml"
    if data.exists():
        try:
            mapping = yaml.safe_load(data.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            mapping = {}
        if isinstance(mapping, dict) and mapping.get(slug):
            return str(mapping[slug])
    return None


def discover_backcover(book_dir: Path, language: str) -> str | None:
    short = language.split("-")[0]
    return _first_existing(book_dir, (f"backcover-{short}", "backcover", f"back-cover-{short}", "back-cover"))


def _first(*values: Any, default: Any = "") -> Any:
    for v in values:
        if v not in (None, ""):
            return v
    return default


def _date_str(value: Any) -> str:
    if value in (None, ""):
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()[:10]
    return str(value)[:10]


def load_config(book_dir: Path, meta: dict[str, Any], intro: str = "") -> BookConfig:
    book = meta.get("book") if isinstance(meta.get("book"), dict) else {}
    authors = meta.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    author = _first(book.get("author"), meta.get("author"), ", ".join(map(str, authors)))
    date = _date_str(_first(book.get("date"), meta.get("date")))
    title = _first(book.get("title"), meta.get("title"), book_dir.name)
    cover_text = {
        "title": _first(book.get("cover_title_text"), title),
        "author": _first(book.get("cover_author_text"), author),
        "subtitle": _first(book.get("cover_subtitle_text"), book.get("subtitle")),
        "title_color": book.get("cover_title_color", "#FFFFFF"),
        "author_color": book.get("cover_author_color", "#FFFFFF"),
        "subtitle_color": book.get("cover_subtitle_color", "#FFFFFF"),
        "title_size": book.get("cover_title_font_size", 40),
        "author_size": book.get("cover_author_font_size", 20),
        "subtitle_size": book.get("cover_subtitle_font_size", 16),
        "title_position": book.get("cover_title_position", "center"),
        "author_position": book.get("cover_author_position", "bottom"),
        "overlay": _truthy(book.get("cover_overlay_enabled"), False),
    }
    language = infer_language(book_dir, _first(book.get("language"), meta.get("language")))
    cover = _resolve_asset(book_dir, _first(book.get("cover"), meta.get("cover"))) or discover_cover(book_dir, language, intro)
    backcover = _resolve_asset(book_dir, _first(book.get("backcover"), book.get("backcover_image"))) or discover_backcover(
        book_dir, language
    )
    show_toc = book.get("show_toc_numbers", book.get("toc_numbered"))
    return BookConfig(
        title=str(title),
        subtitle=str(_first(book.get("subtitle"))),
        author=str(author),
        language=language,
        description=str(_first(book.get("description"), meta.get("description"))),
        website=str(_first(book.get("website"), meta.get("website"))),
        publisher=str(_first(book.get("publisher"), meta.get("publisher"))),
        date=date,
        cover=cover,
        backcover=backcover,
        cover_text=cover_text,
        show_chapter_prefix=_truthy(book.get("show_chapter_prefix"), True),
        show_section_numbers=_truthy(book.get("show_section_numbers"), True),
        show_toc_numbers=_truthy(show_toc, True),
        show_figure_numbers=_truthy(book.get("show_figure_numbers"), True),
        toc_depth=int(book.get("toc_depth", 2)),
        papersize=str(book.get("papersize", "a4")),
        font=book.get("font"),
        monofont=book.get("monofont"),
        raw=book,
    )


def _page_included(meta: dict[str, Any], include_drafts: bool) -> bool:
    if not include_drafts and _truthy(meta.get("draft"), False):
        return False
    if not _truthy(meta.get("export_pdf"), True):
        return False
    if str(meta.get("status", "")).lower() in {"offline", "unpublished"}:
        return False
    return True


def _load_chapter(page: Path, include_drafts: bool, require_front_matter: bool = False) -> Chapter | None:
    meta, body = read_page(page)
    if require_front_matter and not meta:
        return None
    if not _page_included(meta, include_drafts):
        return None
    weight = meta.get("weight", 0)
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        weight = 0.0
    return Chapter(
        path=page,
        title=str(meta.get("title") or page.parent.name),
        body=body,
        weight=weight,
        part_id=meta.get("part_id"),
        draft=_truthy(meta.get("draft"), False),
    )


def _collect(directory: Path, include_drafts: bool, depth: int) -> list[Chapter]:
    chapters: list[Chapter] = []
    for entry in sorted(directory.iterdir()):
        if entry.name.startswith((".", "_")) or entry.name in SKIP_DIRS:
            continue
        if entry.is_dir():
            if (entry / "index.md").exists():
                ch = _load_chapter(entry / "index.md", include_drafts)
            elif (entry / "_index.md").exists():
                ch = _load_chapter(entry / "_index.md", include_drafts)
                if ch is not None and depth < 2:
                    ch.children = _collect(entry, include_drafts, depth + 1)
            else:
                continue
        elif entry.suffix == ".md" and entry.name not in {"index.md", "_index.md"}:
            if entry.name.lower() in SKIP_FILES:
                continue
            ch = _load_chapter(entry, include_drafts, require_front_matter=True)
        else:
            continue
        if ch is not None:
            chapters.append(ch)
    chapters.sort(key=lambda c: (c.weight, c.title))
    return chapters


def load_book(book_dir: Path, include_drafts: bool = False) -> Book:
    book_dir = book_dir.resolve()
    index = book_dir / "_index.md"
    if not index.exists():
        index = book_dir / "index.md"
    if not index.exists():
        raise BookError(f"{book_dir} is not a Hugo book: no _index.md found")
    meta, intro = read_page(index)
    config = load_config(book_dir, meta, intro)
    chapters = _collect(book_dir, include_drafts, depth=1)
    if not chapters:
        raise BookError(f"No chapters found under {book_dir}")

    if _truthy(config.raw.get("sections_as_parts"), False):
        # Top-level sections are the parts and their pages the chapters; pages without children stay chapters.
        sections = [
            Part(id=ch.directory.name, title=ch.title, chapters=ch.children, intro=ch.body, directory=ch.directory)
            for ch in chapters
            if ch.children
        ]
        loose = [ch for ch in chapters if not ch.children]
        return Book(directory=book_dir, config=config, intro=intro, parts=sections, loose_chapters=loose)

    part_defs = meta.get("parts") or []
    parts: list[Part] = []
    if isinstance(part_defs, list):
        for p in sorted(part_defs, key=lambda p: p.get("order", 0) if isinstance(p, dict) else 0):
            if isinstance(p, dict) and p.get("id"):
                parts.append(Part(id=str(p["id"]), title=str(p.get("title") or p["id"])))
    by_id = {p.id: p for p in parts}
    loose: list[Chapter] = []
    for ch in chapters:
        if ch.part_id and ch.part_id in by_id:
            by_id[ch.part_id].chapters.append(ch)
        else:
            loose.append(ch)
    parts = [p for p in parts if p.chapters]
    return Book(directory=book_dir, config=config, intro=intro, parts=parts, loose_chapters=loose)
