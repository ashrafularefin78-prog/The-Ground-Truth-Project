"""Draw the site's pictures as inline SVG, using the standard library only.

Three rules hold for everything in this module.

* **Nothing here carries a fact.** The illustrations are decoration: they are
  hidden from screen readers with ``aria-hidden`` and they contain no numbers
  and no place names. The only graphics that are announced are the target meter
  and the flow diagram, and both take their wording and their figures from the
  caller, which takes them from ``data/stats.json``.
* **Colour comes from the stylesheet.** No fill or stroke colour is written
  here — every shape carries a CSS class, so the pictures follow light mode,
  dark mode and print, and the palette stays in one place (``src/theme.json``).
* **No image files.** Everything is inline SVG, so a page stays small and works
  with JavaScript switched off.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import common  # noqa: E402
from common import BuildError  # noqa: E402

# --------------------------------------------------------------------------
# small line icons (24x24, drawn with currentColor so CSS decides the colour)
# --------------------------------------------------------------------------
ICONS = {
    "clock": '<circle cx="12" cy="12.5" r="8"/><path d="M12 8v4.7l3.3 1.9"/>',
    "stopwatch": (
        '<circle cx="12" cy="13.5" r="7.2"/><path d="M12 9.6v3.9l2.6 1.6"/>'
        '<path d="M9.4 3.4h5.2"/><path d="M12 3.4v2.9"/>'
    ),
    "camera": (
        '<rect x="3" y="7" width="18" height="13" rx="3.2"/>'
        '<path d="M8.4 7l1.3-2.2h4.6L15.6 7"/><circle cx="12" cy="13.4" r="3.3"/>'
    ),
    "quote": '<path d="M20 5.2H4v11.2h5l3 3.2 3-3.2h5z"/>',
    "pin": (
        '<path d="M12 3.6c3.6 0 6.5 2.9 6.5 6.5 0 4.6-6.5 10.3-6.5 10.3S5.5 14.7 5.5 10.1c0-3.6 2.9-6.5 6.5-6.5z"/>'
        '<circle cx="12" cy="10.1" r="2.5"/>'
    ),
    "checklist": (
        '<path d="M4.6 7.1l1.9 1.9 3.4-4"/><path d="M4.6 16.1l1.9 1.9 3.4-4"/>'
        '<path d="M12.8 7.4h6.6"/><path d="M12.8 16.4h6.6"/>'
    ),
    "chart": (
        '<path d="M4 19.6h16"/><rect x="6.4" y="12" width="3" height="5.4" rx="1.2"/>'
        '<rect x="11.4" y="8" width="3" height="9.4" rx="1.2"/>'
        '<rect x="16.4" y="4.6" width="3" height="12.8" rx="1.2"/>'
    ),
    "gauge": (
        '<path d="M4.4 17.2a8.6 8.6 0 1115.2 0"/><path d="M12 14.4l4.2-4.6"/>'
        '<circle cx="12" cy="16.4" r="1.6"/>'
    ),
    "download": (
        '<path d="M12 3.8v10.4"/><path d="M7.9 10.4l4.1 4 4.1-4"/>'
        '<path d="M4.6 17.4v2.2h14.8v-2.2"/>'
    ),
    "refresh": '<path d="M19.4 12a7.4 7.4 0 11-2.2-5.2"/><path d="M19.7 4.6v4.2h-4.2"/>',
    "warning": (
        '<path d="M12 4.2L2.9 19.8h18.2z"/><path d="M12 10v4.4"/>'
        '<circle cx="12" cy="17.2" r="1"/>'
    ),
    "shield": '<path d="M12 3.6l7 2.7v5.2c0 4.3-3 7.6-7 9-4-1.4-7-4.7-7-9V6.3z"/>',
    "table": '<rect x="3.4" y="5" width="17.2" height="14" rx="2.6"/><path d="M3.4 9.6h17.2"/><path d="M9 9.6V19"/>',
    "spark": (
        '<path d="M11 3.6l1.9 5 5 1.9-5 1.9-1.9 5-1.9-5-5-1.9 5-1.9z"/>'
        '<path d="M18.4 16.2l.8 1.9 1.9.8-1.9.8-.8 1.9-.8-1.9-1.9-.8 1.9-.8z"/>'
    ),
    "mail": '<rect x="3" y="5.4" width="18" height="13.2" rx="2.6"/><path d="M4.2 7.4l7.8 5.4 7.8-5.4"/>',
    "edit": '<path d="M4.4 19.6h3.8l9.8-9.8-3.8-3.8-9.8 9.8z"/><path d="M14.2 5.6l3.8 3.8"/>',
    "print": (
        '<path d="M7.2 8.6V3.8h9.6v4.8"/><rect x="4.2" y="8.6" width="15.6" height="7.6" rx="2.2"/>'
        '<path d="M7.2 13.4h9.6v6.8H7.2z"/>'
    ),
    "person": '<circle cx="12" cy="8.4" r="3.6"/><path d="M4.8 19.8c1.2-3.5 4-5.3 7.2-5.3s6 1.8 7.2 5.3"/>',
}

# Glyphs drawn inside the flow diagram, in that diagram's own coordinates.
FLOW_GLYPHS = {
    "table": '<path d="M2 4h22M2 11h22M2 18h22"/><path d="M8 4v14"/>',
    "chart": '<path d="M2 20h20"/><path d="M6 20v-7M12 20V8M18 20V4"/>',
    "page": '<path d="M4 3h11l5 5v13H4z"/><path d="M15 3v5h5"/>',
}


def icon(name: str, *, size: int = 20, cls: str = "ico") -> str:
    """One small line icon. Decorative: the heading beside it carries the words."""
    paths = ICONS.get(name)
    if paths is None:
        raise BuildError(f"art.py has no icon called {name!r} (known: {', '.join(sorted(ICONS))})")
    return (
        f'<svg class="{cls}" viewBox="0 0 24 24" width="{size}" height="{size}" '
        'aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )


def brand_mark(*, size: int = 36) -> str:
    """The site mark: a clock with a short queue waiting beside it."""
    return (
        f'<svg class="brand-mark" viewBox="0 0 36 36" width="{size}" height="{size}" '
        'aria-hidden="true" focusable="false">'
        '<rect class="bm-plate" x="0" y="0" width="36" height="36" rx="11"/>'
        '<circle class="bm-face" cx="14" cy="18" r="7.3"/>'
        '<path class="bm-hand" d="M14 13.2V18h4.1"/>'
        '<circle class="bm-dot" cx="26.6" cy="11.4" r="2.1"/>'
        '<circle class="bm-dot" cx="26.6" cy="18" r="2.1"/>'
        '<circle class="bm-dot" cx="26.6" cy="24.6" r="2.1"/>'
        "</svg>"
    )


def hero_scene(*, uid: str = "hero") -> str:
    """The hero drawing: a queue at a counter, with the wait measured above it.

    Decorative only. It holds no figure, so it cannot contradict the data, and
    it is hidden from screen readers rather than described at length.
    """
    queue = [(70, "hs-person"), (128, "hs-person"), (186, "hs-person"), (244, "hs-person-front")]
    people = []
    for x, cls in queue:
        people.append(
            f'<circle class="{cls}-head" cx="{x}" cy="234" r="13.5"/>'
            f'<rect class="{cls}-body" x="{x - 16}" y="250" width="32" height="44" rx="14"/>'
        )
    return (
        f'<svg class="art art-hero" viewBox="0 0 420 320" preserveAspectRatio="xMidYMid meet" '
        'aria-hidden="true" focusable="false">'
        "<defs>"
        f'<linearGradient id="{uid}-panel" x1="0" y1="0" x2="1" y2="1">'
        '<stop class="gs-wash-a" offset="0"/><stop class="gs-wash-b" offset="1"/>'
        "</linearGradient>"
        f'<linearGradient id="{uid}-track" x1="0" y1="0" x2="1" y2="0">'
        '<stop class="gs-a" offset="0"/><stop class="gs-b" offset="1"/>'
        "</linearGradient>"
        "</defs>"
        f'<rect class="hs-panel" x="0" y="0" width="420" height="320" rx="30" '
        f'style="fill:url(#{uid}-panel)"/>'
        '<circle class="hs-halo" cx="322" cy="116" r="84"/>'
        '<path class="hs-floor" d="M34 294h356"/>'
        # the wait, drawn as a track that fills up as the queue advances
        '<rect class="hs-track" x="36" y="60" width="232" height="11" rx="5.5"/>'
        f'<rect class="hs-track-fill" x="36" y="60" width="158" height="11" rx="5.5" '
        f'style="fill:url(#{uid}-track)"/>'
        '<circle class="hs-track-dot" cx="194" cy="65.5" r="10"/>'
        # the clock hanging over the counter
        '<circle class="hs-clock" cx="322" cy="116" r="43"/>'
        '<path class="hs-hand" d="M322 88v28l19 12"/>'
        '<circle class="hs-pin" cx="322" cy="116" r="3.8"/>'
        # somebody serving, drawn first so the counter stands in front of them
        '<circle class="hs-staff-head" cx="363" cy="150" r="13"/>'
        '<rect class="hs-staff-body" x="346" y="162" width="34" height="40" rx="14"/>'
        '<rect class="hs-counter" x="330" y="166" width="66" height="128" rx="15"/>'
        '<rect class="hs-window" x="340" y="186" width="46" height="34" rx="9"/>'
        + "".join(people)
        + "</svg>"
    )


def wait_meter(percent, label: str, *, uid: str = "meter", size: int = 116) -> str:
    """A ring showing how far the collection has got.

    ``label`` is the accessible name, and it has to spell out the same numbers
    the ring draws — the caller builds both from ``data/stats.json``.
    """
    try:
        value = float(percent or 0)
    except (TypeError, ValueError):
        value = 0.0
    value = max(0.0, min(100.0, value))
    radius = 45.0
    circumference = 2 * math.pi * radius
    offset = circumference * (1 - value / 100)
    return (
        f'<svg class="art art-meter" viewBox="0 0 120 120" width="{size}" height="{size}" '
        f'role="img" aria-label="{common.esc(label)}" focusable="false">'
        f'<defs><linearGradient id="{uid}-ring" x1="0" y1="0" x2="1" y2="1">'
        '<stop class="gs-a" offset="0"/><stop class="gs-b" offset="1"/>'
        "</linearGradient></defs>"
        '<circle class="am-track" cx="60" cy="60" r="45"/>'
        f'<circle class="am-arc" cx="60" cy="60" r="45" transform="rotate(-90 60 60)" '
        f'stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}" '
        f'style="stroke:url(#{uid}-ring)"/>'
        f'<text class="am-value" x="60" y="68" text-anchor="middle">{common.fmt_num(value)}'
        '<tspan class="am-pct">%</tspan></text>'
        "</svg>"
    )


def method_diagram(nodes, title: str, desc: str, *, uid: str = "flow") -> str:
    """Raw files, then the generated stats, then the pages — as a diagram.

    ``nodes`` is three ``(label, sub_label, glyph)`` triples. The file names are
    the real ones, so the diagram cannot drift away from the pipeline.
    """
    if len(nodes) != 3:
        raise BuildError("the method diagram is drawn for exactly three steps")
    left, width, height, top = 2.0, 144.0, 78.0, 16.0
    parts = [
        f'<svg class="art art-flow" viewBox="0 0 480 132" preserveAspectRatio="xMidYMid meet" '
        f'role="img" aria-labelledby="{uid}-t {uid}-d" focusable="false">',
        f'<title id="{uid}-t">{common.esc(title)}</title>',
        f'<desc id="{uid}-d">{common.esc(desc)}</desc>',
    ]
    for index, (label, sub, glyph) in enumerate(nodes):
        # Each step is one group, so the accent node's text colours stay its own:
        # a sibling selector would reach across the other two nodes.
        x = left + index * 166
        accent = " accent" if index == 0 else ""
        parts.append(f'<g class="flow-node-group{accent}">')
        parts.append(
            f'<rect class="flow-node{" flow-node-accent" if index == 0 else ""}" '
            f'x="{common.fmt_num(x)}" y="{common.fmt_num(top)}" '
            f'width="{common.fmt_num(width)}" height="{common.fmt_num(height)}" rx="16"/>'
        )
        parts.append(
            f'<g class="flow-glyph" transform="translate({common.fmt_num(x + 14)},'
            f'{common.fmt_num(top + 13)}) scale(1.05)">{FLOW_GLYPHS[glyph]}</g>'
        )
        label_cls = "flow-label-strong" if index == 0 else "flow-label"
        parts.append(
            f'<text class="{label_cls}" x="{common.fmt_num(x + 14)}" '
            f'y="{common.fmt_num(top + 52)}">{common.esc(label)}</text>'
        )
        parts.append(
            f'<text class="flow-sub" x="{common.fmt_num(x + 14)}" '
            f'y="{common.fmt_num(top + 68)}">{common.esc(sub)}</text>'
        )
        parts.append("</g>")
        if index < 2:
            arrow_x = x + width + 5
            parts.append(
                f'<path class="flow-arrow" d="M{common.fmt_num(arrow_x)} 55h8"/>'
                f'<path class="flow-arrow-head" d="M{common.fmt_num(arrow_x + 5)} 49l6 6-6 6"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


def camera_note() -> str:
    """A drawing for the evidence section while no consented photo exists yet."""
    return (
        '<svg class="art art-empty" viewBox="0 0 220 132" preserveAspectRatio="xMidYMid meet" '
        'aria-hidden="true" focusable="false">'
        '<rect class="ea-body" x="16" y="34" width="188" height="82" rx="20"/>'
        '<rect class="ea-bump" x="88" y="20" width="44" height="16" rx="8"/>'
        '<circle class="ea-lens" cx="110" cy="75" r="26"/>'
        '<circle class="ea-lens-inner" cx="110" cy="75" r="11"/>'
        '<circle class="ea-dot" cx="176" cy="52" r="5"/>'
        '<path class="ea-flash" d="M40 52h22"/>'
        "</svg>"
    )
