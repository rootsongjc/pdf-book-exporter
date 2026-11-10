"""Turn Hugo-flavoured Markdown into Pandoc Markdown.

Handles shortcodes, heading levels, image paths and Hugo-only link syntax.
Everything else is left to Pandoc.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

ResolveImage = Callable[[str], "str | None"]

# Paired shortcodes whose content must be dropped entirely in print.
DROP_PAIRED = {"quiz", "cta", "markmap", "whimsical", "podcast"}
# Single shortcodes with no print representation.
DROP_SINGLE = {"section-toc", "cta", "quiz", "markmap", "marp-slide", "online-slide", "whimsical", "podcast"}

SC_OPEN = r"\{\{[<%]\s*"
SC_CLOSE = r"\s*[>%]\}\}"


def _sc(name: str, args: str = r"([^>%]*?)") -> re.Pattern[str]:
    return re.compile(SC_OPEN + name + r"\b" + args + SC_CLOSE)


def _paired(name: str) -> re.Pattern[str]:
    return re.compile(SC_OPEN + name + r"\b([^>%]*?)" + SC_CLOSE + r"(.*?)" + SC_OPEN + "/" + name + SC_CLOSE, re.S)


ARG_RE = re.compile(r'(\w[\w-]*)=(?:"([^"]*)"|\'([^\']*)\'|(\S+))|"([^"]*)"|\'([^\']*)\'|(\S+)')


def parse_args(raw: str) -> tuple[list[str], dict[str, str]]:
    positional: list[str] = []
    named: dict[str, str] = {}
    for m in ARG_RE.finditer(raw.strip()):
        if m.group(1):
            named[m.group(1)] = m.group(2) or m.group(3) or m.group(4) or ""
        else:
            positional.append(m.group(5) or m.group(6) or m.group(7) or "")
    return positional, named


def _strip_inline_md(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return text.replace('"', "'").strip()


def convert_callouts(body: str) -> str:
    def repl(m: re.Match[str]) -> str:
        pos, named = parse_args(m.group(1))
        kind = (named.get("type") or (pos[0] if pos else "note")).lower()
        title = named.get("title") or (pos[1] if len(pos) > 1 else "")
        title = _strip_inline_md(title)
        attrs = f'type="{kind}"' + (f' title="{title}"' if title else "")
        return f"\n\n::: {{.callout {attrs}}}\n{m.group(2).strip()}\n:::\n\n"

    return _paired("callout").sub(repl, body)


def convert_tables(body: str) -> str:
    def repl(m: re.Match[str]) -> str:
        _, named = parse_args(m.group(1))
        title = _strip_inline_md(named.get("title", ""))
        inner = m.group(2).strip()
        if not title:
            return f"\n\n{inner}\n\n"
        return f'\n\n::: {{.table-title title="{title}"}}\n{inner}\n:::\n\n'

    return _paired("table").sub(repl, body)


def convert_details(body: str) -> str:
    def repl(m: re.Match[str]) -> str:
        pos, named = parse_args(m.group(1))
        title = named.get("title") or (pos[0] if pos else "")
        head = f"**{title.strip()}**\n\n" if title else ""
        return f"\n\n{head}{m.group(2).strip()}\n\n"

    return _paired("details").sub(repl, body)


def convert_figures(body: str) -> str:
    def repl(m: re.Match[str]) -> str:
        _, named = parse_args(m.group(1))
        src = named.get("src", "")
        if not src:
            return ""
        caption = named.get("caption") or named.get("title") or named.get("alt") or ""
        return f"\n\n![{caption}]({src})\n\n"

    return _sc("figure").sub(repl, body)


def convert_videos(body: str, lang: str) -> str:
    label = "视频" if lang.startswith("zh") else "Video"

    def youtube(m: re.Match[str]) -> str:
        pos, named = parse_args(m.group(1))
        vid = named.get("id") or (pos[0] if pos else "")
        return f"\n\n[{label}: https://www.youtube.com/watch?v={vid}](https://www.youtube.com/watch?v={vid})\n\n"

    def bilibili(m: re.Match[str]) -> str:
        pos, named = parse_args(m.group(1))
        vid = named.get("id") or (pos[0] if pos else "")
        return f"\n\n[{label}: https://www.bilibili.com/video/{vid}](https://www.bilibili.com/video/{vid})\n\n"

    body = _sc("youtube").sub(youtube, body)
    return _sc("bilibili").sub(bilibili, body)


def convert_inline_codes(body: str, chapter_dir: Path) -> str:
    def repl(m: re.Match[str]) -> str:
        _, named = parse_args(m.group(1))
        file = named.get("file")
        if not file:
            return ""
        path = chapter_dir / file
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        start = int(named.get("lineStart", 1) or 1)
        end = int(named.get("lineEnd", len(lines)) or len(lines))
        snippet = "\n".join(lines[max(start - 1, 0) : end])
        lang = named.get("lang") or path.suffix.lstrip(".")
        title = named.get("title")
        head = f"**{title}**\n\n" if title else ""
        return f"\n\n{head}```{lang}\n{snippet}\n```\n\n"

    return _sc("inline-codes").sub(repl, body)


def drop_shortcodes(body: str) -> str:
    for name in DROP_PAIRED:
        body = _paired(name).sub("", body)
    for name in DROP_SINGLE:
        body = _sc(name).sub("", body)
    # Any shortcode still present: keep inner content, drop the tags.
    return re.sub(SC_OPEN + r"/?[\w-]+[^>%]*?" + SC_CLOSE, "", body)


def convert_links(body: str) -> str:
    # [text]({{< relref "x" >}}) and relative Hugo links cannot resolve in a PDF: keep the text.
    body = re.sub(r"\[([^\]]+)\]\(\s*\{\{[<%]\s*(?:rel)?ref\b[^}]*\}\}\s*\)", r"\1", body)
    body = re.sub(r"\[([^\]]+)\]\((?!https?://|mailto:|#)[^)\s]*/(?:#[^)]*)?\)", r"\1", body)
    return body


def strip_image_attributes(body: str) -> str:
    # Hugo render hooks accept ![](x.png){width=800 height=600}; Pandoc would apply them literally.
    return re.sub(r"(!\[[^\]]*\]\([^)]*\))\s*\{[^}]*\}", r"\1", body)


def rewrite_images(body: str, resolve: ResolveImage) -> str:
    def repl(m: re.Match[str]) -> str:
        alt, src = m.group(1), m.group(2).strip()
        if src.startswith("<") and src.endswith(">"):
            src = src[1:-1]
        src = src.split(" ")[0]
        target = resolve(src)
        if target is None:
            return f"*{alt}*" if alt else ""
        return f"![{alt}]({target})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, body)


_FENCE_RE = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1[ \t]*$", re.S | re.M)


def _outside_code(body: str, transform: Callable[[str], str]) -> str:
    """Apply `transform` to the text between fenced code blocks only."""
    out: list[str] = []
    pos = 0
    for m in _FENCE_RE.finditer(body):
        out.append(transform(body[pos : m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(transform(body[pos:]))
    return "".join(out)


def normalize_math(body: str) -> str:
    """Map LaTeX-style delimiters Hugo accepts onto the $-forms Pandoc understands."""

    def fix(text: str) -> str:
        text = re.sub(r"(?<!\$)\\\[(.+?)\\\]", r"$$\1$$", text, flags=re.S)
        text = re.sub(r"\\\((.+?)\\\)", r"$\1$", text, flags=re.S)
        text = re.sub(r"^(\\begin\{(align\*?|aligned|equation\*?|gather\*?)\}.*?\\end\{\2\})",
                      r"$$\n\1\n$$", text, flags=re.S | re.M)
        return text

    return _outside_code(body, fix)


HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$", re.M)


def normalize_headings(body: str, title_level: int) -> str:
    """Shift body headings so the smallest one sits one level under the chapter title."""
    blocks: list[str] = []

    def mask(m: re.Match[str]) -> str:
        blocks.append(m.group(0))
        return f"\x00CODEBLOCK{len(blocks) - 1}\x00"

    body = _FENCE_RE.sub(mask, body)
    levels = [len(m.group(1)) for m in HEADING_RE.finditer(body)]
    if levels:
        shift = (title_level + 1) - min(levels)
        if shift:
            body = HEADING_RE.sub(lambda m: "#" * min(6, len(m.group(1)) + shift) + " " + m.group(2), body)
    return re.sub(r"\x00CODEBLOCK(\d+)\x00", lambda m: blocks[int(m.group(1))], body)


def preprocess(body: str, *, chapter_dir: Path, title_level: int, lang: str, resolve_image: ResolveImage) -> str:
    body = body.replace("\r\n", "\n")
    body = convert_inline_codes(body, chapter_dir)
    body = convert_callouts(body)
    body = convert_tables(body)
    body = convert_details(body)
    body = convert_figures(body)
    body = convert_videos(body, lang)
    body = drop_shortcodes(body)
    body = convert_links(body)
    body = strip_image_attributes(body)
    body = rewrite_images(body, resolve_image)
    body = normalize_math(body)
    body = normalize_headings(body, title_level)
    return body.strip() + "\n"
