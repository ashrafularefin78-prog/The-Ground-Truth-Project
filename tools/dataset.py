"""Read the raw CSVs and turn them into typed rows.

Nothing in this module invents a value: a blank cell stays ``None`` and is
reported by the audit, never silently replaced with a zero.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from common import DataError  # noqa: E402

OBS_COLUMNS = [
    "id", "date", "time_start", "time_end", "place_id", "queue_length",
    "people_ahead", "wait_minutes", "timing_method", "walked_away", "day_part",
    "weather", "evidence_photo_id", "observer", "notes",
]
PLACE_COLUMNS = [
    "place_id", "name_en", "name_bn", "diagram_x", "diagram_y",
    "description_en", "description_bn", "lat", "lon",
]
PHOTO_COLUMNS = [
    "photo_id", "file", "place_id", "taken_at", "caption_en", "caption_bn",
    "alt_en", "alt_bn", "subject", "consent_ok",
]

DAY_PARTS = ("morning", "afternoon", "evening", "night")
TIMING_METHODS = ("stopwatch", "estimate", "self_report")
SUBJECTS = ("queue", "counter", "sign", "empty_spot", "other")
MAX_WAIT_MINUTES = 600


class Dataset:
    """Typed raw data plus the problems found while reading it."""

    def __init__(self, root):
        self.root = Path(root)
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.observations: list[dict] = []
        self.places: list[dict] = []
        self.photos: list[dict] = []
        self.interview: dict = {}
        self.place_by_id: dict[str, dict] = {}
        self.photo_by_id: dict[str, dict] = {}

    # -- convenience -------------------------------------------------------
    @property
    def timed(self) -> list[dict]:
        return [row for row in self.observations if row["wait_minutes"] is not None]

    @property
    def observers(self) -> list[str]:
        found = []
        for row in self.observations:
            if row["observer"] and row["observer"] not in found:
                found.append(row["observer"])
        return found

    def place_name(self, place_id: str, lang: str) -> str:
        place = self.place_by_id.get(place_id)
        if not place:
            return place_id
        key = "name_bn" if lang == "bn" else "name_en"
        return place.get(key) or place.get("name_en") or place_id


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------

def _check_columns(path: Path, expected: list[str], errors: list[str]) -> None:
    found = common.csv_fieldnames(path)
    missing = [name for name in expected if name not in found]
    extra = [name for name in found if name not in expected]
    if missing:
        errors.append(f"{path.name}: missing column(s): {', '.join(missing)}")
    if extra:
        errors.append(
            f"{path.name}: unexpected column(s): {', '.join(extra)} "
            "(fix the header or the site will ignore them)"
        )


def load_places(path: Path, errors: list[str], warnings: list[str]) -> list[dict]:
    _check_columns(path, PLACE_COLUMNS, errors)
    places = []
    seen = set()
    for index, row in enumerate(common.read_csv(path), start=2):
        place_id = row.get("place_id", "")
        if not common.PLACE_ID_RE.match(place_id):
            errors.append(f"{path.name} line {index}: place_id {place_id!r} must be lowercase letters, digits, - or _")
            continue
        if place_id in seen:
            errors.append(f"{path.name} line {index}: duplicate place_id {place_id!r}")
            continue
        seen.add(place_id)
        if not row.get("name_en") or not row.get("name_bn"):
            errors.append(f"{path.name} line {index}: {place_id} needs both name_en and name_bn")
        place = {
            "place_id": place_id,
            "name_en": row.get("name_en", ""),
            "name_bn": row.get("name_bn", ""),
            "description_en": row.get("description_en", ""),
            "description_bn": row.get("description_bn", ""),
            "diagram_x": common.parse_float(row.get("diagram_x")),
            "diagram_y": common.parse_float(row.get("diagram_y")),
            "lat": common.parse_float(row.get("lat")),
            "lon": common.parse_float(row.get("lon")),
        }
        for axis in ("diagram_x", "diagram_y"):
            value = place[axis]
            if value is None or not 0 <= value <= 100:
                errors.append(f"{path.name} line {index}: {place_id} {axis} must be a number from 0 to 100")
        place["row_number"] = index
        places.append(place)
    if not places:
        warnings.append(f"{path.name}: no places listed yet")
    return places


def load_observations(path: Path, place_ids: set, photo_ids: set, errors: list, warnings: list) -> list[dict]:
    _check_columns(path, OBS_COLUMNS, errors)
    observations = []
    seen = set()
    for index, row in enumerate(common.read_csv(path), start=2):
        label = row.get("id") or f"line {index}"
        obs_id = row.get("id", "")
        if not common.OBS_ID_RE.match(obs_id):
            errors.append(f"{path.name} line {index}: id {obs_id!r} should look like OBS-001")
        elif obs_id in seen:
            errors.append(f"{path.name} line {index}: duplicate id {obs_id!r}")
        seen.add(obs_id)

        day = common.parse_date(row.get("date"))
        if day is None:
            errors.append(f"{path.name} line {index} ({label}): date {row.get('date')!r} must be YYYY-MM-DD")
        for field in ("time_start", "time_end"):
            raw = row.get(field, "")
            if raw and common.parse_time(raw) is None:
                errors.append(f"{path.name} line {index} ({label}): {field} {raw!r} must be HH:MM")

        place_id = row.get("place_id", "")
        if place_id not in place_ids:
            errors.append(f"{path.name} line {index} ({label}): place_id {place_id!r} is not in places.csv")

        wait = common.parse_float(row.get("wait_minutes"))
        raw_wait = row.get("wait_minutes", "")
        if raw_wait and wait is None:
            errors.append(f"{path.name} line {index} ({label}): wait_minutes {raw_wait!r} is not a number")
        if wait is not None and not 0 <= wait <= MAX_WAIT_MINUTES:
            errors.append(f"{path.name} line {index} ({label}): wait_minutes {wait} is outside 0-{MAX_WAIT_MINUTES}")

        method = row.get("timing_method", "").lower()
        if method and method not in TIMING_METHODS:
            errors.append(
                f"{path.name} line {index} ({label}): timing_method {method!r} must be one of {', '.join(TIMING_METHODS)}"
            )

        start = common.parse_time(row.get("time_start"))
        day_part = row.get("day_part", "").lower()
        if day_part and day_part not in DAY_PARTS:
            errors.append(f"{path.name} line {index} ({label}): day_part {day_part!r} must be one of {', '.join(DAY_PARTS)}")
        if not day_part and start is not None:
            day_part = derive_day_part(start)
        if not day_part:
            warnings.append(f"{path.name} line {index} ({label}): no day_part and no usable time_start")

        photo_id = row.get("evidence_photo_id", "")
        if photo_id and photo_id not in photo_ids:
            errors.append(f"{path.name} line {index} ({label}): evidence_photo_id {photo_id!r} is not in photos.csv")

        if not raw_wait:
            warnings.append(f"{path.name} line {index} ({label}): no wait_minutes recorded")
        if not row.get("observer"):
            warnings.append(f"{path.name} line {index} ({label}): no observer name")

        observations.append({
            "__raw__": row,
            "id": obs_id,
            "row_number": index,
            "date": day,
            "date_raw": row.get("date", ""),
            "time_start": start,
            "time_end": common.parse_time(row.get("time_end")),
            "place_id": place_id,
            "queue_length": common.parse_float(row.get("queue_length")),
            "people_ahead": common.parse_float(row.get("people_ahead")),
            "wait_minutes": wait,
            "timing_method": method,
            "walked_away": common.parse_bool(row.get("walked_away")),
            "day_part": day_part,
            "weather": row.get("weather", ""),
            "evidence_photo_id": photo_id,
            "observer": row.get("observer", ""),
            "notes": row.get("notes", ""),
        })
    if not observations:
        warnings.append(f"{path.name}: no observations recorded yet")
    return observations


def derive_day_part(start) -> str:
    """Split the day exactly as the CSV comment documents it."""
    if start.hour < 12:
        return "morning"
    if start.hour < 17:
        return "afternoon"
    if start.hour < 21:
        return "evening"
    return "night"


def load_photos(path: Path, place_ids: set, photo_dir: Path, errors: list, warnings: list) -> list[dict]:
    _check_columns(path, PHOTO_COLUMNS, errors)
    photos = []
    seen = set()
    for index, row in enumerate(common.read_csv(path), start=2):
        photo_id = row.get("photo_id", "")
        label = photo_id or f"line {index}"
        if not common.PHOTO_ID_RE.match(photo_id):
            errors.append(f"{path.name} line {index}: photo_id {photo_id!r} should look like PH-001")
        elif photo_id in seen:
            errors.append(f"{path.name} line {index}: duplicate photo_id {photo_id!r}")
        seen.add(photo_id)

        filename = row.get("file", "")
        if not filename:
            errors.append(f"{path.name} line {index} ({label}): file is empty")
        elif not (photo_dir / filename).is_file():
            errors.append(f"{path.name} line {index} ({label}): {photo_dir.name}/{filename} does not exist")

        place_id = row.get("place_id", "")
        if place_id and place_id not in place_ids:
            errors.append(f"{path.name} line {index} ({label}): place_id {place_id!r} is not in places.csv")
        if not place_id:
            errors.append(f"{path.name} line {index} ({label}): place_id is empty")

        for field in ("caption_en", "caption_bn", "alt_en", "alt_bn", "subject", "taken_at"):
            if not row.get(field):
                errors.append(f"{path.name} line {index} ({label}): {field} is empty")
        for field in ("alt_en", "alt_bn"):
            value = row.get(field, "")
            if value and (value.lower() in {"image", "photo", "picture", "img"} or filename.lower() in value.lower()):
                errors.append(f"{path.name} line {index} ({label}): {field} must describe what is visible, not name the file")
        if row.get("subject") and row["subject"] not in SUBJECTS:
            errors.append(f"{path.name} line {index} ({label}): subject {row['subject']!r} must be one of {', '.join(SUBJECTS)}")
        if common.parse_date(row.get("taken_at")) is None:
            errors.append(f"{path.name} line {index} ({label}): taken_at {row.get('taken_at')!r} must be YYYY-MM-DD")
        if common.parse_bool(row.get("consent_ok")) is not True:
            errors.append(
                f"{path.name} line {index} ({label}): consent_ok must be 'yes' — nobody identifiable may be published without permission"
            )

        photos.append({
            "photo_id": photo_id,
            "file": filename,
            "place_id": place_id,
            "taken_at": row.get("taken_at", ""),
            "caption_en": row.get("caption_en", ""),
            "caption_bn": row.get("caption_bn", ""),
            "alt_en": row.get("alt_en", ""),
            "alt_bn": row.get("alt_bn", ""),
            "subject": row.get("subject", ""),
            "consent_ok": True,
        })
    if not photos:
        warnings.append(f"{path.name}: no photo evidence logged yet")
    return photos


# --------------------------------------------------------------------------
# interview
# --------------------------------------------------------------------------

INTERVIEW_FIELDS = ("person_label", "preferred_language", "place_id", "date", "mode", "duration_min")
BLOCK_PREFIXES = {"q": "q_en", "b": "q_bn", "a": "a_en", "c": "a_bn"}


def parse_interview(path: Path, errors: list, warnings: list, place_ids: set) -> dict:
    """Parse the note format documented at the top of data/interview.md."""
    result = {
        "present": False,
        "consent_ok": False,
        "person_label": "",
        "preferred_language": "",
        "place_id": "",
        "date": "",
        "mode": "",
        "duration_min": None,
        "quote_en": "",
        "quote_bn": "",
        "pairs": [],
        "missing": [],
    }
    if not Path(path).exists():
        errors.append("data/interview.md is missing")
        return result

    text = common.read_text(path)
    front_lines: list[str] = []
    blocks: list[list[str]] = []
    current: list[str] = []
    seen_separator = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped == "---":
            if not seen_separator:
                seen_separator = True
            else:
                blocks.append(current)
                current = []
            continue
        if seen_separator:
            current.append(line)
        else:
            front_lines.append(line)
    blocks.append(current)

    for line in front_lines:
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "consent_ok":
            result["consent_ok"] = common.parse_bool(value) is True
        elif key == "duration_min":
            result["duration_min"] = common.parse_float(value)
        elif key in result:
            result[key] = value

    for block in blocks:
        pair = {"q_en": "", "q_bn": "", "a_en": "", "a_bn": ""}
        field = None
        for line in block:
            stripped = line.strip()
            if len(stripped) > 2 and stripped[1] == ":" and stripped[0].lower() in BLOCK_PREFIXES:
                field = BLOCK_PREFIXES[stripped[0].lower()]
                pair[field] = stripped[2:].strip()
            elif field and stripped:
                pair[field] = (pair[field] + " " + stripped).strip()
        if any(pair.values()):
            result["pairs"].append(pair)

    complete_pairs = [p for p in result["pairs"] if p["a_en"] or p["a_bn"]]
    result["pairs"] = complete_pairs
    result["present"] = bool(complete_pairs or result["person_label"])

    for field in ("a_en", "a_bn"):
        for pair in result["pairs"]:
            if not pair[field]:
                result["missing"].append(field)
                break
    if result["place_id"] and result["place_id"] not in place_ids:
        errors.append(f"data/interview.md: place_id {result['place_id']!r} is not in places.csv")
    if result["present"] and common.parse_date(result["date"]) is None:
        warnings.append("data/interview.md: date is missing or not YYYY-MM-DD")
    if result["present"] and not result["person_label"]:
        errors.append("data/interview.md: person_label is empty (use an anonymised role label, not a real name)")
    if result["present"] and not result["consent_ok"]:
        warnings.append("data/interview.md: consent_ok is not yes — the answers stay off the site until it is")
    return result


# --------------------------------------------------------------------------

def load_dataset(root) -> Dataset:
    root = Path(root)
    data_dir = root / "data"
    dataset = Dataset(root)
    dataset.places = load_places(data_dir / "places.csv", dataset.errors, dataset.warnings)
    dataset.place_by_id = {place["place_id"]: place for place in dataset.places}
    dataset.photos = load_photos(
        data_dir / "photos.csv", set(dataset.place_by_id), data_dir / "photos",
        dataset.errors, dataset.warnings,
    )
    dataset.photo_by_id = {photo["photo_id"]: photo for photo in dataset.photos}
    dataset.observations = load_observations(
        data_dir / "observations.csv", set(dataset.place_by_id), set(dataset.photo_by_id),
        dataset.errors, dataset.warnings,
    )
    dataset.interview = parse_interview(
        data_dir / "interview.md", dataset.errors, dataset.warnings, set(dataset.place_by_id)
    )
    if not dataset.observations and not dataset.places and not dataset.photos:
        dataset.warnings.append("no field data yet — the site will show its honest empty state")
    return dataset
