"""Check that the external tools (pandoc, typst) are installed and recent enough."""

from __future__ import annotations

import re
import shutil
import subprocess

MIN_PANDOC = (3, 1, 7)  # first release with a usable Typst writer
MIN_TYPST = (0, 13, 0)  # outline.entry API used by the template


def _version(cmd: list[str]) -> tuple[int, ...] | None:
    exe = shutil.which(cmd[0])
    if not exe:
        return None
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", out)
    if not m:
        return ()
    return tuple(int(x) for x in m.groups(default="0"))


def _fmt(v: tuple[int, ...]) -> str:
    return ".".join(map(str, v))


def check() -> list[str]:
    problems: list[str] = []
    pandoc = _version(["pandoc", "--version"])
    if pandoc is None:
        problems.append("pandoc not found. Install: brew install pandoc  (https://pandoc.org/installing.html)")
    elif pandoc < MIN_PANDOC:
        problems.append(f"pandoc {_fmt(pandoc)} is too old; need >= {_fmt(MIN_PANDOC)}")
    typst = _version(["typst", "--version"])
    if typst is None:
        problems.append("typst not found. Install: brew install typst  (https://github.com/typst/typst#installation)")
    elif typst < MIN_TYPST:
        problems.append(f"typst {_fmt(typst)} is too old; need >= {_fmt(MIN_TYPST)}")
    return problems
