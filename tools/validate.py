"""Validate the inputs: raw data, wording, and readiness to publish.

Two levels of strictness:

* normal build — everything that would put a wrong number or a broken page on
  the site is an error; anything still being collected is a warning;
* ``--publish`` — the gates that matter for the assignment (real data, real
  photos, the interview, reviewed Bangla, a public URL) have to be satisfied.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
import content as content_mod  # noqa: E402
from dataset import load_dataset  # noqa: E402

ERROR = "error"
WARN = "warn"
INFO = "info"

REQUIRED_IDENTITY = (
    "student_name", "student_id", "course", "institution",
    "problem_title_en", "problem_title_bn", "site_url", "repo_url", "contact_email",
)
PUBLISH_MIN_PLACES = 2


def _finding(level, message):
    return {"level": level, "message": message}


def _content_keys(tree):
    return {key for key, _value in content_mod.iter_strings(tree)}


def check_content(root, findings, publish):
    """Wording: parity between languages, no typed-in numbers, nothing blank."""
    try:
        english = common.load_json(root / "src" / "content.en.json")
        bangla = common.load_json(root / "src" / "content.bn.json")
    except common.BuildError as exc:
        findings.append(_finding(ERROR, str(exc)))
        return

    en_keys = _content_keys(english)
    bn_keys = _content_keys(bangla)
    for key in sorted(en_keys - bn_keys):
        findings.append(_finding(ERROR, f"content.bn.json is missing {key}"))
    for key in sorted(bn_keys - en_keys):
        findings.append(_finding(ERROR, f"content.en.json is missing {key}"))

    allowlist = set()
    allow_path = root / "src" / "number-allowlist.json"
    if allow_path.exists():
        allowlist = set(common.load_json(allow_path).get("keys", []))

    for lang, tree in (("en", english), ("bn", bangla)):
        for key, _value in content_mod.iter_strings(tree):
            if _value.strip() == "":
                findings.append(_finding(ERROR, f"content.{lang}.json: {key} is empty"))
        for key, value in content_mod.find_bare_numbers(tree):
            if key in allowlist:
                continue
            findings.append(_finding(
                ERROR,
                f"content.{lang}.json: {key} contains a digit outside a token — "
                f"write it as a {{{{stat:...}}}} token or add the key to src/number-allowlist.json: {value!r}",
            ))
    if allowlist:
        findings.append(_finding(INFO, f"digit allowlist (definitions, not measurements): {', '.join(sorted(allowlist))}"))

    status_path = root / "src" / "bn-status.json"
    status = common.load_json(status_path) if status_path.exists() else {}
    if not status.get("reviewed_all") or not str(status.get("reviewer") or "").strip():
        level = ERROR if publish else WARN
        findings.append(_finding(
            level,
            "Bangla wording has not been signed off: set reviewer and reviewed_all in "
            "src/bn-status.json once you have read every line of docs/bangla-review.md",
        ))
    return english, bangla


def check_site_config(root, findings, publish):
    site = common.load_json(root / "src" / "site.json")
    for field in REQUIRED_IDENTITY:
        value = str(site.get(field) or "").strip()
        if not value:
            findings.append(_finding(
                ERROR if publish else WARN,
                f"src/site.json: {field} is empty",
            ))
    site_url = str(site.get("site_url") or "").strip()
    if site_url and not site_url.startswith("https://"):
        findings.append(_finding(ERROR, "src/site.json: site_url must start with https:// so the canonical links are right"))
    if site_url.endswith("/"):
        findings.append(_finding(WARN, "src/site.json: site_url should not end with a slash"))
    email = str(site.get("contact_email") or "").strip()
    if email and "@" not in email:
        findings.append(_finding(ERROR, f"src/site.json: contact_email {email!r} is not an email address"))
    for field in ("target_observations", "target_photos", "slow_wait_minutes", "bucket_width_minutes", "headline_min_place_n"):
        value = site.get(field)
        if not isinstance(value, (int, float)) or value <= 0:
            findings.append(_finding(ERROR, f"src/site.json: {field} must be a positive number (found {value!r})"))
    return site


def check_data(root, findings, site, publish):
    try:
        dataset = load_dataset(root)
    except common.BuildError as exc:
        findings.append(_finding(ERROR, str(exc)))
        return None

    for message in dataset.errors:
        findings.append(_finding(ERROR, message))
    for message in dataset.warnings:
        findings.append(_finding(INFO if not publish else WARN, message))

    coverage_target = int(site.get("target_observations") or 0)
    photo_target = int(site.get("target_photos") or 0)
    collected = len(dataset.observations)
    photos = len(dataset.photos)

    hero_file = str(site.get("hero_photo_file") or "").strip()
    if hero_file:
        known = {photo["file"] for photo in dataset.photos}
        if hero_file not in known:
            findings.append(_finding(
                WARN,
                f"src/site.json: hero_photo_file {hero_file!r} is not a row of data/photos.csv, so the "
                "hero shows the drawn illustration instead",
            ))

    if publish:
        if collected < coverage_target:
            findings.append(_finding(ERROR, f"only {collected} of {coverage_target} observations collected"))
        if photos < photo_target:
            findings.append(_finding(ERROR, f"only {photos} of {photo_target} photos recorded in data/photos.csv"))
        if len(dataset.places) < PUBLISH_MIN_PLACES:
            findings.append(_finding(ERROR, f"at least {PUBLISH_MIN_PLACES} places are needed before the comparison means anything"))
        if not dataset.interview.get("present"):
            findings.append(_finding(ERROR, "data/interview.md has no interview in it yet"))
        elif not dataset.interview.get("consent_ok"):
            findings.append(_finding(ERROR, "data/interview.md: consent_ok must be yes before the answers can be published"))
        else:
            for field in ("date", "mode"):
                if not str(dataset.interview.get(field) or "").strip():
                    findings.append(_finding(ERROR, f"data/interview.md: {field} is empty"))
            if dataset.interview.get("missing"):
                findings.append(_finding(WARN, "data/interview.md: some answers are missing in one of the languages"))

    timings = {}
    for row in dataset.observations:
        if row["timing_method"]:
            timings[row["timing_method"]] = timings.get(row["timing_method"], 0) + 1
    estimated = timings.get("estimate", 0)
    if estimated and dataset.observations:
        findings.append(_finding(
            INFO,
            f"{estimated} of {len(dataset.observations)} waits were estimated by eye rather than timed "
            "(the limitations page reports this automatically)",
        ))
    return dataset


def run(root, publish: bool = False):
    root = Path(root)
    findings: list[dict] = []
    site = check_site_config(root, findings, publish)
    check_content(root, findings, publish)
    check_data(root, findings, site, publish)
    return findings


def summarise(findings):
    errors = [item for item in findings if item["level"] == ERROR]
    warns = [item for item in findings if item["level"] == WARN]
    infos = [item for item in findings if item["level"] == INFO]
    return errors, warns, infos
