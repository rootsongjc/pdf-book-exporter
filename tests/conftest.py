import shutil
from pathlib import Path

import pytest

EXAMPLE = Path(__file__).resolve().parent.parent / "example"


@pytest.fixture
def example_book() -> Path:
    return EXAMPLE


def write(path: Path, front: str, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front.strip()}\n---\n\n{body}", encoding="utf-8")


@pytest.fixture
def parted_book(tmp_path: Path) -> Path:
    """A minimal book with two parts, an appendix, a nested chapter and excluded pages."""
    book = tmp_path / "zh" / "book" / "demo"
    write(
        book / "_index.md",
        "title: 演示手册\nauthors:\n  - Jimmy Song\npublisher: jimmysong.io\n"
        "parts:\n  - {id: part-i, title: 'Part I · 基础', order: 1}\n"
        "  - {id: part-appendix, title: 附录, order: 2}\n",
        "简介 {{< section-toc >}}",
    )
    write(book / "intro" / "index.md", "title: 前言\nweight: 1", "> 引子\n\n正文")
    write(book / "basics" / "_index.md", "title: 基础\nweight: 10\npart_id: part-i", "章节导语")
    write(book / "basics" / "first" / "index.md", "title: 第一节\nweight: 1", "## 小标题\n\n内容\n\n{{< callout note 注意 >}}\n提示\n{{< /callout >}}")
    write(book / "basics" / "draft" / "index.md", "title: 草稿\nweight: 2\ndraft: true", "不应出现")
    write(book / "basics" / "web-only" / "index.md", "title: 仅网页\nweight: 3\nexport_pdf: false", "不应出现")
    write(book / "glossary" / "index.md", "title: 术语表\nweight: 90\npart_id: part-appendix", "术语")
    (book / "README.md").write_text("# GitBook leftover\n", encoding="utf-8")
    (book / "image-caches").mkdir()
    return book


@pytest.fixture
def sectioned_book(tmp_path: Path) -> Path:
    """A book whose top-level sections group the chapters (`book.sections_as_parts`)."""
    book = tmp_path / "zh" / "book" / "sections"
    write(book / "_index.md", "title: 分部手册\nbook:\n  sections_as_parts: true\n  show_chapter_prefix: false\n  show_section_numbers: false")
    write(book / "preface" / "index.md", "title: 前言\nweight: 1", "开场")
    write(book / "foundations" / "_index.md", "title: 系统基础\nweight: 2", "本部分介绍基础。\n\n{{< section-toc >}}")
    write(
        book / "foundations" / "one" / "index.md",
        "title: 第 1 章\nweight: 1",
        "甲文[^a]，乙文[^b]。\n\n[^a]: 甲注\n\n[^b]: 乙注\n\n![甲图](one.jpg)\n\n![乙图](one.jpg)",
    )
    write(
        book / "foundations" / "two" / "index.md",
        "title: 第 2 章\nweight: 2",
        "丙文[^c]。\n\n[^c]: 丙注\n\n![丙图](two.jpg)",
    )
    write(book / "appendix" / "_index.md", "title: 附录\nweight: 9")
    write(book / "appendix" / "glossary" / "index.md", "title: 术语表\nweight: 1", "术语")
    for name in ("one/one.jpg", "two/two.jpg"):
        shutil.copyfile(EXAMPLE / "cover.jpg", book / "foundations" / name)
    return book
