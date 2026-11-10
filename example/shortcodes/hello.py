"""Minimal script embedded through the inline-codes shortcode."""

from pathlib import Path


def count_chapters(book_dir: Path) -> int:
    """Count page bundles (directories with index.md) under a Hugo book."""
    return sum(1 for p in book_dir.iterdir() if (p / "index.md").exists())


if __name__ == "__main__":
    print(count_chapters(Path("example")))
