"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, deps
from .book import BookError, load_book
from .build import BuildError, BuildOptions, build


def _default_output(book_dir: Path) -> Path:
    try:
        lang = load_book(book_dir).config.language.split("-")[0]
    except BookError:
        lang = "book"
    return Path.cwd() / f"{book_dir.resolve().name}-{lang}.pdf"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pdf-book-exporter",
        description="Export a Hugo book directory to PDF (Pandoc + Typst).",
    )
    parser.add_argument("book_dir", type=Path, nargs="?", help="book directory containing _index.md")
    parser.add_argument("-o", "--output", type=Path, help="output PDF path (default: ./<book>-<lang>.pdf)")
    parser.add_argument("--cover", help="cover image path or URL (overrides front matter and site lookup)")
    parser.add_argument("--backcover", help="back cover image path or URL")
    parser.add_argument("--no-cover", action="store_true", help="skip the cover image even if one is found")
    parser.add_argument("--font", help="comma-separated body font families, in fallback order")
    parser.add_argument("--monofont", help="comma-separated monospace font families")
    parser.add_argument("--font-path", type=Path, action="append", help="extra font directory for Typst (repeatable)")
    parser.add_argument("--include-drafts", action="store_true", help="include pages with draft: true")
    parser.add_argument("--offline", action="store_true", help="do not download remote images (use cache only)")
    parser.add_argument("--workdir", type=Path, help="write intermediate files here (implies --keep)")
    parser.add_argument("--keep", action="store_true", help="keep the intermediate Markdown/Typst files")
    parser.add_argument("-v", "--verbose", action="store_true", help="print the pandoc/typst commands")
    parser.add_argument("--check", action="store_true", help="only check that pandoc and typst are available")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    problems = deps.check()
    if args.check:
        print("\n".join(problems) if problems else "pandoc and typst are available")
        return 1 if problems else 0
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2

    if args.book_dir is None:
        parser.error("the following arguments are required: book_dir")
    if not args.book_dir.is_dir():
        print(f"error: {args.book_dir} is not a directory", file=sys.stderr)
        return 2
    for p in (args.cover, args.backcover):
        if p and not p.startswith(("http://", "https://")) and not Path(p).is_file():
            print(f"error: image not found: {p}", file=sys.stderr)
            return 2

    opts = BuildOptions(
        output=args.output or _default_output(args.book_dir),
        include_drafts=args.include_drafts,
        cover=args.cover,
        backcover=args.backcover,
        no_cover=args.no_cover,
        font=args.font,
        monofont=args.monofont,
        keep_workdir=args.keep,
        workdir=args.workdir,
        offline=args.offline,
        font_paths=args.font_path,
        verbose=args.verbose,
    )
    try:
        build(args.book_dir, opts)
    except (BookError, BuildError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
