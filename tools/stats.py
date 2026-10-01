"""Turn the typed raw data into every number the website is allowed to show.

Each interesting figure carries the row ids it was computed from, so the
"no invented statistics" check in tools/check.py has something concrete to
compare against.
"""

from __future__ import annotations

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from dataset import DAY_PARTS  # noqa: E402

AUDITABLE_COLUMNS = [
    "wait_minutes", "timing_method", "walked_away", "day_part", "queue_length",
    "people_ahead", "time_start", "time_end", "weather", "observer",
    "evidence_photo_id", "notes",
]
MAX_BUCKETS = 10


def _median(values):
    return statistics.median(values) if values else None


def _mean(values):
    return statistics.fmean(values) if values else None


def _p90(values):
    """Nearest-rank 90th percentile: the slowest wait in the fastest 90%."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(0.9 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def _stdev(values):
    return statistics.stdev(values) if len(values) > 1 else None


def _buckets(pairs, width, max_buckets=MAX_BUCKETS):
    """Fixed-width histogram buckets. The last bucket is labelled open-ended only
    when a value actually sits at or above its upper edge."""
    if not pairs:
        return []
    top = max(value for value, _ in pairs)
    if top < width:
        count = 1
    else:
        count = max(1, min(max_buckets, int(top // width) + 1))
    buckets = []
    for index in range(count):
        lo = index * width
        hi = lo + width
        last = index == count - 1
        open_ended = bool(last and top >= hi)
        if count == 1:
            label = f"0–{common.fmt_num(width - 1)}"
        elif open_ended:
            label = f"{common.fmt_num(lo)}+"
        else:
            label = f"{common.fmt_num(lo)}–{common.fmt_num(hi - 1)}"
        buckets.append({
            "lo": lo, "hi": hi, "label": label, "open_ended": open_ended,
            "count": 0, "row_ids": [],
        })
    for value, row_id in pairs:
        index = min(int(value // width), count - 1)
        buckets[index]["count"] += 1
        buckets[index]["row_ids"].append(row_id)
    return buckets


def compute(dataset, site) -> dict:
    width = float(site.get("bucket_width_minutes") or 5)
    target = int(site.get("target_observations") or 0)
    photo_target = int(site.get("target_photos") or 0)
    threshold = float(site.get("slow_wait_minutes") or 15)
    min_place_n = int(site.get("headline_min_place_n") or 3)

    observations = dataset.observations
    timed = dataset.timed
    waits = [row["wait_minutes"] for row in timed]
    dates = sorted({row["date"] for row in observations if row["date"]})

    # ---- wait time ------------------------------------------------------
    longest = max(timed, key=lambda row: row["wait_minutes"]) if timed else None
    wait = {
        "count": len(waits),
        "median": _median(waits),
        "mean": _mean(waits),
        "min": min(waits) if waits else None,
        "max": max(waits) if waits else None,
        "p90": _p90(waits),
        "stdev": _stdev(waits),
        "total_minutes": sum(waits) if waits else None,
        "over_threshold": sum(1 for value in waits if value > threshold),
        "threshold": threshold,
        "longest": None if not longest else {
            "id": longest["id"],
            "minutes": longest["wait_minutes"],
            "place_id": longest["place_id"],
            "date": longest["date_raw"],
            "row_ids": [longest["id"]],
        },
    }

    # ---- by place -------------------------------------------------------
    by_place = []
    for place in dataset.places:
        rows = [row for row in observations if row["place_id"] == place["place_id"]]
        place_waits = [row["wait_minutes"] for row in rows if row["wait_minutes"] is not None]
        by_place.append({
            "place_id": place["place_id"],
            "name_en": place["name_en"],
            "name_bn": place["name_bn"],
            "description_en": place["description_en"],
            "description_bn": place["description_bn"],
            "diagram_x": place["diagram_x"],
            "diagram_y": place["diagram_y"],
            "lat": place["lat"],
            "lon": place["lon"],
            "count": len(rows),
            "timed_count": len(place_waits),
            "median": _median(place_waits),
            "mean": _mean(place_waits),
            "max": max(place_waits) if place_waits else None,
            "total_minutes": sum(place_waits) if place_waits else None,
            "queue_median": _median([row["queue_length"] for row in rows if row["queue_length"] is not None]),
            "row_ids": [row["id"] for row in rows],
            "low_n": 0 < len(place_waits) < min_place_n,
        })

    # ---- by day ---------------------------------------------------------
    by_day = []
    cumulative = 0.0
    for day in dates:
        rows = [row for row in observations if row["date"] == day]
        day_waits = [row["wait_minutes"] for row in rows if row["wait_minutes"] is not None]
        total = sum(day_waits) if day_waits else None
        if total is not None:
            cumulative = round(cumulative + total, 2)
        by_day.append({
            "date": day.isoformat(),
            "count": len(rows),
            "timed_count": len(day_waits),
            "total_minutes": total,
            "cumulative_minutes": round(cumulative, 2) if total is not None else None,
            "row_ids": [row["id"] for row in rows],
        })

    # ---- by part of day -------------------------------------------------
    by_day_part = []
    for part in DAY_PARTS:
        rows = [row for row in observations if row["day_part"] == part]
        if not rows:
            continue
        part_waits = [row["wait_minutes"] for row in rows if row["wait_minutes"] is not None]
        by_day_part.append({
            "part": part,
            "count": len(rows),
            "timed_count": len(part_waits),
            "median": _median(part_waits),
            "mean": _mean(part_waits),
            "row_ids": [row["id"] for row in rows],
        })
    covered_parts = [entry["part"] for entry in by_day_part]
    missing_parts = [part for part in DAY_PARTS if part not in covered_parts]

    # ---- how the waits were measured -----------------------------------
    timing = {method: 0 for method in ("stopwatch", "estimate", "self_report")}
    for row in timed:
        if row["timing_method"] in timing:
            timing[row["timing_method"]] += 1
    method_total = sum(timing.values())
    timing["total"] = method_total
    timing["measured_share"] = round(timing["stopwatch"] / method_total * 100) if method_total else None

    # ---- what is missing ------------------------------------------------
    missing = {}
    for column in AUDITABLE_COLUMNS:
        blanks = [row for row in observations if not row["__raw__"].get(column)]
        if blanks:
            missing[column] = len(blanks)

    walked = {
        "yes": sum(1 for row in observations if row["walked_away"] is True),
        "no": sum(1 for row in observations if row["walked_away"] is False),
    }
    walked["known"] = walked["yes"] + walked["no"]
    walked["unknown"] = len(observations) - walked["known"]
    walked["rate"] = round(walked["yes"] / walked["known"] * 100) if walked["known"] else None

    # ---- coverage -------------------------------------------------------
    span_days = (dates[-1] - dates[0]).days + 1 if dates else 0
    coverage = {
        "target": target,
        "collected": len(observations),
        "remaining": max(0, target - len(observations)),
        "percent": round(len(observations) / target * 100) if target else 0,
        "days_distinct": len(dates),
        "span_days": span_days,
        "gap_days": span_days - len(dates),
        "first_date": dates[0].isoformat() if dates else "",
        "last_date": dates[-1].isoformat() if dates else "",
        "date_range": f"{dates[0].isoformat()} → {dates[-1].isoformat()}" if dates else "",
        "photo_target": photo_target,
        "photos": len(dataset.photos),
        "photos_remaining": max(0, photo_target - len(dataset.photos)),
        "places_total": len(dataset.places),
        "places_with_data": sum(1 for place in by_place if place["count"] > 0),
        "timed": len(waits),
        "untimed": len(observations) - len(waits),
    }

    # ---- the headline finding ------------------------------------------
    headline = _headline(by_place, waits, timed, threshold, min_place_n, dataset)

    # ---- honest audit ---------------------------------------------------
    audit = _audit(dataset, coverage, timing, missing, walked, by_place, threshold, min_place_n)

    photos = [{
        "photo_id": photo["photo_id"],
        "file": photo["file"],
        "src": f"assets/photos/{photo['file']}",
        "place_id": photo["place_id"],
        "place_name_en": dataset.place_name(photo["place_id"], "en"),
        "place_name_bn": dataset.place_name(photo["place_id"], "bn"),
        "caption_en": photo["caption_en"],
        "caption_bn": photo["caption_bn"],
        "alt_en": photo["alt_en"],
        "alt_bn": photo["alt_bn"],
        "taken_at": photo["taken_at"],
        "subject": photo["subject"],
    } for photo in dataset.photos]

    buckets = _buckets([(row["wait_minutes"], row["id"]) for row in timed], width)
    provenance = {
        "median_wait": [row["id"] for row in timed],
        "longest_wait": wait["longest"]["row_ids"] if wait["longest"] else [],
        "buckets": {bucket["label"]: bucket["row_ids"] for bucket in buckets},
        "by_place": {place["place_id"]: place["row_ids"] for place in by_place if place["row_ids"]},
        "by_day": {day["date"]: day["row_ids"] for day in by_day},
        "headline": headline["row_ids"],
    }

    return {
        "coverage": coverage,
        "wait": wait,
        "buckets": buckets,
        "by_place": by_place,
        "by_day": by_day,
        "by_day_part": by_day_part,
        "covered_parts": covered_parts,
        "missing_parts": missing_parts,
        "timing": timing,
        "missing": missing,
        "walked": walked,
        "headline": headline,
        "audit": audit,
        "photos": photos,
        "interview": dataset.interview,
        "observers": dataset.observers,
        "provenance": provenance,
        "threshold": threshold,
        "min_place_n": min_place_n,
    }


def _headline(by_place, waits, timed, threshold, min_place_n, dataset) -> dict:
    """Pick the strongest finding with a rule that can be stated out loud."""
    eligible = [place for place in by_place if place["timed_count"] >= max(2, min_place_n)]
    if len(eligible) >= 2 and len(waits) >= 6:
        best = max(eligible, key=lambda place: (place["median"] or 0))
        return {
            "kind": "place_median",
            "rule_key": "place_median",
            "place_id": best["place_id"],
            "place_name_en": best["name_en"],
            "place_name_bn": best["name_bn"],
            "median": best["median"],
            "n": best["timed_count"],
            "min_n": min_place_n,
            "row_ids": best["row_ids"],
        }
    slow = [row for row in timed if row["wait_minutes"] > threshold]
    if len(waits) >= 4 and slow:
        best = max(slow, key=lambda row: row["wait_minutes"])
        return {
            "kind": "share_over",
            "rule_key": "share_over",
            "over": len(slow),
            "n": len(waits),
            "pct": round(len(slow) / len(waits) * 100),
            "threshold": threshold,
            "minutes": best["wait_minutes"],
            "place_id": best["place_id"],
            "place_name_en": dataset.place_name(best["place_id"], "en"),
            "place_name_bn": dataset.place_name(best["place_id"], "bn"),
            "date": best["date_raw"],
            "row_ids": [row["id"] for row in slow],
        }
    if timed:
        best = max(timed, key=lambda row: row["wait_minutes"])
        return {
            "kind": "longest_wait",
            "rule_key": "longest_wait",
            "minutes": best["wait_minutes"],
            "place_id": best["place_id"],
            "place_name_en": dataset.place_name(best["place_id"], "en"),
            "place_name_bn": dataset.place_name(best["place_id"], "bn"),
            "date": best["date_raw"],
            "n": len(waits),
            "row_ids": [best["id"]],
        }
    return {
        "kind": "no_timed",
        "rule_key": "no_timed",
        "n": 0,
        "logged": len(dataset.observations),
        "row_ids": [],
    }


def _audit(dataset, coverage, timing, missing, walked, by_place, threshold, min_place_n) -> list[dict]:
    """Honest limits, derived from the data rather than written from memory."""
    findings: list[dict] = []

    if coverage["collected"] < coverage["target"]:
        findings.append({"key": "not_enough_yet", "params": {
            "collected": coverage["collected"], "target": coverage["target"],
            "remaining": coverage["remaining"]}})

    findings.append({"key": "self_selected_times", "params": {}})
    findings.append({"key": "single_observer_watch", "params": {}})

    if len(dataset.observers) == 1:
        findings.append({"key": "one_observer", "params": {"observer": dataset.observers[0]}})
    elif dataset.observers:
        findings.append({"key": "observer_count", "params": {"count": len(dataset.observers)}})

    if coverage["days_distinct"] == 1:
        findings.append({"key": "single_day", "params": {"date": coverage["first_date"]}})
    elif 0 < coverage["days_distinct"] < 3:
        findings.append({"key": "few_days", "params": {"days": coverage["days_distinct"]}})

    if coverage["span_days"] >= 2 and coverage["gap_days"] > 0:
        findings.append({"key": "day_gaps", "params": {
            "span_days": coverage["span_days"], "days": coverage["days_distinct"],
            "gap_days": coverage["gap_days"]}})

    if coverage["collected"] and not coverage["timed"]:
        findings.append({"key": "no_timed_waits", "params": {"logged": coverage["collected"]}})

    if timing["total"] and timing["estimate"]:
        findings.append({"key": "estimate_share", "params": {
            "estimates": timing["estimate"], "total": timing["total"],
            "share": round(timing["estimate"] / timing["total"] * 100)}})

    if coverage["collected"] and not coverage["photos"]:
        findings.append({"key": "no_photos_yet", "params": {"logged": coverage["collected"]}})
    elif coverage["photos"] < coverage["photo_target"]:
        findings.append({"key": "photo_gap", "params": {
            "photos": coverage["photos"], "target": coverage["photo_target"],
            "remaining": coverage["photos_remaining"]}})

    low_n = [place for place in by_place if place["low_n"]]
    if low_n:
        findings.append({"key": "low_n_places", "params": {
            "place_ids": [place["place_id"] for place in low_n], "min_n": min_place_n}})

    empty_places = [place for place in by_place if place["count"] == 0]
    if empty_places and coverage["places_total"]:
        findings.append({"key": "places_without_data", "params": {
            "place_ids": [place["place_id"] for place in empty_places]}})

    if missing.get("wait_minutes"):
        findings.append({"key": "missing_waits", "params": {
            "blank": missing["wait_minutes"], "total": coverage["collected"]}})

    if missing.get("evidence_photo_id"):
        findings.append({"key": "rows_without_photo", "params": {
            "blank": missing["evidence_photo_id"], "total": coverage["collected"]}})

    if walked["unknown"] and walked["unknown"] >= max(1, coverage["collected"] // 2):
        findings.append({"key": "walkaway_unknown", "params": {
            "blank": walked["unknown"], "total": coverage["collected"]}})

    covered_parts = dataset_part_names(dataset)
    if len(covered_parts) == 1:
        findings.append({"key": "single_day_part", "params": {"part_key": covered_parts[0]}})
    elif 1 < len(covered_parts) < len(DAY_PARTS):
        findings.append({"key": "partial_day_parts", "params": {"covered_keys": covered_parts}})

    findings.append({"key": "no_baseline", "params": {"threshold": threshold}})
    findings.append({"key": "weather_not_controlled", "params": {}})
    findings.append({"key": "no_cause", "params": {}})
    findings.append({"key": "cannot_generalise", "params": {"places": coverage["places_total"]}})
    return findings


def dataset_part_names(dataset) -> list[str]:
    """Which parts of the day actually have observations, in clock order."""
    seen = []
    for part in DAY_PARTS:
        if any(row["day_part"] == part for row in dataset.observations):
            seen.append(part)
    return seen
