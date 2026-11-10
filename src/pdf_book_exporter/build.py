"""Pipeline: Hugo book directory -> Pandoc Markdown -> Typst -> PDF."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .assets import Assets
from .book import Book, Chapter, Part, load_book
from .markdown import preprocess

TEMPLATES = Path(__file__).parent / "templates"
PANDOC_FORMAT = "commonmark_x+implicit_figures-gfm_auto_identifiers"


class BuildError(Exception):
    pass


@dataclass
class BuildOptions:
    output: Path
    include_drafts: bool = False
    cover: str | None = None
    backcover: str | None = None
    no_cover: bool = False
    font: str | None = None
    monofont: str | None = None
    keep_workdir: bool = False
    workdir: Path | None = None
    offline: bool = False
    font_paths: list[Path] | None = None
    verbose: bool = False


def typ_str(value: object) -> str:
    s = "" if value is None else str(value)
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def typ_bool(value: bool) -> str:
    return "true" if value else "false"


def typ_font_list(names: Sequence[str]) -> str:
    if not names:
        return "()"
    return "(" + ", ".join(typ_str(n) for n in names) + ("," if len(names) == 1 else "") + ")"


# Preset fallback chains live here rather than in the template so that families Typst
# cannot find are dropped before compiling: Typst warns once per missing family in a
# chain even when an earlier family is the one actually used.
ZH_BODY_FONTS = ("Noto Sans CJK SC", "Source Han Sans SC", "PingFang SC", "Microsoft YaHei")
BODY_FONTS = {
    "zh": (*ZH_BODY_FONTS, "Noto Sans"),
    "default": ("Noto Sans", "Helvetica Neue", "Arial", "Noto Sans CJK SC"),
}
MONO_FONTS = ("JetBrains Mono", "Menlo", "DejaVu Sans Mono", "Consolas", "Noto Sans Mono CJK SC")


def installed_fonts(font_paths: Sequence[Path] | None = None) -> set[str] | None:
    """Casefolded family names Typst can see, or None when they cannot be listed."""
    cmd = ["typst", "fonts"]
    for fp in font_paths or []:
        cmd += ["--font-path", str(fp)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return {line.strip().casefold() for line in result.stdout.splitlines() if line.strip()}


def resolve_fonts(requested: str | None, preset: Sequence[str], installed: set[str] | None) -> list[str]:
    """Font chain for the template.

    Families requested by the user are passed through untouched, so Typst still reports
    one that is missing. A preset is reduced to its installed families; if none of them
    is installed (or the fonts could not be listed) the whole chain is kept so the
    problem stays visible.
    """
    names = [n.strip() for n in (requested or "").split(",") if n.strip()]
    if names:
        return names
    if installed is None:
        return list(preset)
    return [n for n in preset if n.casefold() in installed] or list(preset)


def _chapter_markdown(chapter: Chapter, level: int, assets: Assets, lang: str) -> str:
    body = preprocess(
        chapter.body,
        chapter_dir=chapter.directory,
        title_level=level,
        lang=lang,
        resolve_image=assets.resolver(chapter.directory),
    )
    parts = [f"{'#' * level} {chapter.title}\n\n{body}"]
    for child in chapter.children:
        parts.append(_chapter_markdown(child, level + 1, assets, lang))
    return "\n\n".join(parts)


APPENDIX_RE = re.compile(r"appendix|附录", re.I)


def _part_block(part: Part) -> str:
    escaped = part.title.replace("\\", "\\\\").replace("]", "\\]").replace("#", "\\#")
    lines = [f"#part[{escaped}]"]
    if APPENDIX_RE.search(part.id) or APPENDIX_RE.search(part.title):
        lines.append("#appendix()")
        lines.append("#set heading(numbering: appendix-heading-number)")
    return "```{=typst}\n" + "\n".join(lines) + "\n```\n"


def render_markdown(book: Book, assets: Assets) -> str:
    lang = book.config.language
    chunks: list[str] = []
    for chapter in book.loose_chapters:
        chunks.append(_chapter_markdown(chapter, 1, assets, lang))
    for part in book.parts:
        chunks.append(_part_block(part))
        for chapter in part.chapters:
            chunks.append(_chapter_markdown(chapter, 1, assets, lang))
    return "\n\n".join(chunks) + "\n"


def render_main_typ(
    book: Book,
    opts: BuildOptions,
    cover: str | None,
    backcover: str | None,
    installed: set[str] | None = None,
) -> str:
    cfg = book.config
    lang = "zh" if cfg.language.startswith("zh") else cfg.language.split("-")[0]
    region = "cn" if lang == "zh" else ("us" if lang == "en" else "")
    body_fonts = resolve_fonts(opts.font or cfg.font, BODY_FONTS["zh" if lang == "zh" else "default"], installed)
    mono_fonts = resolve_fonts(opts.monofont or cfg.monofont, MONO_FONTS, installed)
    ct = cfg.cover_text
    cover_text = (
        "(\n"
        f"    title: {typ_str(ct['title'])},\n"
        f"    subtitle: {typ_str(ct['subtitle'])},\n"
        f"    author: {typ_str(ct['author'])},\n"
        f"    title_color: {typ_str(ct['title_color'])},\n"
        f"    author_color: {typ_str(ct['author_color'])},\n"
        f"    subtitle_color: {typ_str(ct['subtitle_color'])},\n"
        f"    title_size: {float(ct['title_size'])},\n"
        f"    author_size: {float(ct['author_size'])},\n"
        f"    subtitle_size: {float(ct['subtitle_size'])},\n"
        f"    title_position: {typ_str(ct['title_position'])},\n"
        f"    author_position: {typ_str(ct['author_position'])},\n"
        f"    overlay: {typ_bool(bool(ct['overlay']))},\n"
        "  )"
    )
    exported = datetime.now().strftime("%Y-%m-%d")
    return f"""#import "book.typ": book
#show: book.with(
  title: {typ_str(cfg.title)},
  subtitle: {typ_str(cfg.subtitle)},
  author: {typ_str(cfg.author)},
  publisher: {typ_str(cfg.publisher)},
  website: {typ_str(cfg.website)},
  description: {typ_str(cfg.description)},
  date: {typ_str(cfg.date)},
  exported: {typ_str(exported)},
  lang: {typ_str(lang)},
  region: {typ_str(region)},
  cover: {typ_str(cover) if cover else "none"},
  backcover: {typ_str(backcover) if backcover else "none"},
  cover-text: {cover_text},
  show-chapter-prefix: {typ_bool(cfg.show_chapter_prefix)},
  show-section-numbers: {typ_bool(cfg.show_section_numbers)},
  show-toc-numbers: {typ_bool(cfg.show_toc_numbers)},
  show-figure-numbers: {typ_bool(cfg.show_figure_numbers)},
  toc-depth: {cfg.toc_depth},
  paper: {typ_str(cfg.papersize)},
  font: {typ_font_list(body_fonts)},
  monofont: {typ_font_list(mono_fonts)},
)
#include "body.typ"
"""


def _run(cmd: list[str], verbose: bool, label: str) -> subprocess.CompletedProcess[str]:
    if verbose:
        print(f"$ {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise BuildError(f"{label} failed (exit {result.returncode}):\n{result.stderr.strip()}")
    return result


def _print_typst_diagnostics(stderr: str) -> None:
    # Font warnings fire per style run; collapse them to one line per family.
    seen: set[str] = set()
    for block in re.split(r"\n(?=warning:|error:)", stderr.strip()):
        head = block.splitlines()[0] if block else ""
        if "unknown font family" in head:
            fam = re.search(r"unknown font family: (.+)", head)
            key = fam.group(1) if fam else head
            if key in seen:
                continue
            seen.add(key)
            print(f"warning: font not installed: {key}", file=sys.stderr)
        elif block.strip():
            print(block.strip(), file=sys.stderr)


def _warn_missing_cjk_font(book: Book, opts: BuildOptions, installed: set[str] | None) -> None:
    # Dropping uninstalled preset families also drops Typst's hint that no Chinese font
    # exists, and the PDF would silently render missing glyphs. Say so explicitly.
    cfg = book.config
    if installed is None or not cfg.language.startswith("zh") or opts.font or cfg.font:
        return
    if not any(name.casefold() in installed for name in ZH_BODY_FONTS):
        print(
            f"warning: no Chinese font installed (looked for {', '.join(ZH_BODY_FONTS)}); "
            "Chinese text may not render. Install one or pass --font.",
            file=sys.stderr,
        )


def build(book_dir: Path, opts: BuildOptions) -> Path:
    started = time.time()
    book = load_book(book_dir, include_drafts=opts.include_drafts)
    cfg = book.config

    if opts.workdir:
        workdir = opts.workdir
        workdir.mkdir(parents=True, exist_ok=True)
        keep = True
    elif opts.keep_workdir:
        workdir = Path(tempfile.mkdtemp(prefix="pdf-book-"))
        keep = True
    else:
        workdir = Path(tempfile.mkdtemp(prefix="pdf-book-"))
        keep = False

    try:
        assets = Assets(book.directory, workdir, offline=opts.offline)
        cover_src = None if opts.no_cover else (opts.cover or cfg.cover)
        backcover_src = opts.backcover or cfg.backcover
        cover = assets.add_source(cover_src, prefix="cover-") if cover_src else None
        backcover = assets.add_source(backcover_src, prefix="backcover-") if backcover_src else None
        if cover_src and opts.verbose:
            print(f"cover: {cover_src}", file=sys.stderr)

        (workdir / "body.md").write_text(render_markdown(book, assets), encoding="utf-8")
        shutil.copyfile(TEMPLATES / "book.typ", workdir / "book.typ")
        installed = installed_fonts(opts.font_paths)
        _warn_missing_cjk_font(book, opts, installed)
        (workdir / "main.typ").write_text(render_main_typ(book, opts, cover, backcover, installed), encoding="utf-8")

        _run(
            [
                "pandoc",
                str(workdir / "body.md"),
                "-f", PANDOC_FORMAT,
                "-t", "typst",
                "--wrap=none",
                f"--lua-filter={TEMPLATES / 'hugo.lua'}",
                "-o", str(workdir / "body.typ"),
            ],
            opts.verbose,
            "pandoc",
        )
        # `#include` does not share the importing file's scope, so the body needs its own import.
        body_typ = workdir / "body.typ"
        body_typ.write_text('#import "book.typ": part, appendix, appendix-heading-number, callout, taskbox, hrule\n' + body_typ.read_text(encoding="utf-8"), encoding="utf-8")

        output = opts.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["typst", "compile", "--root", str(workdir)]
        for fp in opts.font_paths or []:
            cmd += ["--font-path", str(fp)]
        cmd += [str(workdir / "main.typ"), str(output)]
        result = _run(cmd, opts.verbose, "typst")
        if result.stderr.strip():
            _print_typst_diagnostics(result.stderr)

        elapsed = time.time() - started
        chapters = sum(1 for _ in book.iter_chapters())
        print(f"{output} ({output.stat().st_size / 1024:.0f} KB, {chapters} chapters, {elapsed:.1f}s)")
        if keep:
            print(f"build files kept in {workdir}", file=sys.stderr)
        return output
    except BuildError:
        if not keep:
            kept = Path(tempfile.mkdtemp(prefix="pdf-book-failed-"))
            shutil.copytree(workdir, kept, dirs_exist_ok=True)
            print(f"build files kept in {kept}", file=sys.stderr)
        raise
    finally:
        if not keep:
            shutil.rmtree(workdir, ignore_errors=True)
