"""Draw the charts as inline SVG, using the standard library only.

Colour is never hard-coded here: every shape gets a CSS class, and the
stylesheet (generated from src/theme.json) decides the colour. Gradients work
the same way — the SVG only points at a gradient by id, and the stops inside it
are styled from the theme. That is what makes the charts follow light mode, dark
mode and print, and it is also why a chart cannot quietly use a colour that
failed the contrast check.

The charts carry no wording of their own. Every label is passed in by the build,
which gets it from the content files, so a chart is as bilingual as the page.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402

W = 360.0
FONT = 12.5
SMALL = 11.5
CHARS_PER_LINE = 46


def _short(text: str, limit: int = 16) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _wrap(text: str, limit: int = CHARS_PER_LINE) -> list[str]:
    """SVG text does not wrap itself, so long notes are broken by hand."""
    words = (text or "").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _svg_open(prefix: str, title: str, desc: str, height: float) -> list[str]:
    return [
        f'<svg class="chart" viewBox="0 0 {common.fmt_num(W)} {common.fmt_num(height)}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" focusable="false" '
        f'aria-labelledby="{prefix}-t {prefix}-d">',
        f'<title id="{prefix}-t">{common.esc(title)}</title>',
        f'<desc id="{prefix}-d">{common.esc(desc)}</desc>',
    ]


def _gradient(gid: str, first: str, second: str, *, vertical: bool = True) -> str:
    """A gradient whose two stops are coloured by the stylesheet."""
    if vertical:
        return (
            f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop class="{first}" offset="0"/><stop class="{second}" offset="1"/>'
            "</linearGradient>"
        )
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">'
        f'<stop class="{first}" offset="0"/><stop class="{second}" offset="1"/>'
        "</linearGradient>"
    )


def _text(x, y, content, *, cls="c-label", anchor="start", size=SMALL):
    return (
        f'<text class="{cls}" x="{common.fmt_num(x, 1)}" y="{common.fmt_num(y, 1)}" '
        f'text-anchor="{anchor}" font-size="{common.fmt_num(size, 1)}">{common.esc(content)}</text>'
    )


def _side_label(x: float, y: float, content: str) -> str:
    """The y-axis title, written up the left edge so the two axis labels cannot collide."""
    return (
        f'<text class="c-axis-label" x="0" y="0" text-anchor="middle" font-size="{common.fmt_num(SMALL, 1)}" '
        f'transform="translate({common.fmt_num(x, 1)} {common.fmt_num(y, 1)}) rotate(-90)">'
        f'{common.esc(content)}</text>'
    )


def _chip(cx: float, cy: float, content: str, *, cls="c-chip", text_cls="c-chip-text", size=SMALL) -> str:
    """A small rounded label, sized from the text it holds."""
    width = len(content) * (size * 0.56) + 14
    height = size + 7
    return (
        f'<rect class="{cls}" x="{common.fmt_num(cx - width / 2, 1)}" '
        f'y="{common.fmt_num(cy - height / 2, 1)}" width="{common.fmt_num(width, 1)}" '
        f'height="{common.fmt_num(height, 1)}" rx="{common.fmt_num(height / 2, 1)}"/>'
        f'<text class="{text_cls}" x="{common.fmt_num(cx, 1)}" y="{common.fmt_num(cy + size * 0.36, 1)}" '
        f'text-anchor="middle" font-size="{common.fmt_num(size, 1)}">{common.esc(content)}</text>'
    )


def _empty_panel(prefix: str, title: str, desc: str, note: str, *, height: float = 132.0) -> str:
    """A drawn-on, deliberately empty panel: no bar is ever invented."""
    parts = _svg_open(prefix, title, desc, height)
    parts.append('<rect class="c-empty" x="16" y="14" width="328" height="72" rx="16"/>')
    parts.append(
        '<g class="c-empty-mark">'
        '<rect x="40" y="50" width="12" height="20" rx="4"/>'
        '<rect x="60" y="40" width="12" height="30" rx="4"/>'
        '<rect x="80" y="56" width="12" height="14" rx="4"/>'
        "</g>"
    )
    lines = _wrap(note)
    for index, line in enumerate(lines):
        parts.append(_text(200, 34 + index * 14, line, anchor="middle", cls="c-empty-text", size=SMALL))
    parts.append("</svg>")
    return "".join(parts)


def histogram(buckets, median, *, title, desc, prefix, y_label, h_label, median_label, empty_note) -> str:
    """Waiting time distribution on a shared linear value axis."""
    if not buckets:
        return _empty_panel(prefix, title, desc, empty_note)

    height = 236.0
    left, right, top, bottom = 32.0, 12.0, 40.0, 48.0
    plot_w = W - left - right
    plot_h = height - top - bottom

    axis_max = max(bucket["hi"] for bucket in buckets) or 1
    peak = max(bucket["count"] for bucket in buckets) or 1
    parts = _svg_open(prefix, title, desc, height)
    parts.append(f"<defs>{_gradient(f'{prefix}-bar', 'gs-bar-a', 'gs-bar-b')}</defs>")

    ticks = sorted({0, peak // 2, peak})
    for tick in ticks:
        y = top + plot_h - (tick / peak) * plot_h
        parts.append(
            f'<line class="c-grid" x1="{common.fmt_num(left)}" y1="{common.fmt_num(y)}" '
            f'x2="{common.fmt_num(left + plot_w)}" y2="{common.fmt_num(y)}"/>'
        )
        parts.append(_text(left - 6, y + 4, common.fmt_num(tick), anchor="end", cls="c-tick"))

    # bars, drawn on the same linear value axis as the median line
    # with many buckets, print every other label so the ticks never collide
    label_every = 1 if len(buckets) <= 6 else 2
    for index, bucket in enumerate(buckets):
        x = left + (bucket["lo"] / axis_max) * plot_w
        bar_w = max(3.0, ((bucket["hi"] - bucket["lo"]) / axis_max) * plot_w - 2.5)
        bar_h = (bucket["count"] / peak) * plot_h
        y = top + plot_h - bar_h
        parts.append(
            f'<rect class="c-bar" x="{common.fmt_num(x, 1)}" y="{common.fmt_num(y, 1)}" '
            f'width="{common.fmt_num(bar_w, 1)}" height="{common.fmt_num(max(bar_h, 2.0), 1)}" rx="5" '
            f'style="fill:url(#{prefix}-bar)">'
            f'<title>{common.esc(bucket["label"] + " — " + common.fmt_num(bucket["count"]) + " " + y_label)}</title>'
            f"</rect>"
        )
        if bucket["count"]:
            parts.append(_text(x + bar_w / 2, y - 5, common.fmt_num(bucket["count"]), anchor="middle", cls="c-value"))
        if index % label_every == 0:
            parts.append(_text(x + bar_w / 2, top + plot_h + 17, bucket["label"], anchor="middle", cls="c-tick"))

    # median marker, with the value in a chip so it cannot be mistaken for a bar
    if median is not None and 0 <= median <= axis_max:
        x = left + (median / axis_max) * plot_w
        parts.append(
            f'<line class="c-median" x1="{common.fmt_num(x, 1)}" y1="{common.fmt_num(top)}" '
            f'x2="{common.fmt_num(x, 1)}" y2="{common.fmt_num(top + plot_h)}"/>'
        )
        label = f"{median_label} {common.fmt_num(median)}"
        chip_x = min(max(x, 12 + len(label) * 3.3), W - 12 - len(label) * 3.3)
        parts.append(_chip(chip_x, 20, label, cls="c-chip-median", text_cls="c-chip-median-text"))

    parts.append(
        f'<line class="c-axis" x1="{common.fmt_num(left)}" y1="{common.fmt_num(top + plot_h)}" '
        f'x2="{common.fmt_num(left + plot_w)}" y2="{common.fmt_num(top + plot_h)}"/>'
    )
    parts.append(_text(left + plot_w / 2, height - 10, h_label, anchor="middle", cls="c-axis-label"))
    parts.append(_side_label(13, top + plot_h / 2, y_label))
    parts.append("</svg>")
    return "".join(parts)


def bars_by_place(entries, *, title, desc, prefix, value_label, empty_note) -> str:
    """Horizontal bars: median wait per place, so long place names stay readable."""
    rows = [entry for entry in entries if entry["median"] is not None]
    if not rows:
        return _empty_panel(prefix, title, desc, empty_note)

    row_h = 34.0
    top, bottom = 16.0, 34.0
    height = top + bottom + row_h * len(rows)
    label_w = 110.0
    value_w = 46.0
    left = label_w + 8
    plot_w = W - left - value_w
    peak = max(entry["median"] for entry in rows) or 1
    parts = _svg_open(prefix, title, desc, height)
    parts.append(
        f"<defs>{_gradient(f'{prefix}-bar', 'gs-bar-a', 'gs-bar-b', vertical=False)}"
        f"{_gradient(f'{prefix}-bar-low', 'gs-bar2-a', 'gs-bar2-b', vertical=False)}</defs>"
    )

    for index, entry in enumerate(rows):
        y = top + index * row_h
        bar_h = 16.0
        bar_y = y + 7
        ratio = entry["median"] / peak
        bar_w = max(4.0, ratio * plot_w)
        parts.append(_text(label_w, bar_y + bar_h - 3, _short(entry["label"], 16), anchor="end", cls="c-label"))
        parts.append(
            f'<rect class="c-track" x="{common.fmt_num(left)}" y="{common.fmt_num(bar_y)}" '
            f'width="{common.fmt_num(plot_w)}" height="{common.fmt_num(bar_h)}" rx="{common.fmt_num(bar_h / 2)}"/>'
        )
        gid = f"{prefix}-bar-low" if entry["low_n"] else f"{prefix}-bar"
        parts.append(
            f'<rect class="{"c-bar-2" if entry["low_n"] else "c-bar"}" x="{common.fmt_num(left)}" '
            f'y="{common.fmt_num(bar_y)}" width="{common.fmt_num(bar_w, 1)}" '
            f'height="{common.fmt_num(bar_h)}" rx="{common.fmt_num(bar_h / 2)}" style="fill:url(#{gid})">'
            f'<title>{common.esc(entry["label"] + " — " + common.fmt_num(entry["median"]) + " " + value_label + " (" + common.fmt_num(entry["timed_count"]) + ")")}</title>'
            f"</rect>"
        )
        value = common.fmt_num(entry["median"])
        chip_cx = min(left + bar_w + 8 + len(value) * 3.3, W - 10 - len(value) * 3.3)
        parts.append(_chip(chip_cx, bar_y + bar_h / 2, value))

    parts.append(_text(left, height - 10, value_label, cls="c-axis-label"))
    parts.append("</svg>")
    return "".join(parts)


def cumulative_line(by_day, *, title, desc, prefix, x_label, y_label, empty_note) -> str:
    """Running total of minutes spent waiting, one point per collection day."""
    points = [day for day in by_day if day["cumulative_minutes"] is not None]
    if len(points) < 1:
        return _empty_panel(prefix, title, desc, empty_note)

    height = 214.0
    left, right, top, bottom = 36.0, 16.0, 34.0, 46.0
    plot_w = W - left - right
    plot_h = height - top - bottom
    peak = max(day["cumulative_minutes"] for day in points) or 1
    steps = max(1, len(points) - 1)

    coords = []
    for index, day in enumerate(points):
        x = left + (index / steps) * plot_w
        y = top + plot_h - (day["cumulative_minutes"] / peak) * plot_h
        coords.append((x, y, day))

    parts = _svg_open(prefix, title, desc, height)
    parts.append(f"<defs>{_gradient(f'{prefix}-area', 'gs-area-a', 'gs-area-b')}</defs>")
    for tick in sorted({0, peak}):
        y = top + plot_h - (tick / peak) * plot_h
        parts.append(
            f'<line class="c-grid" x1="{common.fmt_num(left)}" y1="{common.fmt_num(y)}" '
            f'x2="{common.fmt_num(left + plot_w)}" y2="{common.fmt_num(y)}"/>'
        )
        parts.append(_text(left - 6, y + 4, common.fmt_num(tick), anchor="end", cls="c-tick"))

    if len(coords) > 1:
        line = " ".join(f"{common.fmt_num(x, 1)},{common.fmt_num(y, 1)}" for x, y, _ in coords)
        area = (
            f"{common.fmt_num(coords[0][0], 1)},{common.fmt_num(top + plot_h, 1)} "
            + line + " "
            + f"{common.fmt_num(coords[-1][0], 1)},{common.fmt_num(top + plot_h, 1)}"
        )
        parts.append(f'<polygon class="c-area" points="{area}" style="fill:url(#{prefix}-area)"/>')
        parts.append(f'<polyline class="c-line" points="{line}"/>')

    for x, y, day in coords:
        parts.append(
            f'<circle class="c-dot-ring" cx="{common.fmt_num(x, 1)}" cy="{common.fmt_num(y, 1)}" r="6">'
            f'<title>{common.esc(day["date"] + " — " + common.fmt_num(day["cumulative_minutes"]) + " " + y_label)}</title>'
            f"</circle>"
            f'<circle class="c-dot" cx="{common.fmt_num(x, 1)}" cy="{common.fmt_num(y, 1)}" r="3.4"/>'
        )

    # the running total at the end of the line, in a chip
    last_x, last_y, last_day = coords[-1]
    total = f"{common.fmt_num(last_day['cumulative_minutes'])} {y_label}"
    chip_cx = min(max(last_x, 10 + len(total) * 3.3), W - 10 - len(total) * 3.3)
    chip_cy = max(top - 4, last_y - 16)
    parts.append(_chip(chip_cx, chip_cy, total))

    label_every = max(1, len(coords) // 4)
    for index, (x, _y, day) in enumerate(coords):
        if index % label_every and index != len(coords) - 1:
            continue
        parts.append(_text(x, top + plot_h + 17, day["date"][5:], anchor="middle", cls="c-tick"))

    parts.append(
        f'<line class="c-axis" x1="{common.fmt_num(left)}" y1="{common.fmt_num(top + plot_h)}" '
        f'x2="{common.fmt_num(left + plot_w)}" y2="{common.fmt_num(top + plot_h)}"/>'
    )
    parts.append(_text(left + plot_w / 2, height - 10, x_label, anchor="middle", cls="c-axis-label"))
    parts.append("</svg>")
    return "".join(parts)


def place_diagram(entries, *, title, desc, prefix, count_label, median_label, unmeasured_label) -> str:
    """Labelled plan drawing of the queue area: bubble size = observations."""
    height = 250.0
    pad = 34.0
    plot_w = W - pad * 2
    plot_h = height - pad * 2

    def px(value, extent):
        value = 0.0 if value is None else max(0.0, min(100.0, value))
        return pad + (value / 100.0) * extent

    parts = _svg_open(prefix, title, desc, height)
    parts.append(
        f'<rect class="c-plot" x="{common.fmt_num(pad)}" y="{common.fmt_num(pad)}" '
        f'width="{common.fmt_num(plot_w)}" height="{common.fmt_num(plot_h)}" rx="18"/>'
    )
    for step in range(1, 4):
        x = pad + plot_w * step / 4
        y = pad + plot_h * step / 4
        parts.append(f'<line class="c-grid" x1="{common.fmt_num(x)}" y1="{common.fmt_num(pad)}" x2="{common.fmt_num(x)}" y2="{common.fmt_num(pad + plot_h)}"/>')
        parts.append(f'<line class="c-grid" x1="{common.fmt_num(pad)}" y1="{common.fmt_num(y)}" x2="{common.fmt_num(pad + plot_w)}" y2="{common.fmt_num(y)}"/>')

    if not entries:
        for index, line in enumerate(_wrap(unmeasured_label)):
            parts.append(_text(W / 2, height / 2 - 8 + index * 15, line, anchor="middle", cls="c-empty-text"))
        parts.append("</svg>")
        return "".join(parts)

    peak = max(entry["count"] for entry in entries) or 1
    for entry in entries:
        x = px(entry["diagram_x"], plot_w)
        y = px(entry["diagram_y"], plot_h)
        radius = 7.0 if entry["count"] == 0 else 9.0 + 11.0 * (entry["count"] / peak)
        if entry["count"]:
            parts.append(
                f'<circle class="c-node-ring" cx="{common.fmt_num(x, 1)}" cy="{common.fmt_num(y, 1)}" '
                f'r="{common.fmt_num(radius + 3, 1)}"/>'
            )
        cls = "c-node-empty" if entry["count"] == 0 else "c-node"
        parts.append(
            f'<circle class="{cls}" cx="{common.fmt_num(x, 1)}" cy="{common.fmt_num(y, 1)}" r="{common.fmt_num(radius, 1)}">'
            f'<title>{common.esc(entry["label"] + " — " + common.fmt_num(entry["count"]) + " " + count_label)}</title>'
            f"</circle>"
        )
        parts.append(_text(
            x, y + 3.7, common.fmt_num(entry["count"]), anchor="middle",
            cls="c-node-value" if entry["count"] else "c-node-value-empty",
        ))
        anchor = "end" if x > W * 0.62 else "start"
        dx = -radius - 7 if anchor == "end" else radius + 7
        parts.append(_text(x + dx, y - 1, _short(entry["label"], 16), anchor=anchor, cls="c-label"))
        detail = (
            f'{median_label} {common.fmt_num(entry["median"])} ({common.fmt_num(entry["timed_count"])})'
            if entry["median"] is not None else unmeasured_label
        )
        parts.append(_text(x + dx, y + 13, _short(detail, 22), anchor=anchor, cls="c-tick"))
    parts.append("</svg>")
    return "".join(parts)
