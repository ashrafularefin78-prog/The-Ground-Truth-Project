"""Shared helpers for the Ground Truth Project build pipeline.

Standard library only. The site must rebuild on a machine that has Python and
nothing else installed, so no third-party packages are imported anywhere here.
"""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path

DATA_FILES = ("places.csv", "observations.csv", "photos.csv")
LANGUAGES = ("en", "bn")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
OBS_ID_RE = re.compile(r"^OBS-\d{3,}$")
PHOTO_ID_RE = re.compile(r"^PH-\d{3,}$")
PLACE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,30}$")


class BuildError(Exception):
    """Anything that should stop the build with a readable message."""


class DataError(BuildError):
    """Raw data does not match the documented schema."""


class TokenError(BuildError):
    """A {{namespace:key}} token could not be resolved."""


# --------------------------------------------------------------------------
# paths and files
# --------------------------------------------------------------------------

def repo_root() -> Path:
    """Repository root: the folder holding ``data/``, ``src/`` and ``tools/``."""
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path):
    try:
        return json.loads(read_text(path))
    except FileNotFoundError as exc:
        raise BuildError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"{path} is not valid JSON: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def data_fingerprint(root: Path) -> dict:
    """Hash of every raw data file, so a page can prove which data it came from."""
    files = {}
    for name in DATA_FILES + ("interview.md",):
        path = Path(root) / "data" / name
        files[name] = sha256_file(path) if path.exists() else "missing"
    combined = hashlib.sha256(
        "".join(f"{name}:{digest}" for name, digest in sorted(files.items())).encode("utf-8")
    ).hexdigest()
    return {"files": files, "combined": combined, "short": combined[:12]}


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict]:
    """Read a CSV, skipping ``#`` comment lines and blank lines.

    Comments are allowed so the raw files can carry their own column
    documentation without a separate data dictionary drifting out of date.
    """
    path = Path(path)
    if not path.exists():
        raise DataError(f"missing data file: {path}")
    kept = []
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        kept.append(line)
    if not kept:
        raise DataError(f"{path} has a header row missing")
    reader = csv.DictReader(io.StringIO("\n".join(kept)))
    rows = []
    for row in reader:
        clean = {}
        for key, value in row.items():
            if key is None:
                continue
            clean[str(key).strip()] = ("" if value is None else str(value).strip())
        if not clean or all(value == "" for value in clean.values()):
            continue
        rows.append(clean)
    return rows


def csv_fieldnames(path: Path) -> list[str]:
    path = Path(path)
    if not path.exists():
        raise DataError(f"missing data file: {path}")
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return [part.strip() for part in stripped.split(",")]
    raise DataError(f"{path} has a header row missing")


# --------------------------------------------------------------------------
# value parsing (blank stays None; never invent a zero)
# --------------------------------------------------------------------------

def parse_date(value) -> date | None:
    text = (value or "").strip()
    if not DATE_RE.match(text):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_time(value):
    text = (value or "").strip()
    if not TIME_RE.match(text):
        return None
    hour, minute = text.split(":")
    try:
        return time(int(hour) % 24, int(minute) % 60)
    except ValueError:
        return None


def parse_float(value):
    text = (value or "").strip().replace(",", ".")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value):
    text = (value or "").strip().lower()
    if text in {"yes", "y", "true", "1", "ok"}:
        return True
    if text in {"no", "n", "false", "0"}:
        return False
    return None


def fmt_num(value, digits: int = 1) -> str:
    """Format a number for the page: no trailing .0, no invented precision."""
    if value is None:
        return "—"
    number = float(value)
    if abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def esc(value) -> str:
    """Escape anything that comes from data before it reaches the HTML."""
    return html.escape("" if value is None else str(value), quote=True)


def human_bytes(size: int) -> str:
    if size < 1000:
        return f"{size} B"
    if size < 1000000:
        return f"{size / 1000:.1f} kB"
    return f"{size / 1000000:.2f} MB"


def setup_console() -> None:
    """Windows consoles default to a code page that cannot print “·” or Bangla.

    The build and check scripts print both, so switch the streams to UTF-8 and
    never let a decorative character crash a build.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or "item"
