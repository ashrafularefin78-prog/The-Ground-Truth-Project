"""Tests for the Ground Truth build pipeline.

    py tools/tests/run_tests.py

Every fixture here is synthetic and is written into a temporary folder, then
deleted. None of it ever reaches data/ or the published site: the point is to
prove the engine reacts to raw data correctly, including the cases the site
only meets once real observations arrive.

The tests that matter most:

* a synthetic CSV produces the median that is actually in the CSV;
* changing one number in the CSV changes the chart and the sentence;
* an empty data folder still builds a clean site with no figures in it.
"""

from __future__ import annotations

import base64
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import art  # noqa: E402
import build  # noqa: E402
import charts  # noqa: E402
import check  # noqa: E402
import common  # noqa: E402
import content as content_mod  # noqa: E402
import stats as stats_mod  # noqa: E402
import validate  # noqa: E402
from dataset import derive_day_part, load_dataset, parse_interview  # noqa: E402

PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg=="
)

PLACES_HEADER = "place_id,name_en,name_bn,diagram_x,diagram_y,description_en,description_bn,lat,lon"
OBS_HEADER = (
    "id,date,time_start,time_end,place_id,queue_length,people_ahead,wait_minutes,"
    "timing_method,walked_away,day_part,weather,evidence_photo_id,observer,notes"
)
PHOTOS_HEADER = (
    "photo_id,file,place_id,taken_at,caption_en,caption_bn,alt_en,alt_bn,subject,consent_ok"
)

PLACES = [
    "alpha,Counter Alpha,কাউন্টার আলফা,20,30,Main counter,প্রধান কাউন্টার,23.75,90.39",
    "beta,Counter Beta,কাউন্টার বিটা,70,55,Side counter,পাশের কাউন্টার,23.76,90.40",
    "gamma,Counter Gamma,কাউন্টার গামা,45,80,Back counter,পেছনের কাউন্টার,,",
]

OBSERVATIONS = [
    "OBS-001,2026-03-02,09:30,09:35,alpha,4,3,5,stopwatch,yes,morning,sun,PH-001,Test collector,straightforward wait",
    "OBS-002,2026-03-02,09:45,09:52,alpha,5,4,7,stopwatch,no,morning,sun,,Test collector,till jammed",
    "OBS-003,2026-03-02,13:10,13:19,alpha,6,5,9,estimate,yes,afternoon,hot,,Test collector,longer at midday",
    "OBS-004,2026-03-03,13:20,13:31,alpha,7,6,11,stopwatch,no,afternoon,hot,,Test collector,",
    "OBS-005,2026-03-03,18:05,18:25,beta,9,8,20,stopwatch,yes,evening,rain,,Test collector,worst in the evening",
    "OBS-006,2026-03-03,18:30,18:52,beta,10,9,22,stopwatch,yes,evening,rain,PH-002,Test collector,",
    "OBS-007,2026-03-04,19:00,19:25,beta,11,10,25,estimate,yes,evening,rain,,Test collector,queue past the door",
]

PHOTOS = [
    "PH-001,evidence-alpha.png,alpha,2026-03-02,Four people at the counter,কাউন্টারে চারজন,"
    "Four people standing at a narrow counter,কাউন্টারে চারজন মানুষ দাঁড়িয়ে আছে,queue,yes",
    "PH-002,evidence-beta.png,beta,2026-03-03,Eight people bunched at the shutter,শাটারের সামনে আটজন,"
    "Eight people bunched in front of a closed shutter,বন্ধ শাটারের সামনে আটজন মানুষ ভিড় করেছেন,queue,yes",
]

INTERVIEW = """person_label: Counter staff
preferred_language: both
place_id: beta
date: 2026-03-03
mode: in person at the counter
duration_min: 6
consent_ok: yes
quote_en: On the evening shift there is only one of me and everybody arrives at once.
quote_bn: সন্ধ্যার পালায় আমি একা, আর সবাই একসঙ্গে এসে পড়ে।

---

Q: What makes the queue worst?
B: লাইন সবচেয়ে খারাপ কেন হয়?
A: Everybody arrives together in the evening, and there is one person at the counter.
C: সন্ধ্যায় সবাই একসঙ্গে আসে, আর কাউন্টারে থাকি আমি একজন।

---

Q: Do people give up and leave?
B: অনেকে হাল ছেড়ে চলে যায় কি?
A: Yes, mostly the ones with a bus to catch.
C: হ্যাঁ, যাদের বাস ধরতে হয় তারা বেশিরভাগ সময় চলে যায়।
"""


def write_rows(path: Path, header: str, rows, comments=("synthetic test fixture",)):
    lines = [f"# {line}" for line in comments]
    lines.append(header)
    lines.extend(rows)
    common.write_text(path, "\n".join(lines) + "\n")


def make_root(tmp: Path, *, observations=OBSERVATIONS, places=PLACES, photos=PHOTOS, interview=INTERVIEW):
    """A throwaway copy of the real src/ folder plus the given raw data."""
    if (tmp / "src").exists():
        shutil.rmtree(tmp / "src")
    shutil.copytree(TOOLS.parent / "src", tmp / "src")
    data = tmp / "data"
    photos_dir = data / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    write_rows(data / "places.csv", PLACES_HEADER, places)
    write_rows(data / "observations.csv", OBS_HEADER, observations)
    write_rows(data / "photos.csv", PHOTOS_HEADER, photos)
    for row in photos:
        name = row.split(",")[1]
        (photos_dir / name).write_bytes(PNG_1PX)
    common.write_text(data / "interview.md", interview if interview is not None else "")
    return tmp


class TempCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="groundtruth-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def build_site(self, **kwargs):
        root = make_root(self.tmp, **kwargs)
        builder = build.Builder(root)
        builder.build()
        builder.write()
        return builder

    def build_with_site(self, **overrides):
        """Build the synthetic site with some fields changed in src/site.json."""
        root = make_root(self.tmp)
        path = root / "src" / "site.json"
        site = json.loads(common.read_text(path))
        site.update(overrides)
        common.write_text(path, json.dumps(site, ensure_ascii=False, indent=2))
        builder = build.Builder(root)
        builder.build()
        builder.write()
        return builder

    def build_other(self, **kwargs):
        """Build the same site in a second temporary folder, for comparisons."""
        other = Path(tempfile.mkdtemp(prefix="groundtruth-other-"))
        self.addCleanup(shutil.rmtree, other, ignore_errors=True)
        make_root(other, **kwargs)
        builder = build.Builder(other)
        builder.build()
        builder.write()
        return other


class BucketMathTests(TempCase):
    def test_buckets_are_fixed_width_and_label_the_top_one_honestly(self):
        buckets = stats_mod._buckets([(value, f"OBS-{value:03d}") for value in (5, 7, 9, 11, 20, 22, 25)], 5)
        self.assertEqual([bucket["count"] for bucket in buckets], [0, 3, 1, 0, 2, 1])
        self.assertEqual(buckets[1]["label"], "5–9")
        self.assertFalse(buckets[-1]["open_ended"])
        self.assertEqual(buckets[-1]["label"], "25–29")

    def test_open_ended_top_bucket_when_a_value_sits_above_it(self):
        buckets = stats_mod._buckets([(value, f"OBS-{index:03d}") for index, value in enumerate([12, 63])], 5)
        self.assertEqual(len(buckets), 10)
        self.assertTrue(buckets[-1]["open_ended"])
        self.assertEqual(buckets[-1]["label"], "45+")
        self.assertEqual(sum(bucket["count"] for bucket in buckets), 2)

    def test_single_bucket_when_every_wait_is_tiny(self):
        buckets = stats_mod._buckets([(2, "OBS-001"), (3, "OBS-002")], 5)
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0]["label"], "0–4")
        self.assertEqual(buckets[0]["count"], 2)

    def test_median_mean_and_p90(self):
        values = [5, 7, 9, 11, 20, 22, 25]
        self.assertEqual(stats_mod._median(values), 11)
        self.assertEqual(stats_mod._p90(values), 25)
        self.assertIsNone(stats_mod._median([]))
        self.assertIsNone(stats_mod._stdev([4]))


class DayPartTests(TempCase):
    def test_day_parts_follow_the_documented_boundaries(self):
        from datetime import time

        self.assertEqual(derive_day_part(time(9, 30)), "morning")
        self.assertEqual(derive_day_part(time(13, 0)), "afternoon")
        self.assertEqual(derive_day_part(time(18, 5)), "evening")
        self.assertEqual(derive_day_part(time(22, 30)), "night")


class ChartTests(TempCase):
    def test_charts_are_svg_with_a_title_and_description(self):
        buckets = [{"label": "5–9", "lo": 5, "hi": 10, "count": 2, "row_ids": ["OBS-001"], "open_ended": False}]
        svg = charts.histogram(buckets, 6.5, title="Waits", desc="A histogram", prefix="t1",
                               y_label="observations", h_label="minutes", median_label="median",
                               empty_note="no data")
        self.assertIn("<svg", svg)
        self.assertIn('role="img"', svg)
        self.assertIn('<title id="t1-t">Waits</title>', svg)
        self.assertIn('aria-labelledby="t1-t t1-d"', svg)

    def test_empty_chart_says_so_instead_of_inventing_bars(self):
        svg = charts.histogram([], None, title="Waits", desc="A histogram", prefix="t2",
                               y_label="observations", h_label="minutes", median_label="median",
                               empty_note="no data yet")
        self.assertIn("no data yet", svg)
        self.assertNotIn("c-bar", svg)


class EmptySiteTests(TempCase):
    def test_site_builds_and_claims_no_findings_without_data(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-empty-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        shutil.copytree(TOOLS.parent / "src", root / "src")
        (root / "data").mkdir()
        write_rows(root / "data" / "places.csv", PLACES_HEADER, [])
        write_rows(root / "data" / "observations.csv", OBS_HEADER, [])
        write_rows(root / "data" / "photos.csv", PHOTOS_HEADER, [])
        common.write_text(root / "data" / "interview.md", "")

        builder = build.Builder(root)
        builder.build()
        builder.write()

        home = common.read_text(root / "index.html")
        self.assertIn("Field data collection is under way", home)
        self.assertNotIn("{{", home)
        self.assertIn("0 of 20 observations logged", home)

        data_page = common.read_text(root / "data.html")
        self.assertNotIn('<svg class="chart"', data_page, "no chart may be drawn without data")

        report = check.run(root, publish=False)
        errors = [item for item in report["findings"] if item["level"] == validate.ERROR]
        self.assertEqual([], errors, f"empty site should still be clean: {errors}")


class SyntheticSiteTests(TempCase):
    def test_numbers_on_the_page_come_from_the_csv(self):
        builder = self.build_site()
        data_page = common.read_text(self.tmp / "data.html")
        self.assertIn("11", data_page)                       # median of the synthetic waits
        self.assertIn("99", data_page)                        # total minutes
        self.assertIn("OBS-001", data_page)                    # and the rows are cited
        self.assertEqual(builder.stats["wait"]["median"], 11)
        self.assertEqual(builder.stats["wait"]["total_minutes"], 99)

    def test_headline_is_chosen_by_a_stated_rule(self):
        builder = self.build_site()
        headline = builder.stats["headline"]
        self.assertEqual(headline["kind"], "place_median")
        self.assertEqual(headline["place_id"], "beta")
        self.assertEqual(headline["median"], 22)
        home = common.read_text(self.tmp / "index.html")
        self.assertIn("Counter Beta", home)
        self.assertIn("Why this is the headline", home)
        self.assertIn("OBS-005", home)

    def test_charts_map_and_photos_render(self):
        self.build_site()
        data_page = common.read_text(self.tmp / "data.html")
        self.assertEqual(data_page.count('<svg class="chart"'), 3)
        map_page = common.read_text(self.tmp / "map.html")
        self.assertIn('class="c-node"', map_page)
        self.assertIn("Counter Beta", map_page)
        self.assertIn("কাউন্টার বিটা", common.read_text(self.tmp / "bn" / "map.html"))   # the same table in Bangla
        self.assertIn("assets/photos/evidence-alpha.png", common.read_text(self.tmp / "index.html"))
        self.assertTrue((self.tmp / "assets" / "photos" / "evidence-alpha.png").is_file())

    def test_limitations_page_reports_real_gaps(self):
        self.build_site()
        page = common.read_text(self.tmp / "limitations.html")
        self.assertIn("Counter Gamma", page)                   # listed but never measured
        self.assertIn("were estimated rather than timed", page)  # two rows were estimates
        self.assertIn("estimated by eye", common.read_text(self.tmp / "data.html"))
        findings = [item["key"] for item in self.build_site().stats["audit"]]
        self.assertIn("places_without_data", findings)
        self.assertIn("estimate_share", findings)
        self.assertIn("not_enough_yet", findings)

    def test_interview_is_published_only_with_consent(self):
        builder = self.build_site()
        home = common.read_text(self.tmp / "index.html")
        self.assertIn("Counter staff", home)
        self.assertIn("only one of me", home)

        without = self.build_other(interview=INTERVIEW.replace("consent_ok: yes", "consent_ok: no"))
        self.assertNotIn("only one of me", common.read_text(without / "index.html"))
        self.assertIn("permission to publish", common.read_text(without / "index.html"))

    def test_bangla_pages_mirror_the_english_ones(self):
        self.build_site()
        bangla_home = common.read_text(self.tmp / "bn" / "index.html")
        self.assertIn('<html lang="bn"', bangla_home)
        self.assertIn('data-bn-review="pending"', bangla_home)
        self.assertIn("কাউন্টার বিটা", bangla_home)
        self.assertIn('href="../index.html"', bangla_home)

    def test_changing_one_number_changes_the_chart_and_the_sentence(self):
        self.build_site()
        before_data = common.read_text(self.tmp / "data.html")
        before_home = common.read_text(self.tmp / "index.html")

        changed = list(OBSERVATIONS)
        changed[6] = changed[6].replace(",25,estimate", ",60,estimate")
        after_root = self.build_other(observations=changed)
        after_data = common.read_text(after_root / "data.html")
        after_home = common.read_text(after_root / "index.html")

        self.assertNotEqual(before_data, after_data)
        self.assertIn("45+", after_data)                # the open-ended top bucket appears
        self.assertNotEqual(before_home, after_home)     # the headline sentence moved with it


class DesignTests(TempCase):
    """The drawings, the illustrations and the hero picture."""

    def test_the_decorations_are_hidden_and_carry_no_figures(self):
        for name, svg in (("hero", art.hero_scene()), ("camera", art.camera_note()), ("mark", art.brand_mark())):
            self.assertIn('aria-hidden="true"', svg, f"the {name} drawing should be decorative")
            self.assertNotIn("<title", svg, f"the {name} drawing should not be announced at all")
            self.assertNotIn("<text", svg, f"the {name} drawing must not print a figure or a label")

    def test_the_icons_are_decoration_and_a_typo_stops_the_build(self):
        svg = art.icon("camera")
        self.assertIn('aria-hidden="true"', svg)
        self.assertNotIn("<text", svg)
        with self.assertRaises(common.BuildError):
            art.icon("no-such-icon")

    def test_the_target_meter_draws_the_figure_it_announces(self):
        svg = art.wait_meter(37, "37 of 100 observations logged")
        self.assertIn('role="img"', svg)
        self.assertIn('aria-label="37 of 100 observations logged"', svg)
        self.assertIn(">37<tspan", svg)
        # circumference of r=45 is 282.7, so 37 percent leaves 178.1 of it empty
        self.assertIn('stroke-dashoffset="178.1"', svg)
        self.assertIn('stroke-dashoffset="0.0"', art.wait_meter(140, "over the top"))

    def test_the_hero_shows_the_drawing_until_a_photo_is_named(self):
        self.build_site()
        home = common.read_text(self.tmp / "index.html")
        self.assertIn('class="art art-hero"', home)
        self.assertNotIn("hero-photo", home)

    def test_the_hero_uses_the_authors_own_photo_when_it_is_named(self):
        self.build_with_site(hero_photo_file="evidence-alpha.png")
        home = common.read_text(self.tmp / "index.html")
        self.assertIn('class="hero-photo"', home)
        self.assertIn("Four people standing at a narrow counter", home)
        self.assertNotIn('class="art art-hero"', home)
        bangla = common.read_text(self.tmp / "bn" / "index.html")
        self.assertIn("কাউন্টারে চারজন মানুষ দাঁড়িয়ে আছে", bangla)

    def test_the_hero_falls_back_instead_of_showing_a_broken_picture(self):
        self.build_with_site(hero_photo_file="not-in-photos-csv.png")
        home = common.read_text(self.tmp / "index.html")
        self.assertIn('class="art art-hero"', home)
        self.assertNotIn("hero-photo", home)
        findings = validate.run(self.tmp, publish=False)
        self.assertTrue(
            any("hero_photo_file" in item["message"] for item in findings),
            "naming a photo that is not in photos.csv should be reported",
        )

    def test_the_pipeline_diagram_is_drawn_from_the_content_files(self):
        self.build_site()
        home = common.read_text(self.tmp / "index.html")
        self.assertIn("art art-flow", home)
        self.assertIn("data/stats.json", home)
        self.assertIn("the rows I wrote by hand", home)
        self.assertIn("আমি হাতে লেখা সারিগুলো", common.read_text(self.tmp / "bn" / "index.html"))

    def test_every_colour_a_chart_uses_has_a_contrast_pair(self):
        theme = common.load_json(TOOLS.parent / "src" / "theme.json")
        pairs = {(pair["scheme"], pair["fg"].lower()) for pair in theme["contrast_pairs"]}
        for scheme in ("light", "dark"):
            for name in ("accent", "accent_2", "ok", "warn", "danger"):
                colour = theme[scheme][name].lower()
                self.assertIn((scheme, colour), pairs, f"{scheme} {name} has no contrast pair")
            for index in range(1, 6):
                colour = theme[scheme][f"series_{index}"].lower()
                self.assertIn((scheme, colour), pairs, f"{scheme} series_{index} has no contrast pair")


class ValidationTests(TempCase):
    def test_broken_rows_are_rejected_with_readable_messages(self):
        broken = [
            "OBS-001,02-03-2026,09:30,09:35,alpha,4,3,5,stopwatch,yes,morning,sun,,Tester,wrong date format",
            "OBS-002,2026-03-02,9.30,09:52,nowhere,5,4,7,stopwatch,no,morning,sun,,Tester,unknown place",
            "OBS-002,2026-03-02,13:10,13:19,alpha,6,5,9,stopwatch,yes,afternoon,hot,,Tester,duplicate id",
            "OBS-003,2026-03-03,18:05,18:25,beta,9,8,900,stopwatch,yes,evening,rain,,Tester,impossible wait",
        ]
        root = Path(tempfile.mkdtemp(prefix="groundtruth-broken-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        shutil.copytree(TOOLS.parent / "src", root / "src")
        (root / "data" / "photos").mkdir(parents=True)
        write_rows(root / "data" / "places.csv", PLACES_HEADER, PLACES)
        write_rows(root / "data" / "observations.csv", OBS_HEADER, broken)
        write_rows(root / "data" / "photos.csv", PHOTOS_HEADER, [])
        common.write_text(root / "data" / "interview.md", "")

        dataset = load_dataset(root)
        joined = " | ".join(dataset.errors)
        self.assertIn("must be YYYY-MM-DD", joined)
        self.assertIn("is not in places.csv", joined)
        self.assertIn("duplicate id", joined)
        self.assertIn("outside 0-600", joined)

    def test_photo_without_alt_text_is_rejected(self):
        bad_photo = ["PH-001,evidence-alpha.png,alpha,2026-03-02,Four people at the counter,কাউন্টারে চারজন,,,queue,yes"]
        without_photo_refs = [row.replace(",PH-002,", ",,") for row in OBSERVATIONS]
        root = self.build_other(photos=bad_photo, observations=without_photo_refs)
        dataset = load_dataset(root)
        joined = " | ".join(dataset.errors)
        self.assertIn("alt_en is empty", joined)
        self.assertIn("alt_bn is empty", joined)

    def test_publish_gate_blocks_an_unfinished_site(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-gate-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        shutil.copytree(TOOLS.parent / "src", root / "src")
        (root / "data" / "photos").mkdir(parents=True)
        write_rows(root / "data" / "places.csv", PLACES_HEADER, [])
        write_rows(root / "data" / "observations.csv", OBS_HEADER, [])
        write_rows(root / "data" / "photos.csv", PHOTOS_HEADER, [])
        common.write_text(root / "data" / "interview.md", "")
        builder = build.Builder(root)
        builder.build()
        builder.write()

        report = check.run(root, publish=True)
        errors = " | ".join(item["message"] for item in report["findings"] if item["level"] == validate.ERROR)
        self.assertIn("student_name is empty", errors)
        self.assertIn("only 0 of 20 observations collected", errors)
        self.assertIn("no interview in it yet", errors)
        self.assertIn("has not been signed off", errors)
        self.assertIn("review-pending note", errors)

    def test_publish_gate_passes_on_a_complete_synthetic_site(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-complete-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        make_root(root)
        site = json.loads(common.read_text(root / "src" / "site.json"))
        site.update({
            "student_name": "Test Student", "student_id": "S-000", "course": "Test Course",
            "institution": "Test Institution", "problem_title_en": "How long people wait at the test counters",
            "problem_title_bn": "পরীক্ষার কাউন্টারে মানুষ কতক্ষণ অপেক্ষা করে",
            "site_url": "https://example.invalid/ground-truth", "repo_url": "https://example.invalid/repo",
            "contact_email": "student@example.invalid", "target_observations": 7, "target_photos": 2,
        })
        common.write_text(root / "src" / "site.json", json.dumps(site, ensure_ascii=False, indent=2))
        status = json.loads(common.read_text(root / "src" / "bn-status.json"))
        status.update({"reviewer": "Test Student", "reviewed_all": True})
        common.write_text(root / "src" / "bn-status.json", json.dumps(status, ensure_ascii=False, indent=2))

        builder = build.Builder(root)
        builder.build()
        builder.write()

        report = check.run(root, publish=True)
        errors = [item["message"] for item in report["findings"] if item["level"] == validate.ERROR]
        self.assertEqual([], errors, f"a complete site must pass the publish gate: {errors}")
        self.assertIn('data-snapshot="', common.read_text(root / "index.html"))
        self.assertIn("sitemap.xml", [path.name for path in root.iterdir()])
        # with a repository url set, the footer has to make the licence reachable
        self.assertIn("/blob/main/LICENSE", common.read_text(root / "index.html"))
        self.assertIn("/blob/main/LICENSE", common.read_text(root / "bn" / "index.html"))


class IntegrityTests(TempCase):
    def test_checker_catches_a_page_that_is_no_longer_in_sync_with_the_csv(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-stale-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        make_root(root)
        builder = build.Builder(root)
        builder.build()
        builder.write()

        # edit the raw data without rebuilding: the checked site must refuse it
        rows = common.read_text(root / "data" / "observations.csv").replace(",25,estimate", ",60,estimate")
        common.write_text(root / "data" / "observations.csv", rows)

        report = check.run(root, publish=False)
        errors = " | ".join(item["message"] for item in report["findings"] if item["level"] == validate.ERROR)
        self.assertIn("built from an older CSV", errors)
        self.assertIn("stats.json is older than the CSV", errors)

    def test_checker_rejects_content_with_a_typed_in_number(self):
        findings = []
        tree = {"lede": "People waited 7 minutes on average."}
        for key, value in content_mod.find_bare_numbers(tree):
            findings.append((key, value))
        self.assertEqual(findings[0][0], "lede")

        allowed = {"lede": "People waited {{stat:wait.median}} minutes."}
        self.assertEqual([], content_mod.find_bare_numbers(allowed))

    def test_token_resolution_refuses_a_missing_value(self):
        content = content_mod.Content(TOOLS.parent, {}, {"wait": {"median": None}}, {})
        with self.assertRaises(common.TokenError):
            content.t("en", "median {{stat:wait.median}}")

    def test_huge_page_fails_the_weight_check(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-heavy-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "bn").mkdir()
        (root / "big.html").write_bytes(b"x" * 1_100_000)
        findings = []
        check.check_weights(root, ["big.html"], findings)
        self.assertTrue(any("per-page limit" in item["message"] for item in findings))

    def test_javascript_that_writes_text_is_rejected(self):
        root = Path(tempfile.mkdtemp(prefix="groundtruth-js-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "assets").mkdir()
        common.write_text(root / "assets" / "app.js", "element.innerHTML = '<b>hello</b>';")
        findings = []
        check.check_script(root, findings)
        self.assertTrue(any("innerHTML" in item["message"] for item in findings))

    def test_interview_parser_reads_both_languages(self):
        path = self.tmp / "interview.md"
        common.write_text(path, INTERVIEW)
        errors, warnings = [], []
        parsed = parse_interview(path, errors, warnings, {"alpha", "beta", "gamma"})
        self.assertTrue(parsed["present"])
        self.assertTrue(parsed["consent_ok"])
        self.assertEqual(2, len(parsed["pairs"]))
        self.assertIn("সন্ধ্যার", parsed["quote_bn"])
        self.assertIn("bus to catch", parsed["pairs"][1]["a_en"])
        self.assertEqual([], errors)

    def test_contrast_ratios_are_computed_from_the_theme(self):
        self.assertAlmostEqual(21.0, check.contrast_ratio("#000000", "#ffffff"), places=1)
        self.assertLess(check.contrast_ratio("#777777", "#ffffff"), 4.5)


if __name__ == "__main__":
    common.setup_console()
    unittest.main(verbosity=2)
