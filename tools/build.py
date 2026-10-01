"""Generate the whole static site from data/ and src/.

Run it from the repository root:

    py tools/build.py

Every page under the repository root is written by this script. The raw CSVs
are never edited, and no number is ever typed into a page by hand: pages quote
figures through ``{{namespace:key}}`` tokens that resolve out of
``data/stats.json``.

A section that needs data is skipped when there is no data yet, so the site
can never print an empty figure or a placeholder number. What it prints
instead is an honest "collection in progress" panel.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import art  # noqa: E402
import charts  # noqa: E402
import common  # noqa: E402
import content as content_mod  # noqa: E402
from common import BuildError, esc, fmt_num  # noqa: E402
from dataset import load_dataset  # noqa: E402
from stats import compute  # noqa: E402

PAGES = ("index", "data", "map", "action", "summary", "limitations")
PAGE_FILES = {
    "index": "index.html",
    "data": "data.html",
    "map": "map.html",
    "action": "action.html",
    "summary": "summary.html",
    "limitations": "limitations.html",
}
BN_DIR = "bn"
RAW_TABLE_LIMIT = 40


class Builder:
    def __init__(self, root, strict: bool = False):
        self.root = Path(root)
        self.strict = strict
        self.theme = common.load_json(self.root / "src" / "theme.json")
        self.site = common.load_json(self.root / "src" / "site.json")
        self.dataset = load_dataset(self.root)
        self.stats = compute(self.dataset, self.site)
        self.fingerprint = common.data_fingerprint(self.root)
        self.meta = {
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "built_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "data_hash": self.fingerprint["combined"],
            "data_hash_short": self.fingerprint["short"],
            "year": str(datetime.now(timezone.utc).year),
        }
        self.content = content_mod.Content(self.root, self.site, self.stats, self.meta)
        self.errors = list(self.dataset.errors)
        self.warnings = list(self.dataset.warnings)
        self.pages: dict[str, str] = {}
        self.extra_files: dict[str, str] = {}

    # ------------------------------------------------------------------
    # small helpers
    # ------------------------------------------------------------------
    @property
    def has_data(self) -> bool:
        return self.stats["coverage"]["collected"] > 0

    @property
    def has_waits(self) -> bool:
        return self.stats["wait"]["count"] > 0

    def c(self, lang: str, key: str) -> str:
        return self.content.c(lang, key)

    def t(self, lang: str, key: str, extra: dict | None = None) -> str:
        return self.content.t(lang, self.c(lang, key), extra)

    def items(self, lang: str, key: str, extra: dict | None = None) -> str:
        """A list in the content file, rendered as <li> entries."""
        value = content_mod.lookup(self.content.trees[lang], key)
        if value is content_mod.MISSING or not isinstance(value, list):
            raise BuildError(f"content.{lang}.json: {key} should be a list of lines")
        return "".join(
            f"<li>{self.content.t(lang, str(entry), extra)}</li>" for entry in value
        )

    def label(self, lang: str, key: str) -> str:
        value = content_mod.lookup(self.content.trees[lang].get("labels", {}), key)
        if value is content_mod.MISSING:
            raise BuildError(f"content.{lang}.json: labels.{key} is missing")
        return str(value)

    def title(self, lang: str) -> str:
        configured = (self.site.get("problem_title_bn" if lang == "bn" else "problem_title_en") or "").strip()
        if configured:
            return configured
        return self.label(lang, "problem_title_fallback")

    def url(self, lang: str, page: str, from_lang: str) -> str:
        """Relative href, from a page written in ``from_lang`` to ``page`` in ``lang``."""
        prefix = "../" if from_lang == "bn" else ""
        target = f"{BN_DIR}/" if lang == "bn" else ""
        return f"{prefix}{target}{PAGE_FILES[page]}"

    def asset(self, from_lang: str, path: str) -> str:
        return ("../" if from_lang == "bn" else "") + path

    def canonical(self, lang: str, page: str) -> str:
        site_url = (self.site.get("site_url") or "").rstrip("/")
        if not site_url:
            return ""
        tail = PAGE_FILES[page] if page != "index" else ""
        path = f"{BN_DIR}/" if lang == "bn" else ""
        return f"{site_url}/{path}{tail}"

    def has_contact(self) -> bool:
        return bool((self.site.get("contact_email") or "").strip())

    def has_repo(self) -> bool:
        return bool((self.site.get("repo_url") or "").strip())

    def repo_link(self, path: str) -> str:
        base = (self.site.get("repo_url") or "").rstrip("/")
        return f"{base}/blob/main/{path}" if base else ""

    def row_ids(self, ids, limit: int = RAW_TABLE_LIMIT) -> str:
        ids = list(ids)
        shown = ", ".join(ids[:limit])
        if len(ids) > limit:
            shown += f" (+{len(ids) - limit} more)"
        return shown

    def row_id_span(self, ids) -> str:
        return f'<span class="row-ids">{esc(self.row_ids(ids))}</span>'

    def table(self, headers, rows, caption="", wrap_label="") -> str:
        """A data table that stacks into labelled rows on a phone.

        Every cell carries the column name in ``data-label``, so the stylesheet
        can turn the table into a list of labelled values under 34rem, and the
        table never needs sideways scrolling to be read.
        """
        head = "".join(f'<th scope="col">{esc(cell)}</th>' for cell in headers)
        body = []
        for row in rows:
            cells = []
            for index, cell in enumerate(row):
                label = f' data-label="{esc(headers[index])}"' if index < len(headers) else ""
                if isinstance(cell, tuple):
                    cells.append(f'<td class="{cell[1]}"{label}>{cell[0]}</td>')
                else:
                    cells.append(f"<td{label}>{esc(cell)}</td>")
            body.append(f"<tr>{''.join(cells)}</tr>")
        caption_html = f"<caption>{esc(caption)}</caption>" if caption else ""
        label = wrap_label or caption or "data table"
        return (
            f'<div class="table-wrap" role="region" aria-label="{esc(label)}" tabindex="0">'
            f'<table class="responsive">{caption_html}<thead><tr>{head}</tr></thead>'
            f"<tbody>{''.join(body)}</tbody></table></div>"
        )

    def details(self, summary: str, body: str) -> str:
        return f"<details><summary>{esc(summary)}</summary>{body}</details>"

    def progress(self, lang: str) -> str:
        """The collection target, drawn as a ring and stated in words.

        The ring and the sentence are built from the same two figures, so the
        picture cannot claim a different total from the text beside it.
        """
        percent = min(100, self.stats["coverage"]["percent"])
        return (
            '<div class="meter">'
            f'<div class="meter-ring">{art.wait_meter(percent, self.t(lang, "common.progress_aria"))}</div>'
            f'<p class="note meter-copy">{self.t(lang, "common.progress_text")}</p>'
            "</div>"
        )

    def heading(self, text: str, icon_name: str | None = None) -> str:
        """A section heading, optionally with an icon chip beside it.

        The icon repeats nothing: it is decoration, so it is hidden from screen
        readers and the heading text carries the whole meaning.
        """
        glyph = (
            f'<span class="ico-chip" aria-hidden="true">{art.icon(icon_name)}</span>'
            if icon_name else ""
        )
        return f'<h2 class="section">{glyph}<span>{esc(text)}</span></h2>'

    def empty_card(self, lang: str, body_key: str = "common.empty_body") -> str:
        return (
            '<section class="card empty-state">'
            f'<p class="card-title">{self.t(lang, "common.empty_title")}</p>'
            f"<p>{self.t(lang, body_key)}</p>{self.progress(lang)}</section>"
        )

    def stat_cards(self, lang: str, items) -> str:
        """The metric band. Each entry is (label, value, unit) or the same plus an icon name."""
        cards = []
        for item in items:
            label, value, unit = item[0], item[1], item[2]
            icon_name = item[3] if len(item) > 3 else None
            unit_html = f" <small>{esc(unit)}</small>" if unit else ""
            glyph = (
                f'<span class="metric-icon" aria-hidden="true">{art.icon(icon_name, size=16)}</span>'
                if icon_name else ""
            )
            cards.append(
                f'<div class="metric"><dt>{glyph}{esc(label)}</dt>'
                f"<dd>{esc(value)}{unit_html}</dd></div>"
            )
        return f'<dl class="metrics">{"".join(cards)}</dl>'

    def hero_photo(self):
        """The author's own photo for the hero, if one is named and it passed the checks.

        A file only reaches this list by being a real, consented row of
        photos.csv with a caption and alt text, so the hero picture can never be
        a stock image standing in for evidence.
        """
        wanted = (self.site.get("hero_photo_file") or "").strip()
        if not wanted:
            return None
        for photo in self.stats["photos"]:
            if photo["file"] == wanted:
                return photo
        return None

    def hero_media(self, lang: str) -> str:
        """Either the author's photograph or the drawn illustration, never both."""
        photo = self.hero_photo()
        if photo is None:
            return art.hero_scene()
        alt_key = "alt_bn" if lang == "bn" else "alt_en"
        return (
            '<figure class="hero-figure">'
            f'<img class="hero-photo" src="{esc(self.asset(lang, photo["src"]))}" '
            f'alt="{esc(photo[alt_key])}" decoding="async">'
            "</figure>"
        )

    def hero(self, lang: str) -> str:
        return (
            '<section class="hero">'
            '<div class="hero-copy">'
            f'<p class="kicker">{esc(self.t(lang, "home.kicker"))}</p>'
            f"<h1>{esc(self.title(lang))}</h1>"
            f'<p class="lede">{self.t(lang, "home.lede")}</p>'
            '<p class="hero-actions">'
            f'<a class="button" href="{self.url(lang, "data", lang)}">{esc(self.t(lang, "home.data_button"))}</a> '
            f'<a class="button secondary" href="{self.url(lang, "summary", lang)}">'
            f'{esc(self.t(lang, "home.hero_print_button"))}</a>'
            "</p>"
            "</div>"
            f'<div class="hero-art">{self.hero_media(lang)}</div>'
            "</section>"
        )

    def flow_figure(self, lang: str) -> str:
        """The pipeline, drawn: the raw files, the computed figures, these pages."""
        nodes = [
            (self.t(lang, "home.flow_node_1"), self.t(lang, "home.flow_node_1_sub"), "table"),
            (self.t(lang, "home.flow_node_2"), self.t(lang, "home.flow_node_2_sub"), "chart"),
            (self.t(lang, "home.flow_node_3"), self.t(lang, "home.flow_node_3_sub"), "page"),
        ]
        chart = art.method_diagram(
            nodes, self.t(lang, "home.flow_alt"), self.t(lang, "home.flow_desc"),
        )
        return f'<figure>{chart}<figcaption>{self.t(lang, "home.flow_caption")}</figcaption></figure>'

    def photo_strip(self, lang: str, limit: int | None = None, empty_key: str = "home.no_photos") -> str:
        photos = self.stats["photos"]
        if not photos:
            return (
                '<section class="card empty-state evidence-empty">'
                f'<div class="art-empty" aria-hidden="true">{art.camera_note()}</div>'
                f'<p class="note">{self.t(lang, empty_key)}</p>'
                "</section>"
            )
        caption_key = "caption_bn" if lang == "bn" else "caption_en"
        alt_key = "alt_bn" if lang == "bn" else "alt_en"
        place_key = "place_name_bn" if lang == "bn" else "place_name_en"
        figures = []
        for photo in photos[:limit] if limit else photos:
            figures.append(
                f'<figure><img src="{esc(self.asset(lang, photo["src"]))}" alt="{esc(photo[alt_key])}" '
                f'loading="lazy" decoding="async">'
                f'<figcaption><strong>{esc(photo[place_key])}</strong> · {esc(photo[caption_key])} '
                f'<span class="note">{esc(photo["taken_at"])}</span></figcaption></figure>'
            )
        return f'<div class="evidence">{"".join(figures)}</div>'

    # ------------------------------------------------------------------
    # page frame
    # ------------------------------------------------------------------
    def interview_block(self, lang: str) -> str:
        """The one interview. Answers stay off the site until consent is recorded."""
        interview = self.stats["interview"]
        parts = [self.heading(self.t(lang, "interview.title"), "quote")]
        if not interview.get("present"):
            parts.append(f'<p class="note">{self.t(lang, "interview.not_recorded")}</p>')
            return "\n".join(parts)
        if not interview.get("consent_ok"):
            parts.append(f'<p class="note">{self.t(lang, "interview.no_consent")}</p>')
            return "\n".join(parts)
        parts.append(f'<p class="note">{self.t(lang, "interview.meta")}</p>')
        quote = (interview.get("quote_bn") if lang == "bn" else interview.get("quote_en")) or ""
        if quote:
            parts.append(
                f'<blockquote class="quote"><p>{esc(quote)}</p>'
                f'<footer>{esc(interview.get("person_label", ""))}</footer></blockquote>'
            )
        question_key = "q_bn" if lang == "bn" else "q_en"
        answer_key = "a_bn" if lang == "bn" else "a_en"
        for pair in interview["pairs"]:
            answer = pair.get(answer_key) or ""
            if not answer:
                continue
            parts.append(f'<h3>{esc(pair.get(question_key, ""))}</h3><p>{esc(answer)}</p>')
        parts.append(f'<p class="note">{self.t(lang, "interview.source_note")}</p>')
        return "\n".join(parts)

    def header(self, lang: str, page: str) -> str:
        nav_items = "".join(
            f'<li><a href="{self.url(lang, item, lang)}"'
            f'{" aria-current=\"page\"" if item == page else ""}>'
            f'{esc(self.t(lang, f"nav.{item}"))}</a></li>'
            for item in PAGES
        )
        other = "bn" if lang == "en" else "en"
        return (
            '<header class="site-header"><div class="wrap">'
            f'<a class="brand" href="{self.url(lang, "index", lang)}">{art.brand_mark()}'
            f'<span class="brand-text"><strong>{esc(self.t(lang, "meta.site_name"))}</strong>'
            f'<span>{esc(self.t(lang, "meta.site_tagline"))}</span></span></a>'
            f'<nav class="site-nav" aria-label="{esc(self.t(lang, "nav.label"))}"><ul>{nav_items}</ul></nav>'
            f'<p class="lang-switch"><a href="{self.url(other, page, lang)}" hreflang="{other}" lang="{other}" '
            f'title="{esc(self.label(lang, "lang_switch_aria"))}">{esc(self.label(lang, "lang_switch"))}</a></p>'
            "</div></header>"
        )

    def footer(self, lang: str, page: str) -> str:
        links = []
        method = self.repo_link("docs/method-note.md")
        if method:
            links.append(f'<li><a href="{esc(method)}">{esc(self.t(lang, "footer.method"))}</a></li>')
        log = self.repo_link("docs/ai-use-log.md")
        if log:
            links.append(f'<li><a href="{esc(log)}">{esc(self.t(lang, "footer.ai_log"))}</a></li>')
        if self.has_repo():
            links.append(f'<li><a href="{esc(self.site["repo_url"])}">{esc(self.t(lang, "footer.source"))}</a></li>')
        licence = self.repo_link("LICENSE")
        if licence:
            links.append(f'<li><a href="{esc(licence)}">{esc(self.t(lang, "footer.licence"))}</a></li>')
        byline = ""
        if (self.site.get("student_name") or "").strip():
            parts = [self.site.get("student_name", ""), self.site.get("course", ""), self.site.get("institution", "")]
            byline = f'<p>{esc(self.t(lang, "footer.byline"))} {esc(" · ".join(part for part in parts if part))}</p>'
        review = ""
        review_attr = ""
        if lang == "bn" and not self.bn_reviewed():
            review = f'<p class="note">{esc(self.t(lang, "footer.review_pending"))}</p>'
            review_attr = ' data-bn-review="pending"'
        link_list = f'<ul>{"".join(links)}</ul>' if links else ""
        brand = (
            f'<div class="footer-brand">{art.brand_mark(size=32)}'
            f'<span>{esc(self.t(lang, "meta.site_name"))}</span></div>'
        )
        return (
            f'<footer class="site-footer"{review_attr}><div class="wrap">'
            f'<div class="footer-top">{brand}{link_list}</div>'
            f"{byline}"
            f'<p>{esc(self.t(lang, "footer.ai_note"))}</p>{review}'
            f'<p class="fingerprint">{esc(self.t(lang, "footer.snapshot"))} '
            f'<code>{esc(self.meta["data_hash_short"])}</code> · {esc(self.t(lang, "footer.built"))} '
            f'{esc(self.meta["built_date"])} · '
            f'<a href="{self.url(lang, "data", lang)}">{esc(self.t(lang, "footer.raw_data_link"))}</a></p>'
            f'<p>{esc(self.t(lang, "footer.rights"))}</p>'
            "</div></footer>"
        )

    def bn_reviewed(self) -> bool:
        status = self.content.bn_status or {}
        return bool(status.get("reviewed_all")) and bool(str(status.get("reviewer") or "").strip())

    def layout(self, lang: str, page: str, body: str, *, title_key: str | None = None,
               description_key: str | None = None) -> str:
        page_title = self.t(lang, title_key or f"pages.{page}.title")
        description = self.t(lang, description_key or f"pages.{page}.description")
        canonical = self.canonical(lang, page)
        canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
        alternates = ""
        if canonical:
            base = (self.site.get("site_url") or "").rstrip("/")
            tail = PAGE_FILES[page] if page != "index" else ""
            alternates = (
                f'<link rel="alternate" hreflang="en" href="{esc(f"{base}/{tail}")}">'
                f'<link rel="alternate" hreflang="bn" href="{esc(f"{base}/{BN_DIR}/{tail}")}">'
                f'<link rel="alternate" hreflang="x-default" href="{esc(f"{base}/{tail}")}">'
            )
        return (
            "<!DOCTYPE html>\n"
            f'<html lang="{lang}" data-snapshot="{esc(self.meta["data_hash_short"])}">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{esc(page_title)}</title>\n"
            f'<meta name="description" content="{esc(description)}">\n'
            f'<meta name="data-snapshot" content="{esc(self.meta["data_hash"])}">\n'
            f'<meta name="generator" content="tools/build.py — built {esc(self.meta["built_at"])} from data/*.csv">\n'
            f"{canonical_tag}{alternates}"
            f'<link rel="stylesheet" href="{self.asset(lang, "assets/site.css")}">\n'
            "</head>\n<body>\n"
            f'<a class="skip-link" href="#main">{esc(self.t(lang, "common.skip_link"))}</a>\n'
            f"{self.header(lang, page)}\n"
            f'<main id="main" class="wrap">\n{body}\n</main>\n'
            f"{self.footer(lang, page)}\n"
            f'<script src="{self.asset(lang, "assets/app.js")}" defer></script>\n'
            "</body>\n</html>\n"
        )

    # ------------------------------------------------------------------
    # charts and their tables
    # ------------------------------------------------------------------
    def chart_figure(self, *, chart_html: str, finding: str, citation: str, table_html: str, summary: str) -> str:
        return (
            f"<figure>{chart_html}"
            f'<figcaption>{finding} <span class="note">{citation}</span></figcaption>'
            f"{self.details(summary, table_html)}</figure>"
        )

    def histogram_figure(self, lang: str, prefix: str = "ch1") -> str:
        stats = self.stats
        buckets = stats["buckets"]
        chart = charts.histogram(
            buckets, stats["wait"]["median"],
            title=self.t(lang, "data.chart1_alt"),
            desc=self.t(lang, "data.chart1_desc"),
            prefix=prefix,
            y_label=self.label(lang, "unit_observations"),
            h_label=self.label(lang, "unit_minutes"),
            median_label=self.label(lang, "median"),
            empty_note=self.t(lang, "common.chart_no_data"),
        )
        rows = [[bucket["label"], fmt_num(bucket["count"]), self.row_ids(bucket["row_ids"])] for bucket in buckets]
        table = self.table(
            [self.label(lang, "minutes_bucket"), self.label(lang, "unit_observations"), self.label(lang, "row_ids")],
            rows,
            caption=self.t(lang, "data.chart1_table_caption"),
        )
        if not buckets:
            return self.chart_figure(
                chart_html=chart, finding=self.t(lang, "common.chart_no_data"),
                citation=self.t(lang, "common.citation_readymade"), table_html=table,
                summary=self.t(lang, "common.show_table"),
            )
        note = self.t(lang, "data.open_bucket_note") if buckets[-1]["open_ended"] else ""
        return self.chart_figure(
            chart_html=chart, finding=self.t(lang, "data.chart1_finding") + note,
            citation=self.t(lang, "common.citation"), table_html=table,
            summary=self.t(lang, "common.show_table"),
        )

    def labelled_places(self, lang: str, only_measured: bool = False):
        """Place rows with the display name for this language attached."""
        name_key = "name_bn" if lang == "bn" else "name_en"
        chosen = [entry for entry in self.stats["by_place"] if entry["count"] > 0 or not only_measured]
        return [{**entry, "label": entry[name_key] or entry["place_id"]} for entry in chosen]

    def place_figure(self, lang: str) -> str:
        entries = self.labelled_places(lang, only_measured=True)
        chart = charts.bars_by_place(
            entries,
            title=self.t(lang, "data.chart2_alt"),
            desc=self.t(lang, "data.chart2_desc"),
            prefix="ch2",
            value_label=self.t(lang, "data.chart2_value_label"),
            empty_note=self.t(lang, "common.chart_no_data"),
        )
        rows = []
        for entry in entries:
            name_key = "name_bn" if lang == "bn" else "name_en"
            rows.append([
                entry[name_key],
                fmt_num(entry["count"]),
                fmt_num(entry["median"]) if entry["median"] is not None else "—",
                fmt_num(entry["mean"]) if entry["mean"] is not None else "—",
                fmt_num(entry["max"]) if entry["max"] is not None else "—",
                self.row_ids(entry["row_ids"]),
            ])
        table = self.table(
            [self.label(lang, "place"), self.label(lang, "unit_observations"), self.label(lang, "median"),
             self.label(lang, "mean"), self.label(lang, "slowest"), self.label(lang, "row_ids")],
            rows,
            caption=self.t(lang, "data.chart2_table_caption"),
        )
        if self.has_waits:
            finding = self.t(lang, "data.chart2_finding") + " " + self.t(lang, "data.chart2_min_note")
        else:
            finding = self.t(lang, "common.chart_no_data")
        return self.chart_figure(
            chart_html=chart, finding=finding, citation=self.t(lang, "common.citation"),
            table_html=table, summary=self.t(lang, "common.show_table"),
        )

    def cumulative_figure(self, lang: str) -> str:
        by_day = self.stats["by_day"]
        chart = charts.cumulative_line(
            by_day,
            title=self.t(lang, "data.chart3_alt"),
            desc=self.t(lang, "data.chart3_desc"),
            prefix="ch3",
            x_label=self.label(lang, "date"),
            y_label=self.label(lang, "unit_minutes"),
            empty_note=self.t(lang, "common.chart_no_data"),
        )
        rows = []
        for day in by_day:
            rows.append([
                day["date"],
                fmt_num(day["count"]),
                fmt_num(day["total_minutes"]) if day["total_minutes"] is not None else "—",
                fmt_num(day["cumulative_minutes"]) if day["cumulative_minutes"] is not None else "—",
                self.row_ids(day["row_ids"]),
            ])
        table = self.table(
            [self.label(lang, "date"), self.label(lang, "unit_observations"), self.label(lang, "minutes_total"),
             self.label(lang, "minutes_running"), self.label(lang, "row_ids")],
            rows,
            caption=self.t(lang, "data.chart3_table_caption"),
        )
        finding = self.t(lang, "data.chart3_finding") if self.has_waits else self.t(lang, "common.chart_no_data")
        return self.chart_figure(
            chart_html=chart, finding=finding, citation=self.t(lang, "common.citation"),
            table_html=table, summary=self.t(lang, "common.show_table"),
        )

    def day_part_table(self, lang: str) -> str:
        rows = []
        for entry in self.stats["by_day_part"]:
            rows.append([
                self.label(lang, f"part_{entry['part']}"),
                fmt_num(entry["count"]),
                fmt_num(entry["median"]) if entry["median"] is not None else "—",
                self.row_ids(entry["row_ids"]),
            ])
        return self.table(
            [self.label(lang, "part_of_day"), self.label(lang, "unit_observations"),
             self.label(lang, "median"), self.label(lang, "row_ids")],
            rows,
            caption=self.t(lang, "data.day_part_caption"),
        )

    def missing_table(self, lang: str) -> str:
        rows = []
        for column, count in sorted(self.stats["missing"].items(), key=lambda item: -item[1]):
            rows.append([self.t(lang, f"limitations.field_{column}"), fmt_num(count),
                         fmt_num(self.stats["coverage"]["collected"])])
        return self.table(
            [self.label(lang, "field"), self.label(lang, "blank_cells"), self.label(lang, "of_total")],
            rows,
            caption=self.t(lang, "limitations.missing_caption"),
        )

    def timing_table(self, lang: str) -> str:
        timing = self.stats["timing"]
        rows = [[self.label(lang, f"timing_{method}"), fmt_num(timing[method])]
                for method in ("stopwatch", "estimate", "self_report")]
        rows.append([self.label(lang, "total"), fmt_num(timing["total"])])
        return self.table(
            [self.label(lang, "method"), self.label(lang, "unit_observations")],
            rows,
            caption=self.t(lang, "limitations.timing_caption"),
        )

    # ------------------------------------------------------------------
    # pages
    # ------------------------------------------------------------------
    def finding_note(self, lang: str) -> str:
        headline = self.stats["headline"]
        extra = {"headline": headline}
        sentence = self.t(lang, f"home.finding_{headline['kind']}", extra)
        rule = self.t(lang, f"home.rule_{headline['rule_key']}", extra)
        citation = ""
        if headline["row_ids"]:
            citation = (
                f'<p class="note">{esc(self.t(lang, "common.citation_headline"))} '
                f"{self.row_id_span(headline['row_ids'])}</p>"
            )
        return (
            f'<section class="card card-headline"><p class="card-title">'
            f'{esc(self.t(lang, "home.headline_label"))}</p>'
            f'<p class="lede">{sentence}</p>'
            f'<p class="note"><strong>{esc(self.t(lang, "common.rule_label"))}</strong> {rule}</p>'
            f"{citation}</section>"
        )

    def home(self, lang: str) -> str:
        stats = self.stats
        coverage = stats["coverage"]
        parts = [self.hero(lang)]
        if self.has_data:
            parts.append(self.finding_note(lang))
            if self.has_waits:
                cards = [
                    (self.label(lang, "observations_count"), fmt_num(coverage["collected"]), "", "table"),
                    (self.label(lang, "places_count"), fmt_num(coverage["places_with_data"]), "", "pin"),
                    (self.label(lang, "median"), fmt_num(stats["wait"]["median"]),
                     self.label(lang, "unit_minutes"), "gauge"),
                ]
            else:
                cards = [
                    (self.label(lang, "observations_count"), fmt_num(coverage["collected"]), "", "table"),
                    (self.label(lang, "places_count"), fmt_num(coverage["places_with_data"]), "", "pin"),
                    (self.label(lang, "waits_pending"), fmt_num(coverage["untimed"]), "", "stopwatch"),
                ]
            parts.append(self.stat_cards(lang, cards))
        else:
            parts.append(self.empty_card(lang))
        parts.append(self.heading(self.t(lang, "home.how_title"), "stopwatch"))
        parts.append(f'<ul>{self.items(lang, "home.how_points")}</ul>')
        parts.append(self.flow_figure(lang))
        parts.append(self.heading(self.t(lang, "home.evidence_title"), "camera"))
        parts.append(self.photo_strip(lang, limit=3))
        parts.append(self.interview_block(lang))
        if self.has_data:
            parts.append(self.heading(self.t(lang, "home.where_title"), "pin"))
            parts.append(f'<p>{self.t(lang, "home.where_body")}</p>')
        parts.append(
            f'<section class="card">{self.heading(self.t(lang, "home.ask_title"), "checklist")}'
            f'<p>{self.t(lang, "home.ask_body")}</p>'
            f'<p><a class="button" href="{self.url(lang, "action", lang)}">{esc(self.t(lang, "home.ask_button"))}</a> '
            f'<a class="button secondary" href="{self.url(lang, "data", lang)}">{esc(self.t(lang, "home.data_button"))}</a></p>'
            "</section>"
        )
        return "\n".join(parts)

    def data_page(self, lang: str) -> str:
        stats = self.stats
        coverage = stats["coverage"]
        parts = [
            f"<h1>{esc(self.t(lang, 'pages.data.title'))}</h1>",
            f'<p class="lede">{self.t(lang, "data.lede")}</p>',
        ]
        if not self.has_data:
            parts.append(self.empty_card(lang, "data.empty_body"))
        else:
            parts.append(self.progress(lang))
            cards = [(self.label(lang, "observations_count"), fmt_num(coverage["collected"]), ""),
                     (self.label(lang, "days_count"), fmt_num(coverage["days_distinct"]), "")]
            if self.has_waits:
                cards.append((self.label(lang, "slowest"), fmt_num(stats["wait"]["max"]), self.label(lang, "unit_minutes")))
            else:
                cards.append((self.label(lang, "waits_pending"), fmt_num(coverage["untimed"]), ""))
            parts.append(self.stat_cards(lang, cards))
            if self.has_waits:
                minutes = esc(self.label(lang, "unit_minutes"))
                facts = [
                    (self.label(lang, "median"), f'{fmt_num(stats["wait"]["median"])} {minutes}'),
                    (self.label(lang, "mean"), f'{fmt_num(stats["wait"]["mean"])} {minutes}'),
                    (self.label(lang, "p90"), f'{fmt_num(stats["wait"]["p90"])} {minutes}'),
                    (self.label(lang, "total_wait"), f'{fmt_num(stats["wait"]["total_minutes"])} {minutes}'),
                    (self.label(lang, "observations_count"), fmt_num(stats["wait"]["count"])),
                    (self.label(lang, "date_range"), esc(coverage["date_range"])),
                ]
                rows = "".join(f"<dt>{esc(label)}</dt><dd>{value}</dd>" for label, value in facts)
                parts.append(
                    self.heading(self.t(lang, "data.summary_label"), "table")
                    + f'<dl class="facts">{rows}</dl>'
                )
            parts.append(self.heading(self.t(lang, "data.charts_title"), "chart"))
            parts.append(self.histogram_figure(lang))
            parts.append(self.place_figure(lang))
            parts.append(self.cumulative_figure(lang))
            if stats["by_day_part"]:
                parts.append(self.heading(self.t(lang, "data.part_of_day_title"), "clock"))
                parts.append(f'<p>{self.t(lang, "data.part_of_day_body")}</p>')
                parts.append(self.day_part_table(lang))
            if self.has_waits:
                parts.append(self.heading(self.t(lang, "data.quality_title"), "gauge"))
                parts.append(f'<p>{self.t(lang, "data.quality_body")}</p>')
                parts.append(self.timing_table(lang))
                parts.append(
                    f'<p class="note">{self.t(lang, "data.walkaway_body")}</p>'
                    if stats["walked"]["known"] else
                    f'<p class="note">{self.t(lang, "data.walkaway_none")}</p>'
                )
        parts.append(self.heading(self.t(lang, "data.download_title"), "download"))
        parts.append(f'<p>{self.t(lang, "data.download_body")}</p>')
        parts.append(
            '<ul class="downloads">'
            f'<li><a href="{self.asset(lang, "data/observations.csv")}" download>'
            f'{esc(self.t(lang, "data.download_observations"))}</a></li>'
            f'<li><a href="{self.asset(lang, "data/photos.csv")}" download>'
            f'{esc(self.t(lang, "data.download_photos"))}</a></li>'
            f'<li><a href="{self.asset(lang, "data/stats.json")}" download>'
            f'{esc(self.t(lang, "data.download_stats"))}</a></li>'
            "</ul>"
        )
        parts.append(self.heading(self.t(lang, "data.rebuild_title"), "refresh"))
        parts.append(f'<p>{self.t(lang, "data.rebuild_body")}</p>')
        parts.append('<pre class="message">py tools/build.py\npy tools/check.py</pre>')
        return "\n".join(parts)

    def map_page(self, lang: str) -> str:
        entries = self.labelled_places(lang)
        chart = charts.place_diagram(
            entries,
            title=self.t(lang, "map.alt"),
            desc=self.t(lang, "map.desc"),
            prefix="map1",
            count_label=self.label(lang, "unit_observations"),
            median_label=self.label(lang, "median"),
            unmeasured_label=self.t(lang, "map.unmeasured"),
        )
        parts = [
            f"<h1>{esc(self.t(lang, 'pages.map.title'))}</h1>",
            f'<p class="lede">{self.t(lang, "map.lede")}</p>',
            f"<figure>{chart}<figcaption>{self.t(lang, 'map.caption')} "
            f'<span class="note">{esc(self.t(lang, "map.not_to_scale"))}</span></figcaption></figure>',
        ]
        if not entries:
            parts.append(self.empty_card(lang, "map.empty_body"))
            return "\n".join(parts)
        rows = []
        for entry in entries:
            name_key = "name_bn" if lang == "bn" else "name_en"
            desc_key = "description_bn" if lang == "bn" else "description_en"
            coords = ""
            if entry["lat"] is not None and entry["lon"] is not None:
                coords = f'{fmt_num(entry["lat"], 4)}, {fmt_num(entry["lon"], 4)}'
            rows.append([
                entry[name_key],
                (esc(entry[desc_key]), "wrap-cell"),
                fmt_num(entry["count"]),
                fmt_num(entry["median"]) if entry["median"] is not None else "—",
                (esc(self.row_ids(entry["row_ids"])) or "—", "row-ids"),
                esc(coords) or "—",
            ])
        parts.append(self.table(
            [self.label(lang, "place"), self.label(lang, "what_it_is"), self.label(lang, "unit_observations"),
             self.label(lang, "median"), self.label(lang, "row_ids"), self.label(lang, "coordinates")],
            rows,
            caption=self.t(lang, "map.table_caption"),
        ))
        parts.append(self.heading(self.t(lang, "map.photos_title"), "camera"))
        parts.append(self.photo_strip(lang))
        parts.append(f'<p class="note">{self.t(lang, "map.privacy_note")}</p>')
        return "\n".join(parts)

    def action_subject(self, lang: str) -> str:
        return self.t(lang, "action.email_subject")

    def action_message_key(self) -> str:
        if self.has_waits:
            return "action.message_data"
        return "action.message_partial" if self.has_data else "action.message_empty"

    def action_page(self, lang: str) -> str:
        message = self.t(lang, self.action_message_key())
        parts = [
            f"<h1>{esc(self.t(lang, 'pages.action.title'))}</h1>",
            f'<p class="lede">{self.t(lang, "action.lede")}</p>',
            self.heading(self.t(lang, "action.message_title"), "mail"),
            f'<p>{self.t(lang, "action.message_body")}</p>',
            f'<pre class="message" id="prepared-message">{message}</pre>',
            '<p class="copy-state no-print">'
            '<button class="button" type="button" data-copy-target="prepared-message">'
            f'<span class="when-idle">{esc(self.t(lang, "action.copy"))}</span>'
            f'<span class="when-done">{esc(self.t(lang, "action.copied"))}</span></button> '
            f'<span class="copy-note">{esc(self.t(lang, "action.copy_note"))}</span></p>',
        ]
        if self.has_contact():
            address = esc(self.site["contact_email"])
            subject = esc(self.action_subject(lang))
            body = esc(message)
            parts.append(
                f'<p class="no-print"><a class="button" href="mailto:{address}?subject={subject}&amp;body={body}">'
                f'{esc(self.t(lang, "action.email_button"))}</a></p>'
            )
        else:
            parts.append(f'<p class="note">{self.t(lang, "action.no_contact")}</p>')
        parts.append(self.heading(self.t(lang, "action.form_title"), "edit"))
        parts.append(f'<p>{self.t(lang, "action.form_body")}</p>')
        parts.append(self.report_form(lang) if self.has_contact() else f'<p class="note">{self.t(lang, "action.form_disabled")}</p>')
        parts.append(self.heading(self.t(lang, "action.print_title"), "print"))
        parts.append(f'<p>{self.t(lang, "action.print_body")}</p>')
        parts.append(
            f'<p class="no-print"><a class="button secondary" href="{self.url(lang, "summary", lang)}">'
            f'{esc(self.t(lang, "action.print_button"))}</a></p>'
        )
        parts.append(self.heading(self.t(lang, "action.include_title"), "checklist"))
        parts.append(f"<ul>{self.items(lang, 'action.include_points')}</ul>")
        parts.append(f'<p class="note">{self.t(lang, "action.privacy_note")}</p>')
        return "\n".join(parts)

    def report_form(self, lang: str) -> str:
        address = esc(self.site["contact_email"])
        subject = esc(self.action_subject(lang))
        fields = [
            ("name", "text", "action.field_name", "action.hint_name", True),
            ("contact", "text", "action.field_contact", "action.hint_contact", False),
            ("place", "text", "action.field_place", "action.hint_place", True),
            ("when", "text", "action.field_when", "action.hint_when", True),
            ("what", "textarea", "action.field_what", "action.hint_what", True),
        ]
        rendered = []
        for name, kind, label_key, hint_key, required in fields:
            required_attr = " required" if required else ""
            label = self.t(lang, label_key)
            hint = self.t(lang, hint_key)
            if kind == "textarea":
                field = (f'<textarea id="{name}" name="{name}"{required_attr} aria-describedby="{name}-hint" '
                         f'data-label="{esc(label)}"></textarea>')
            else:
                field = (f'<input id="{name}" name="{name}" type="text"{required_attr} '
                         f'aria-describedby="{name}-hint" data-label="{esc(label)}">')
            rendered.append(
                f'<div class="field"><label for="{name}">{esc(label)}'
                f'{" <span aria-hidden=\"true\">*</span>" if required else ""}</label>'
                f'<span class="hint" id="{name}-hint">{esc(hint)}</span>{field}</div>'
            )
        return (
            f'<form method="post" action="mailto:{address}?subject={subject}" enctype="text/plain" '
            f'data-mailto-form="{address}" data-subject="{subject}">'
            f'{"".join(rendered)}'
            f'<p><button class="button" type="submit">{esc(self.t(lang, "action.form_submit"))}</button></p>'
            f'<p class="note">{self.t(lang, "action.form_note")}</p></form>'
        )

    def summary_place_items(self, lang: str) -> str:
        items = []
        for entry in self.stats["by_place"]:
            name_key = "name_bn" if lang == "bn" else "name_en"
            if entry["count"] == 0:
                items.append(f'<li>{esc(entry[name_key])} — {esc(self.t(lang, "summary.place_unmeasured"))}</li>')
                continue
            items.append(
                f'<li>{esc(entry[name_key])} — {esc(self.t(lang, "summary.place_line"))} '
                f'{fmt_num(entry["count"])} · {esc(self.label(lang, "median"))} '
                f'{fmt_num(entry["median"]) if entry["median"] is not None else "—"} '
                f'{esc(self.label(lang, "unit_minutes"))} '
                f'({esc(self.row_ids(entry["row_ids"]))})</li>'
            )
        return "".join(items)

    def summary_page(self, lang: str) -> str:
        stats = self.stats
        coverage = stats["coverage"]
        parts = [
            '<div class="print-page">',
            f'<p class="kicker">{esc(self.t(lang, "summary.kicker"))}</p>',
            f"<h1>{esc(self.title(lang))}</h1>",
            f'<p class="note">{self.t(lang, "summary.where")}</p>',
        ]
        if self.has_data:
            parts.append(f'<p class="note">{self.t(lang, "summary.period")}</p>')
        if self.has_data and self.has_waits:
            parts.append(self.finding_note(lang))
            parts.append(self.stat_cards(lang, [
                (self.label(lang, "observations_count"), fmt_num(coverage["collected"]), ""),
                (self.label(lang, "median"), fmt_num(stats["wait"]["median"]), self.label(lang, "unit_minutes")),
                (self.label(lang, "slowest"), fmt_num(stats["wait"]["max"]), self.label(lang, "unit_minutes")),
            ]))
            parts.append(
                "<figure>"
                + charts.histogram(
                    stats["buckets"], stats["wait"]["median"],
                    title=self.t(lang, "summary.chart_alt"),
                    desc=self.t(lang, "data.chart1_desc"),
                    prefix="sum1",
                    y_label=self.label(lang, "unit_observations"),
                    h_label=self.label(lang, "unit_minutes"),
                    median_label=self.label(lang, "median"),
                    empty_note=self.t(lang, "common.chart_no_data"),
                )
                + f'<figcaption>{self.t(lang, "summary.chart_caption")}</figcaption></figure>'
            )
            parts.append(self.heading(self.t(lang, "summary.places_title"), "pin"))
            parts.append(f"<ul>{self.summary_place_items(lang)}</ul>")
            parts.append(self.heading(self.t(lang, "summary.limits_title"), "warning"))
            parts.append(f"<ul>{self.limit_items(lang, limit=3)}</ul>")
        else:
            parts.append(self.empty_card(lang, "summary.empty_body"))
            if self.stats["by_place"]:
                parts.append(self.heading(self.t(lang, "summary.places_title"), "pin"))
                parts.append(f"<ul>{self.summary_place_items(lang)}</ul>")
        parts.append(self.heading(self.t(lang, "summary.ask_title"), "checklist"))
        parts.append(f"<ol>{self.items(lang, 'summary.ask_points')}</ol>")
        if self.has_contact():
            parts.append(f'<p>{self.t(lang, "summary.contact")}</p>')
        parts.append(f'<p class="note">{self.t(lang, "summary.provenance")}</p>')
        parts.append(
            '<p class="no-print">'
            f'<button class="button" type="button" data-print>{esc(self.t(lang, "summary.print_button"))}</button></p>'
        )
        parts.append("</div>")
        return "\n".join(parts)

    def limit_items(self, lang: str, limit: int = 0) -> str:
        skipped = {
            "no_baseline", "no_cause", "cannot_generalise", "weather_not_controlled",
            "single_observer_watch", "self_selected_times",
        }
        items = []
        for finding in self.stats["audit"]:
            key = finding["key"]
            if key in skipped:
                continue
            items.append(
                f"<li>{self.t(lang, 'limitations.finding_' + key, self.finding_ns(finding, lang))}</li>"
            )
        return "".join(items[:limit] if limit else items)

    def cannot_items(self, lang: str) -> str:
        keys = ("no_cause", "cannot_generalise", "no_baseline", "weather_not_controlled",
                "single_observer_watch", "self_selected_times")
        order = {key: index for index, key in enumerate(keys)}
        findings = sorted(
            (finding for finding in self.stats["audit"] if finding["key"] in order),
            key=lambda finding: order[finding["key"]],
        )
        return "".join(
            f"<li>{self.t(lang, 'limitations.finding_' + finding['key'], self.finding_ns(finding, lang))}</li>"
            for finding in findings
        )

    def finding_ns(self, finding: dict, lang: str) -> dict:
        params = dict(finding.get("params") or {})
        place_ids = params.pop("place_ids", None)
        if place_ids is not None:
            params["places"] = ", ".join(self.dataset.place_name(place_id, lang) for place_id in place_ids)
        covered = params.pop("covered_keys", None)
        if covered is not None:
            params["covered"] = ", ".join(self.label(lang, f"part_{key}") for key in covered)
        part_key = params.pop("part_key", None)
        if part_key:
            params["part"] = self.label(lang, f"part_{part_key}")
        return {"finding": params}

    def limitations_page(self, lang: str) -> str:
        stats = self.stats
        parts = [
            f"<h1>{esc(self.t(lang, 'pages.limitations.title'))}</h1>",
            f'<p class="lede">{self.t(lang, "limitations.lede")}</p>',
            self.heading(self.t(lang, "limitations.about_title"), "warning")
            + f"<ul>{self.limit_items(lang)}</ul>",
            self.heading(self.t(lang, "limitations.cannot_title"), "shield")
            + f"<ul>{self.cannot_items(lang)}</ul>",
        ]
        if stats["missing"]:
            parts.append(self.heading(self.t(lang, "limitations.missing_title"), "table"))
            parts.append(f'<p>{self.t(lang, "limitations.missing_body")}</p>')
            parts.append(self.missing_table(lang))
        parts.append(self.heading(self.t(lang, "limitations.strengthen_title"), "spark"))
        parts.append(f"<ul>{self.items(lang, 'limitations.strengthen_points')}</ul>")
        parts.append(f'<p class="note">{self.t(lang, "limitations.method_link")}</p>')
        return "\n".join(parts)

    def not_found(self, lang: str) -> str:
        other = "bn" if lang == "en" else "en"
        body = (
            f"<h1>{esc(self.t(lang, 'notfound.title'))}</h1>"
            f"<p>{self.t(lang, 'notfound.body')}</p>"
            f'<p><a class="button" href="{self.url(lang, "index", lang)}">{esc(self.t(lang, "notfound.home"))}</a> '
            f'<a class="button secondary" href="{self.url(lang, "data", lang)}">{esc(self.t(lang, "notfound.data"))}</a></p>'
        )
        return self.layout(
            lang, "index", body,
            title_key="notfound.title", description_key="notfound.body",
        )

    # ------------------------------------------------------------------
    # outputs
    # ------------------------------------------------------------------
    def css(self) -> str:
        template = common.read_text(self.root / "src" / "site.css.tpl")

        def vars_block(palette):
            return "\n  ".join(f"--{name.replace('_', '-')}: {value};" for name, value in palette.items())

        for token, value in (
            ("{{css:light_vars}}", vars_block(self.theme["light"])),
            ("{{css:dark_vars}}", vars_block(self.theme["dark"])),
            ("{{css:radius}}", self.theme["shape"]["radius"]),
            ("{{css:radius_small}}", self.theme["shape"]["radius_small"]),
            ("{{css:radius_pill}}", self.theme["shape"].get("radius_pill", "999px")),
            ("{{css:max_width}}", self.theme["shape"]["max_width"]),
            ("{{css:font_stack}}", self.theme["type"]["font_stack"]),
            ("{{css:font_stack_bn}}", self.theme["type"]["font_stack_bn"]),
            ("{{css:font_stack_mono}}", self.theme["type"]["font_stack_mono"]),
            ("{{css:font_stack_display}}", self.theme["type"].get("font_stack_display", self.theme["type"]["font_stack"])),
        ):
            template = template.replace(token, value)
        if "{{" in template:
            raise BuildError("site.css.tpl still has an unresolved placeholder token")
        return template

    def sync_photos(self) -> list[str]:
        source = self.root / "data" / "photos"
        target = self.root / "assets" / "photos"
        removed = []
        target.mkdir(parents=True, exist_ok=True)
        wanted = {photo["file"] for photo in self.dataset.photos}
        for existing in sorted(target.iterdir()):
            if existing.is_file() and existing.name not in wanted:
                existing.unlink()
                removed.append(existing.name)
        for name in sorted(wanted):
            src = source / name
            if src.is_file():
                (target / name).write_bytes(src.read_bytes())
        return removed

    def sitemap(self) -> str:
        base = (self.site.get("site_url") or "").rstrip("/")
        if not base:
            return ""
        urls = []
        for lang in common.LANGUAGES:
            for page in PAGES:
                tail = PAGE_FILES[page] if page != "index" else ""
                path = f"{BN_DIR}/" if lang == "bn" else ""
                priority = "1.0" if page == "index" and lang == "en" else "0.6"
                urls.append(
                    f"  <url><loc>{esc(f'{base}/{path}{tail}')}</loc>"
                    f"<changefreq>weekly</changefreq><priority>{priority}</priority></url>"
                )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n"
        )

    def build(self) -> list[str]:
        renderers = {
            "index": self.home,
            "data": self.data_page,
            "map": self.map_page,
            "action": self.action_page,
            "summary": self.summary_page,
            "limitations": self.limitations_page,
        }
        self.pages = {}
        for lang in common.LANGUAGES:
            for page in PAGES:
                name = PAGE_FILES[page]
                key = name if lang == "en" else f"{BN_DIR}/{name}"
                self.pages[key] = self.layout(lang, page, renderers[page](lang))
        self.pages["404.html"] = self.not_found("en")
        self.pages[f"{BN_DIR}/404.html"] = self.not_found("bn")
        self.extra_files[".nojekyll"] = ""
        site_url = (self.site.get("site_url") or "").rstrip("/")
        robots = (
            "# The site is meant to be found; the paperwork is not.\n"
            "User-agent: *\nAllow: /\n"
            "Disallow: /docs/\nDisallow: /src/\nDisallow: /tools/\n"
        )
        sitemap = self.sitemap()
        if sitemap:
            self.extra_files["sitemap.xml"] = sitemap
            robots += f"Sitemap: {site_url}/sitemap.xml\n"
        self.extra_files["robots.txt"] = robots
        return list(self.pages)

    def bangla_review(self) -> str:
        """A side-by-side list of every Bangla string, for the author to sign off."""
        english = self.content.trees["en"]
        bangla = self.content.trees["bn"]
        rows = []
        for key, value in content_mod.iter_strings(bangla):
            original = content_mod.lookup(english, key)
            if original is content_mod.MISSING:
                original = "— missing in content.en.json —"
            if isinstance(original, list):
                original = " | ".join(str(item) for item in original)
            rows.append((key, str(original), value))
        status = self.content.bn_status or {}
        signed = bool(status.get("reviewed_all")) and bool(str(status.get("reviewer") or "").strip())
        lines = [
            "# Bangla review list",
            "",
            "Generated by `py tools/build.py` — do not edit this file, edit `src/content.bn.json`.",
            "",
            "The assignment says the Bangla wording has to be written or checked by you, and that",
            "machine translation is easy to spot in the viva. This is the whole list, side by side.",
            "",
            "How to sign it off:",
            "",
            "1. Read every row below out loud. Fix anything that sounds like a translation in",
            "   `src/content.bn.json`, then run `py tools/build.py` again.",
            "2. When the whole list reads the way you would say it, open `src/bn-status.json` and set",
            "   `\"reviewer\"` to your name and `\"reviewed_all\"` to `true`.",
            "3. Run `py tools/check.py --publish`. The review note disappears from the Bangla pages",
            "   and the check stops complaining.",
            "",
            f"Strings to read: {len(rows)}",
            f"Signed off: {'yes' if signed else 'no'}",
            "",
            "| key | English | Bangla |",
            "| --- | --- | --- |",
        ]
        for key, original, value in rows:
            clean_original = original.replace("|", "\\|").replace("\n", " ")
            clean_bangla = value.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{key}` | {clean_original} | {clean_bangla} |")
        lines.append("")
        return "\n".join(lines)

    def write(self) -> list[str]:
        written = []
        common.write_text(self.root / "assets" / "site.css", self.css())
        common.write_text(self.root / "assets" / "app.js", common.read_text(self.root / "src" / "app.js"))
        written += ["assets/site.css", "assets/app.js"]
        for name, html in self.pages.items():
            common.write_text(self.root / name, html)
            written.append(name)
        for name, text in self.extra_files.items():
            common.write_text(self.root / name, text)
            written.append(name)
        common.write_text(self.root / "data" / "stats.json", self.stats_json())
        written.append("data/stats.json")
        common.write_text(self.root / "docs" / "bangla-review.md", self.bangla_review())
        written.append("docs/bangla-review.md")
        written += [f"assets/photos/{name}" for name in self.sync_photos()]
        return written

    def stats_json(self) -> str:
        payload = {
            "_note": (
                "Generated by tools/build.py. Every figure the website shows is in here, with "
                "the row ids it came from. Do not edit by hand: edit data/*.csv and rebuild."
            ),
            "generated": self.meta,
            "data_files": self.fingerprint["files"],
            "site": self.site,
            "stats": self.stats,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main(argv=None) -> int:
    common.setup_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    root = common.repo_root()
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1])
    builder = Builder(root)
    pages = builder.build()
    written = builder.write()
    coverage = builder.stats["coverage"]
    print(f"built {len(pages)} pages from data/ (snapshot {builder.meta['data_hash_short']})")
    print(f"  observations: {coverage['collected']} (target {coverage['target']}) · "
          f"timed waits: {builder.stats['wait']['count']} · photos: {len(builder.stats['photos'])}")
    print(f"  wrote {len(written)} files")
    if builder.warnings:
        print(f"  {len(builder.warnings)} warning(s):")
        for warning in builder.warnings[:12]:
            print(f"    - {warning}")
        if len(builder.warnings) > 12:
            print(f"    ... and {len(builder.warnings) - 12} more (py tools/check.py lists them all)")
    if builder.errors:
        print(f"  {len(builder.errors)} ERROR(S) — pages were written but are not publishable:")
        for error in builder.errors[:20]:
            print(f"    ! {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
