"""Collect images into the build directory; remote images are downloaded once and cached."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
UNSUPPORTED_EXTS = {".avif", ".bmp", ".tiff", ".tif", ".ico"}


def default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
    return Path(base) / "pdf-book-exporter"


class Assets:
    def __init__(self, book_dir: Path, workdir: Path, cache_dir: Path | None = None, offline: bool = False):
        self.book_dir = book_dir
        self.images_dir = workdir / "img"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir or default_cache_dir()
        self.offline = offline
        self.warnings: list[str] = []
        self._seen: dict[str, str] = {}

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"warning: {message}", file=sys.stderr)

    def resolver(self, chapter_dir: Path):
        def resolve(src: str) -> str | None:
            key = f"{chapter_dir}::{src}"
            if key not in self._seen:
                self._seen[key] = self._resolve(src, chapter_dir)
            return self._seen[key]

        return resolve

    def add_source(self, source: str | Path, prefix: str = "") -> str | None:
        """Stage a cover-like image given as a local path or an http(s) URL."""
        text = str(source)
        if text.startswith(("http://", "https://")):
            local = self._download(text)
            return self._stage(local, prefix=prefix) if local else None
        path = Path(text)
        if not path.is_file():
            self.warn(f"image not found: {path}")
            return None
        return self._stage(path, prefix=prefix)

    def _resolve(self, src: str, chapter_dir: Path) -> str | None:
        if src.startswith(("http://", "https://")):
            local = self._download(src)
            return self._stage(local) if local else None
        candidate = self._find_local(src, chapter_dir)
        if candidate is None:
            self.warn(f"image not found: {src} (referenced from {chapter_dir.name})")
            return None
        return self._stage(candidate)

    def _find_local(self, src: str, chapter_dir: Path) -> Path | None:
        clean = src.split("?")[0].split("#")[0]
        if clean.startswith("/"):
            # Hugo static path: try the book dir and then a sibling static/ root.
            for base in (self.book_dir, *self._static_roots()):
                p = base / clean.lstrip("/")
                if p.is_file():
                    return p
            return None
        for base in (chapter_dir, self.book_dir):
            p = (base / clean).resolve()
            if p.is_file():
                return p
        # Fall back to a basename search within the book (images moved into image-caches/ etc.).
        name = Path(clean).name
        for p in self.book_dir.rglob(name):
            if p.is_file():
                return p
        return None

    def _static_roots(self) -> list[Path]:
        roots = []
        for parent in self.book_dir.parents:
            if (parent / "static").is_dir():
                roots.append(parent / "static")
            if (parent / "hugo.toml").exists() or (parent / "config").is_dir():
                break
        return roots

    def _stage(self, path: Path, prefix: str = "") -> str | None:
        ext = path.suffix.lower()
        if ext in UNSUPPORTED_EXTS or ext not in IMAGE_EXTS:
            self.warn(f"unsupported image format skipped: {path}")
            return None
        digest = hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:12]
        target = self.images_dir / f"{prefix}{digest}{ext}"
        if not target.exists():
            shutil.copyfile(path, target)
        return f"img/{target.name}"

    def _download(self, url: str) -> Path | None:
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix.lower() or ".png"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cached = self.cache_dir / (hashlib.sha1(url.encode()).hexdigest() + ext)
        if cached.exists():
            return cached
        if self.offline:
            self.warn(f"offline: remote image skipped: {url}")
            return None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pdf-book-exporter/2"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(cached, "wb") as out:
                shutil.copyfileobj(resp, out)
        except Exception as exc:  # network errors are non-fatal: the figure is dropped with a warning
            cached.unlink(missing_ok=True)
            self.warn(f"download failed: {url} ({exc})")
            return None
        return cached
