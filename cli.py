import argparse
import os
from tree import build_tree
from frontmatter import parse_front_matter, should_include, load_book_config
from pdf_builder import build_pdf
from cache_utils import clean_cache, show_cache_info

def main():
    parser = argparse.ArgumentParser(description='Export a Hugo book to PDF')
    parser.add_argument('book_dir', help='Path to the book directory')
    parser.add_argument('-o', '--output', help='Output PDF file path')
    parser.add_argument('--generate-summary', action='store_true', help='Generate summary.md file')
    parser.add_argument('--template', default=None, help='Custom LaTeX template path (XeLaTeX only)')
    parser.add_argument('--clean-cache', type=int, nargs='?', const=30, help='Clean cache files older than specified days (default: 30)')
    parser.add_argument('--cache-info', action='store_true', help='Show cache directory information')
    parser.add_argument('--appendix', default=None, help='Path to appendix markdown file')
    parser.add_argument('--emoji', action='store_true', help='Enable emoji support')
    parser.add_argument('--include-drafts', action='store_true', help='Include draft content')
    parser.add_argument('--diagnostics', action='store_true', help='Diagnostics')
    parser.add_argument('--generate-troubleshooting-guide', action='store_true', help='Generate troubleshooting guide')
    parser.add_argument('--max-table-width', type=float, default=0.85,
                        help='Maximum table width as fraction of text width (default: 0.85)')

    args = parser.parse_args()
    
    if args.clean_cache is not None:
        clean_cache(args.book_dir, args.clean_cache)
        return
    if args.cache_info:
        show_cache_info(args.book_dir)
        return
    
    root_node = build_tree(args.book_dir, args.include_drafts, parse_front_matter, should_include)
    if not root_node:
        return
    
    # Load book configuration from _index.md
    book_config = load_book_config(args.book_dir)
    
    output_pdf = args.output or os.path.join(args.book_dir, 'book.pdf')
    ok = build_pdf(args.book_dir, root_node, output_pdf, book_config, args.template, args.appendix, args.emoji, args.max_table_width)
    if not ok:
        # Non-zero exit so callers (e.g., Makefile) can detect failure
        raise SystemExit(1)

if __name__ == '__main__':
    main()
