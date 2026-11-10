import shutil
from pathlib import Path

import pytest

from pdf_book_exporter.build import BuildOptions, build, render_markdown
from pdf_book_exporter.assets import Assets
from pdf_book_exporter.book import load_book

needs_tools = pytest.mark.skipif(
    not (shutil.which("pandoc") and shutil.which("typst")), reason="pandoc and typst required"
)


def test_render_markdown_structure(parted_book: Path, tmp_path: Path):
    book = load_book(parted_book)
    md = render_markdown(book, Assets(book.directory, tmp_path / "work", offline=True))
    assert md.index("# 前言") < md.index("#part[Part I · 基础]") < md.index("# 基础") < md.index("## 第一节")
    assert "### 小标题" in md
    assert "#appendix()" in md and md.index("#appendix()") < md.index("# 术语表")
    assert '::: {.callout type="note" title="注意"}' in md
    assert "section-toc" not in md


@needs_tools
def test_build_example_pdf(example_book: Path, tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    out = build(example_book, BuildOptions(output=tmp_path / "example.pdf", offline=True))
    reader = pypdf.PdfReader(out)
    assert len(reader.pages) > 10
    titles = [o.title for o in reader.outline if hasattr(o, "title")]
    assert titles[0] == "1 说明"
    assert reader.metadata.title == "PDF 导出功能完整测试"


@needs_tools
def test_build_parts_and_appendix(parted_book: Path, tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    out = build(parted_book, BuildOptions(output=tmp_path / "demo.pdf", offline=True))
    titles = [o.title for o in pypdf.PdfReader(out).outline if hasattr(o, "title")]
    assert titles == ["1 前言", "Part I · 基础", "2 基础", "附录", "A 术语表"]


@needs_tools
def test_horizontal_rule_uses_template_function(parted_book: Path, tmp_path: Path):
    (parted_book / "intro" / "index.md").write_text("---\ntitle: 前言\nweight: 1\n---\n\n上\n\n---\n\n下\n", encoding="utf-8")
    workdir = tmp_path / "work"
    out = build(parted_book, BuildOptions(output=tmp_path / "demo.pdf", offline=True, workdir=workdir))
    assert "#hrule()" in (workdir / "body.typ").read_text(encoding="utf-8")
    assert out.exists()
