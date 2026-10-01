"""Check the built site before it is published.

Run it after every build:

    py tools/check.py            full report
    py tools/check.py --publish  also enforce the gates that matter for submission

Nothing here trusts the build: it re-reads the generated HTML, re-measures the
page weight, recomputes the contrast ratios from src/theme.json, and compares
the data snapshot printed in every page against the current CSVs. If the CSV
changed after the last build, or a number in a page is not in data/stats.json,
this fails.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import validate  # noqa: E402
from dataset import load_dataset  # noqa: E402

PAGE_BUDGET = 1_000_000          # the assignment caps a page at one megabyte
PAGE_WARN = 400_000              # keep well clear of it, and say so early
ASSET_RE = re.compile(r'(?:src|href)="([^"#?]+\.(?:css|js|png|jpe?g|webp|avif|svg|mp3|m4a|ogg))"', re.I)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
ALT_RE = re.compile(r'alt="([^"]*)"', re.I)
ID_RE = re.compile(r'id="([^"]+)"', re.I)
LABEL_RE = re.compile(r'<label\b[^>]*for="([^"]+)"', re.I)
HREF_RE = re.compile(r'href="([^"]+)"', re.I)
H1_RE = re.compile(r"<h1\b", re.I)
SNAPSHOT_RE = re.compile(r'<meta name="data-snapshot" content="([0-9a-f]+)"')
PLACEHOLDER_PATTERNS = (
    "lorem", "ipsum", "todo", "tbd", "to be decided", "fixme", "xxx",
    "placeholder", "john doe", "jane doe", "example.com", "your name here",
    "sample text", "insert text", "untitled", "coming soon", "dummy",
)
FORBIDDEN_JS = (
    "innerHTML", "insertAdjacentHTML", "document.write", "outerHTML",
    "textContent =", "innerText =", "textContent=", "innerText=",
)


def page_files(root: Path) -> list[Path]:
    pages = sorted(path for path in root.glob("*.html"))
    pages += sorted((root / "bn").glob("*.html")) if (root / "bn").is_dir() else []
    return [page.relative_to(root).as_posix() for page in pages]


def relative_paths(root: Path, page: str, html: str) -> list[str]:
    found = []
    for match in ASSET_RE.finditer(html):
        href = match.group(1).strip()
        if href.startswith(("http://", "https://", "data:", "//")):
            continue
        found.append(((root / page).parent / href).resolve())
    return found


def check_weights(root: Path, pages: list[str], findings: list[dict]) -> list[tuple[str, int]]:
    weights = []
    for page in pages:
        html = common.read_text(root / page)
        total = len(html.encode("utf-8"))
        for asset in relative_paths(root, page, html):
            if asset.is_file():
                total += asset.stat().st_size
            else:
                findings.append({"level": validate.ERROR, "message": f"{page}: references a missing asset {asset.name}"})
        weights.append((page, total))
        if total > PAGE_BUDGET:
            findings.append({
                "level": validate.ERROR,
                "message": f"{page} weighs {common.human_bytes(total)}, over the {common.human_bytes(PAGE_BUDGET)} per-page limit",
            })
        elif total > PAGE_WARN:
            findings.append({
                "level": validate.WARN,
                "message": f"{page} weighs {common.human_bytes(total)}, close to the limit — check the photos first",
            })
    return weights


def _luminance(hex_colour: str) -> float:
    value = hex_colour.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(part * 2 for part in value)
    channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    first, second = _luminance(foreground), _luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(root: Path, findings: list[dict]) -> list[tuple[str, float, float]]:
    theme = common.load_json(root / "src" / "theme.json")
    results = []
    for pair in theme.get("contrast_pairs", []):
        ratio = contrast_ratio(pair["fg"], pair["bg"])
        results.append((f"{pair['scheme']} {pair['label']}", ratio, pair["min"]))
        if ratio + 0.005 < pair["min"]:
            findings.append({
                "level": validate.ERROR,
                "message": f"contrast: {pair['scheme']} {pair['label']} is {ratio:.2f}:1, below {pair['min']}:1",
            })
    return results


def check_markup(root: Path, pages: list[str], findings: list[dict], publish: bool = False) -> None:
    for page in pages:
        html = common.read_text(root / page)

        if "{{" in html or "}}" in html:
            findings.append({"level": validate.ERROR, "message": f"{page}: an unresolved {{{{token}}}} was printed"})

        for tag in IMG_RE.findall(html):
            alt = ALT_RE.search(tag)
            if alt is None:
                findings.append({"level": validate.ERROR, "message": f"{page}: an img has no alt attribute"})
            elif not alt.group(1).strip():
                findings.append({"level": validate.ERROR, "message": f"{page}: an img has an empty alt attribute"})

        labels = set(LABEL_RE.findall(html))
        for match in re.finditer(r"<input\b[^>]*>|<textarea\b[^>]*>|<select\b[^>]*>", html, re.I):
            tag = match.group(0)
            if 'type="hidden"' in tag or 'type="submit"' in tag:
                continue
            identifier = ID_RE.search(tag)
            if identifier is None:
                findings.append({"level": validate.ERROR, "message": f"{page}: a form control has no id"})
            elif identifier.group(1) not in labels:
                findings.append({
                    "level": validate.ERROR,
                    "message": f"{page}: form control {identifier.group(1)} has no label pointing at it",
                })

        if len(H1_RE.findall(html)) != 1:
            findings.append({"level": validate.WARN, "message": f"{page}: expected exactly one h1 heading"})

        lang = re.search(r'<html lang="([a-z-]+)"', html)
        if lang is None:
            findings.append({"level": validate.ERROR, "message": f"{page}: html element has no lang attribute"})

        for match in HREF_RE.finditer(html):
            href = match.group(1).strip()
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:", "//")) or not href:
                continue
            target = ((root / page).parent / href.split("#")[0].split("?")[0]).resolve()
            if not target.exists():
                findings.append({"level": validate.ERROR, "message": f"{page}: link to {href} does not exist"})

        for pattern in PLACEHOLDER_PATTERNS:
            if pattern in html.lower():
                findings.append({
                    "level": validate.ERROR,
                    "message": f"{page}: leftover placeholder wording ({pattern!r})",
                })

        if 'data-bn-review="pending"' in html:
            findings.append({
                "level": validate.ERROR if publish else validate.WARN,
                "message": f"{page}: carries the Bangla review-pending note — sign off src/bn-status.json before submitting",
            })


def strip_comments(source: str) -> str:
    """Comments may explain the rule; only real code is checked."""
    without_block = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    return re.sub(r"//[^\n]*", "", without_block)


def check_script(root: Path, findings: list[dict]) -> None:
    path = root / "assets" / "app.js"
    if not path.exists():
        findings.append({"level": validate.ERROR, "message": "assets/app.js is missing"})
        return
    script = strip_comments(common.read_text(path))
    for pattern in FORBIDDEN_JS:
        if pattern in script:
            findings.append({
                "level": validate.ERROR,
                "message": f"assets/app.js uses {pattern!r}: the no-JavaScript change request would break the page content",
            })
    if len(script.encode("utf-8")) > 20_000:
        findings.append({"level": validate.WARN, "message": "assets/app.js is bigger than expected for an enhancement-only file"})


def check_freshness(root: Path, pages: list[str], findings: list[dict]) -> dict:
    fingerprint = common.data_fingerprint(root)
    for page in pages:
        html = common.read_text(root / page)
        match = SNAPSHOT_RE.search(html)
        if match is None:
            findings.append({"level": validate.ERROR, "message": f"{page}: no data snapshot stamp — rebuild it"})
        elif match.group(1) != fingerprint["combined"]:
            findings.append({
                "level": validate.ERROR,
                "message": f"{page}: built from an older CSV ({match.group(1)[:12]}) — run py tools/build.py",
            })
    stats_path = root / "data" / "stats.json"
    if not stats_path.exists():
        findings.append({"level": validate.ERROR, "message": "data/stats.json is missing — run py tools/build.py"})
        return fingerprint
    stats = json.loads(common.read_text(stats_path))
    if stats.get("generated", {}).get("data_hash") != fingerprint["combined"]:
        findings.append({"level": validate.ERROR, "message": "data/stats.json is older than the CSV — run py tools/build.py"})
    return fingerprint


def check_provenance(root: Path, findings: list[dict]) -> None:
    stats_path = root / "data" / "stats.json"
    if not stats_path.exists():
        return
    payload = json.loads(common.read_text(stats_path))
    stats = payload.get("stats", {})
    dataset = load_dataset(root)
    known = {row["id"] for row in dataset.observations}

    provenance = stats.get("provenance", {})
    cited = set(provenance.get("median_wait", []))
    for ids in provenance.get("buckets", {}).values():
        cited.update(ids)
    for ids in provenance.get("by_place", {}).values():
        cited.update(ids)
    for ids in provenance.get("by_day", {}).values():
        cited.update(ids)
    cited.update(provenance.get("longest_wait", []))
    cited.update(provenance.get("headline", []))
    unknown = sorted(cited - known)
    if unknown:
        findings.append({
            "level": validate.ERROR,
            "message": f"a chart cites rows that are not in the CSV: {', '.join(unknown[:6])}",
        })

    collected = stats.get("coverage", {}).get("collected")
    if collected is not None and collected != len(dataset.observations):
        findings.append({
            "level": validate.ERROR,
            "message": f"stats.json says {collected} observations but the CSV holds {len(dataset.observations)} — rebuild",
        })


def run(root: Path, publish: bool = False):
    root = Path(root)
    findings: list[dict] = []
    pages = page_files(root)
    expected = ["index.html", "data.html", "map.html", "action.html", "summary.html", "limitations.html", "404.html"]
    for name in expected:
        if name not in pages:
            findings.append({"level": validate.ERROR, "message": f"{name} was not built"})
        if f"bn/{name}" not in pages:
            findings.append({"level": validate.ERROR, "message": f"bn/{name} was not built"})

    weights = check_weights(root, pages, findings)
    check_markup(root, pages, findings, publish)
    check_script(root, findings)
    fingerprint = check_freshness(root, pages, findings)
    check_provenance(root, findings)
    contrasts = check_contrast(root, findings)
    findings.extend(validate.run(root, publish))
    return {
        "findings": findings,
        "weights": weights,
        "contrasts": contrasts,
        "snapshot": fingerprint["short"],
        "pages": pages,
        "publish": publish,
    }


def main(argv=None) -> int:
    common.setup_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    root = common.repo_root()
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1])
    publish = "--publish" in argv
    report = run(root, publish)
    errors, warns, infos = validate.summarise(report["findings"])

    print("=" * 72)
    print(f"Ground Truth check — data snapshot {report['snapshot']}" + (" — publish gate ON" if publish else ""))
    print("=" * 72)
    print("\nPage weight (HTML + CSS + JS + every image on the page):")
    for page, size in sorted(report["weights"], key=lambda item: -item[1]):
        flag = "OVER LIMIT" if size > PAGE_BUDGET else ("close" if size > PAGE_WARN else "ok")
        print(f"  {page:24s} {common.human_bytes(size):>10s}  {flag}")
    print(f"  limit: {common.human_bytes(PAGE_BUDGET)} per page")
    print("\nContrast (WCAG AA from src/theme.json):")
    worst = sorted(report["contrasts"], key=lambda item: item[1] / item[2])[:3]
    for label, ratio, minimum in worst:
        print(f"  {ratio:5.2f}:1  (min {minimum}:1)  {label}")
    verdict = "FAILED" if errors else ("passed with warnings" if warns else "passed")
    print(f"\nResult: {verdict} — {len(errors)} error(s), {len(warns)} warning(s), {len(infos)} note(s)")
    if infos:
        print(f"\n{len(infos)} note(s):")
        for item in infos[:20]:
            print(f"  · {item['message']}")
    if warns:
        print(f"\n{len(warns)} warning(s):")
        for item in warns[:25]:
            print(f"  ! {item['message']}")
        if len(warns) > 25:
            print(f"  ... and {len(warns) - 25} more")
    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for item in errors[:30]:
            print(f"  X {item['message']}")
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
