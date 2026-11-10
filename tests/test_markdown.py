from pathlib import Path

from pdf_book_exporter.markdown import (
    convert_callouts,
    convert_links,
    convert_tables,
    drop_shortcodes,
    normalize_headings,
    normalize_math,
    preprocess,
    strip_image_attributes,
)


def test_callout_with_quoted_and_bare_titles():
    out = convert_callouts('{{< callout note "观点" >}}\n正文\n{{< /callout >}}')
    assert '::: {.callout type="note" title="观点"}\n正文\n:::' in out
    out = convert_callouts("{{<callout warning 注意>}}\n正文\n{{</callout>}}")
    assert '::: {.callout type="warning" title="注意"}' in out
    out = convert_callouts("{{< callout tip >}}\n正文\n{{< /callout >}}")
    assert '::: {.callout type="tip"}' in out


def test_table_title_wraps_in_div():
    src = '{{< table title="来源与表现" >}}\n| a | b |\n|---|---|\n| 1 | 2 |\n{{< /table >}}'
    out = convert_tables(src)
    assert out.strip().startswith('::: {.table-title title="来源与表现"}')
    assert out.strip().endswith(":::")
    assert "| 1 | 2 |" in out


def test_unknown_paired_shortcode_keeps_inner_content_but_drops_quiz():
    src = "{{< mystery x=1 >}}\nkeep me\n{{< /mystery >}}\n{{< quiz >}}\nq\n{{< /quiz >}}\n{{< section-toc >}}"
    out = drop_shortcodes(src)
    assert "keep me" in out
    assert "q\n" not in out
    assert "{{" not in out


def test_internal_links_become_plain_text():
    src = '[定义]({{< relref "definition" >}}) 与 [上一章](../compute-governance/) 以及 [外链](https://x.io/a/)'
    out = convert_links(src)
    assert out == "定义 与 上一章 以及 [外链](https://x.io/a/)"


def test_preprocess_handles_relref_before_dropping_shortcodes(tmp_path: Path):
    out = preprocess(
        '见 [基础]({{< relref "basics" >}})。', chapter_dir=tmp_path, title_level=1, lang="zh-hans", resolve_image=lambda s: None
    )
    assert out == "见 基础。\n"


def test_image_attribute_block_removed():
    assert strip_image_attributes("![a](x.svg){width=800 height=600}") == "![a](x.svg)"


def test_headings_shift_relative_to_title_and_skip_code_fences():
    body = "## A\n\n```md\n# not a heading\n```\n\n### B\n"
    out = normalize_headings(body, title_level=2)
    assert "### A" in out and "#### B" in out
    assert "# not a heading" in out


def test_math_delimiters_normalised_outside_code():
    src = "\\[ x \\] and \\( y \\)\n\n\\begin{align}\na &= b\n\\end{align}\n\n```tex\n\\[ raw \\]\n```"
    out = normalize_math(src)
    assert "$$ x $$ and $ y $" in out
    assert "$$\n\\begin{align}" in out
    assert "\\[ raw \\]" in out


def test_preprocess_resolves_images_and_drops_missing(tmp_path: Path):
    seen = []

    def resolve(src):
        seen.append(src)
        return "img/ok.svg" if src.endswith("ok.svg") else None

    body = "![好图](ok.svg)\n\n![坏图](missing.png){width=10}\n"
    out = preprocess(body, chapter_dir=tmp_path, title_level=1, lang="zh-hans", resolve_image=resolve)
    assert "![好图](img/ok.svg)" in out
    assert "missing.png" not in out and "*坏图*" in out
    assert seen == ["ok.svg", "missing.png"]
