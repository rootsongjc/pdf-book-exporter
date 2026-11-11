from pathlib import Path

from pdf_book_exporter.book import load_book


def test_example_book_config(example_book: Path):
    book = load_book(example_book)
    cfg = book.config
    assert cfg.title == "PDF Book Exporter 示例"
    assert cfg.language == "zh-hans"
    assert cfg.cover is not None and cfg.cover.endswith("/cover.jpg")
    assert cfg.backcover is not None and cfg.backcover.endswith("/back-cover.jpg")
    assert cfg.cover_text["overlay"] is True
    assert cfg.cover_text["title"] == "PDF Book Exporter"
    assert [c.title for c in book.loose_chapters] == ["前言"]
    assert [(p.title, [c.title for c in p.chapters]) for p in book.parts] == [
        ("第一部分 · 基础排版", ["基础格式", "代码与表格"]),
        ("第二部分 · Hugo 与进阶", ["Hugo 短代码", "进阶格式"]),
        ("附录", ["字体与等宽字符"]),
    ]
    assert [c.title for c in book.parts[1].chapters[1].children] == ["版式细节"]
    assert "未完成的章节" in [c.title for c in load_book(example_book, include_drafts=True).iter_chapters()]


def test_parts_nesting_and_exclusions(parted_book: Path):
    book = load_book(parted_book)
    assert book.config.language == "zh-hans"
    assert book.config.author == "Jimmy Song"
    assert [c.title for c in book.loose_chapters] == ["前言"]
    assert [(p.title, [c.title for c in p.chapters]) for p in book.parts] == [
        ("Part I · 基础", ["基础"]),
        ("附录", ["术语表"]),
    ]
    basics = book.parts[0].chapters[0]
    assert [c.title for c in basics.children] == ["第一节"]


def test_include_drafts(parted_book: Path):
    book = load_book(parted_book, include_drafts=True)
    titles = [c.title for c in book.parts[0].chapters[0].children]
    assert titles == ["第一节", "草稿"]


def test_cover_discovered_from_hugo_site(tmp_path: Path):
    site = tmp_path / "site"
    (site / "config").mkdir(parents=True)
    book = site / "content" / "zh" / "book" / "demo"
    (book / "a").mkdir(parents=True)
    (book / "_index.md").write_text("---\ntitle: Demo\n---\n", encoding="utf-8")
    (book / "a" / "index.md").write_text("---\ntitle: A\n---\nbody\n", encoding="utf-8")

    assert load_book(book).config.cover is None

    (site / "data" / "zh").mkdir(parents=True)
    (site / "data" / "zh" / "book_covers.yaml").write_text(
        "demo: https://cdn.example.com/demo/cover-zh.webp\n", encoding="utf-8"
    )
    cfg = load_book(book).config
    assert cfg.cover == "https://cdn.example.com/demo/cover-zh.webp"
    assert cfg.cover_text["overlay"] is False

    static = site / "static" / "images" / "book-covers"
    static.mkdir(parents=True)
    (static / "demo.webp").write_bytes(b"")
    assert load_book(book).config.cover == str(static / "demo.webp")

    (book / "cover.png").write_bytes(b"")
    assert load_book(book).config.cover == str(book / "cover.png")


def test_cover_falls_back_to_the_cover_image_in_the_index_page(tmp_path: Path):
    book = tmp_path / "site" / "content" / "zh" / "book" / "demo"
    (tmp_path / "site" / "config").mkdir(parents=True)
    (book / "a").mkdir(parents=True)
    (book / "a" / "index.md").write_text("---\ntitle: A\n---\nbody\n", encoding="utf-8")
    index = book / "_index.md"

    index.write_text("---\ntitle: Demo\n---\n![架构图](https://cdn.example.com/arch.png)\n", encoding="utf-8")
    assert load_book(book).config.cover is None

    index.write_text(
        "---\ntitle: Demo\n---\n![架构图](https://cdn.example.com/arch.png)\n\n"
        "![《Demo》中文版封面](https://cdn.example.com/demo-zh.webp)\n",
        encoding="utf-8",
    )
    assert load_book(book).config.cover == "https://cdn.example.com/demo-zh.webp"

    # A generated site cover still wins over the image in the page.
    (tmp_path / "site" / "data" / "zh").mkdir(parents=True)
    (tmp_path / "site" / "data" / "zh" / "book_covers.yaml").write_text(
        "demo: https://cdn.example.com/demo/cover-zh.webp\n", encoding="utf-8"
    )
    assert load_book(book).config.cover == "https://cdn.example.com/demo/cover-zh.webp"


def test_sections_as_parts(sectioned_book: Path):
    book = load_book(sectioned_book)
    assert [c.title for c in book.loose_chapters] == ["前言"]
    assert [(p.title, [c.title for c in p.chapters]) for p in book.parts] == [
        ("系统基础", ["第 1 章", "第 2 章"]),
        ("附录", ["术语表"]),
    ]
    assert book.parts[0].intro.strip().startswith("本部分介绍")


def test_language_inferred_from_path(tmp_path: Path):
    book = tmp_path / "content" / "en" / "book" / "x"
    book.mkdir(parents=True)
    (book / "_index.md").write_text("---\ntitle: X\n---\n", encoding="utf-8")
    (book / "a" / "index.md").parent.mkdir()
    (book / "a" / "index.md").write_text("---\ntitle: A\n---\nbody\n", encoding="utf-8")
    assert load_book(book).config.language == "en"
