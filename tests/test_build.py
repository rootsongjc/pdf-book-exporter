import shutil
from pathlib import Path

import pytest

from pdf_book_exporter.build import (
    BODY_FONTS,
    MONO_FONTS,
    BuildOptions,
    _warn_missing_cjk_font,
    build,
    render_main_typ,
    render_markdown,
    resolve_fonts,
)
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
    assert titles[:3] == ["1 前言", "第一部分 · 基础排版", "2 基础格式"]
    assert "A 字体与等宽字符" in titles
    assert reader.metadata.title == "PDF Book Exporter 示例"


@needs_tools
def test_build_parts_and_appendix(parted_book: Path, tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    out = build(parted_book, BuildOptions(output=tmp_path / "demo.pdf", offline=True))
    titles = [o.title for o in pypdf.PdfReader(out).outline if hasattr(o, "title")]
    assert titles == ["1 前言", "Part I · 基础", "2 基础", "附录", "A 术语表"]


@needs_tools
def test_numbering_restarts_in_every_chapter(sectioned_book: Path, tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    out = build(sectioned_book, BuildOptions(output=tmp_path / "sections.pdf", offline=True, no_cover=True))
    reader = pypdf.PdfReader(out)
    titles = [o.title for o in reader.outline if hasattr(o, "title")]
    assert titles == ["1 前言", "系统基础", "2 第 1 章", "3 第 2 章", "附录", "A 术语表"]

    pages = ["".join(p.extract_text().split()) for p in reader.pages]
    part = next(t for t in pages if "本部分介绍基础" in t)
    assert "系统基础" in part and "section-toc" not in part
    text = "".join(pages)
    assert "1甲注" in text and "2乙注" in text
    # Chapter 2 starts over; chapter numbers are hidden, so figures carry no chapter prefix either.
    assert "1丙注" in text and "3丙注" not in text
    assert text.index("图1甲图") < text.index("图2乙图") < text.index("图1丙图")


@needs_tools
def test_horizontal_rule_uses_template_function(parted_book: Path, tmp_path: Path):
    (parted_book / "intro" / "index.md").write_text("---\ntitle: 前言\nweight: 1\n---\n\n上\n\n---\n\n下\n", encoding="utf-8")
    workdir = tmp_path / "work"
    out = build(parted_book, BuildOptions(output=tmp_path / "demo.pdf", offline=True, workdir=workdir))
    assert "#hrule()" in (workdir / "body.typ").read_text(encoding="utf-8")
    assert out.exists()


def test_preset_fonts_are_reduced_to_installed_families():
    installed = {"pingfang sc", "menlo", "noto sans mono cjk sc"}
    assert resolve_fonts(None, BODY_FONTS["zh"], installed) == ["PingFang SC"]
    assert resolve_fonts(None, MONO_FONTS, installed) == ["Menlo", "Noto Sans Mono CJK SC"]
    # nothing usable, or fonts could not be listed: keep the chain so Typst still reports it
    assert resolve_fonts(None, MONO_FONTS, set()) == list(MONO_FONTS)
    assert resolve_fonts(None, MONO_FONTS, None) == list(MONO_FONTS)


def test_requested_fonts_are_passed_through_unfiltered():
    assert resolve_fonts("Foo Sans, Menlo", MONO_FONTS, {"menlo"}) == ["Foo Sans", "Menlo"]


def test_main_typ_lists_only_installed_preset_fonts(parted_book: Path, tmp_path: Path):
    book = load_book(parted_book)
    installed = {"source han sans sc", "menlo"}
    typ = render_main_typ(book, BuildOptions(output=tmp_path / "x.pdf"), None, None, installed)
    assert 'font: ("Source Han Sans SC",),' in typ
    assert 'monofont: ("Menlo",),' in typ
    typ = render_main_typ(book, BuildOptions(output=tmp_path / "x.pdf", font="My Font"), None, None, installed)
    assert 'font: ("My Font",),' in typ


def test_warns_once_when_no_chinese_font_is_installed(parted_book: Path, tmp_path: Path, capsys):
    book = load_book(parted_book)
    _warn_missing_cjk_font(book, BuildOptions(output=tmp_path / "x.pdf"), {"noto sans", "menlo"})
    assert "no Chinese font installed" in capsys.readouterr().err
    _warn_missing_cjk_font(book, BuildOptions(output=tmp_path / "x.pdf"), {"pingfang sc"})
    _warn_missing_cjk_font(book, BuildOptions(output=tmp_path / "x.pdf", font="My Font"), {"noto sans"})
    assert capsys.readouterr().err == ""


@needs_tools
def test_strong_text_is_bold_not_black(parted_book: Path, tmp_path: Path):
    pypdf = pytest.importorskip("pypdf")
    (parted_book / "intro" / "index.md").write_text(
        "---\ntitle: 前言 **重点**\nweight: 1\n---\n\n正文 **行内加粗** 文字\n\n| **表头** |\n| --- |\n| 内容 |\n",
        encoding="utf-8",
    )
    out = build(parted_book, BuildOptions(output=tmp_path / "demo.pdf", offline=True))
    fonts = {
        str(font.get_object().get("/BaseFont", ""))
        for page in pypdf.PdfReader(out).pages
        for font in page.get("/Resources", {}).get("/Font", {}).values()
    }
    # strong adds a weight delta; stacked on an explicit 700 it used to select the Black face
    assert fonts and not [name for name in fonts if "Black" in name or "Heavy" in name], fonts
