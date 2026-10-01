/* Ground Truth Project — generated from src/site.css.tpl + src/theme.json.
   Do not edit assets/site.css: edit the template and run `py tools/build.py`.

   Order: tokens, base, layout, header, hero, buttons, headings, cards, metrics,
   meter, facts, charts, diagrams, tables, evidence, quote, forms, footer, print. */

:root {
  color-scheme: light dark;
  {{css:light_vars}}
  --radius: {{css:radius}};
  --radius-sm: {{css:radius_small}};
  --radius-pill: {{css:radius_pill}};
  --wrap: {{css:max_width}};
  --font: {{css:font_stack}};
  --font-bn: {{css:font_stack_bn}};
  --font-mono: {{css:font_stack_mono}};
  --font-display: {{css:font_stack_display}};
}

@media (prefers-color-scheme: dark) {
  :root {
    {{css:dark_vars}}
  }
}

/* ---------- base ---------- */
*, *::before, *::after { box-sizing: border-box; }

html {
  -webkit-text-size-adjust: 100%;
  /* Hidden on the root so the viewport never scrolls sideways; on the body it
     would turn the body into a scroll container and break the sticky header. */
  overflow-x: hidden;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 1rem;
  line-height: 1.65;
  overflow-x: clip;
  -webkit-font-smoothing: antialiased;
}

html[lang="bn"] body { font-family: var(--font-bn); line-height: 1.9; }

img { max-width: 100%; height: auto; display: block; }

a { color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 3px; }
a:hover { text-decoration-thickness: 2px; }

::selection { background: var(--accent-soft); color: var(--text); }

:focus-visible {
  outline: 3px solid var(--accent);
  outline-offset: 2px;
  border-radius: 5px;
}

h1, h2, h3 { line-height: 1.22; margin: 0 0 .55rem; letter-spacing: -.012em; font-family: var(--font-display); }
html[lang="bn"] h1, html[lang="bn"] h2, html[lang="bn"] h3 {
  font-family: var(--font-bn);
  letter-spacing: 0;
  line-height: 1.55;
}
h1 { font-size: clamp(2rem, 1.45rem + 2.5vw, 3.05rem); letter-spacing: -.024em; }
h2 { font-size: clamp(1.32rem, 1.12rem + 1vw, 1.8rem); margin-top: 2rem; }
h3 { font-family: var(--font); font-size: 1.06rem; font-weight: 700; margin-top: 1.4rem; }
p { margin: 0 0 1rem; }
p, li { overflow-wrap: break-word; }
ul, ol { margin: 0 0 1rem; padding-left: 1.3rem; }
li { margin-bottom: .35rem; }
li::marker { color: var(--accent); }
h1, h2, h3, [id] { scroll-margin-top: 6rem; }

/* ---------- layout + utilities ---------- */
.wrap { max-width: var(--wrap); margin: 0 auto; padding: 1rem; }
main { display: block; padding-bottom: 3rem; }

.skip-link {
  position: absolute; left: -9999px; top: 0; z-index: 40;
  background: var(--accent); color: var(--accent-text);
  padding: .7rem 1rem; border-radius: 0 0 var(--radius-sm) 0; font-weight: 600;
}
.skip-link:focus { left: 0; }

.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}

.note { color: var(--muted); font-size: .9rem; }
.lede { font-size: clamp(1.02rem, .97rem + .35vw, 1.16rem); color: var(--muted); max-width: 62ch; }
.badge {
  display: inline-block; background: var(--accent-soft); color: var(--accent);
  border-radius: var(--radius-pill); padding: .12rem .65rem; font-size: .78rem; font-weight: 600;
}
.review-flag { border-left: 4px solid var(--warn); }

.ico { display: block; flex: 0 0 auto; }

/* ---------- header ---------- */
.site-header {
  position: sticky; top: 0; z-index: 30;
  background: var(--header-bg);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--border);
}
@supports not ((backdrop-filter: blur(2px)) or (-webkit-backdrop-filter: blur(2px))) {
  .site-header { background: var(--surface); }
}
.site-header .wrap { display: flex; flex-wrap: wrap; align-items: center; gap: .45rem .9rem; padding: .6rem 1rem; }

.brand {
  display: flex; align-items: center; gap: .6rem;
  flex: 1 1 13rem; min-width: 0;
  color: var(--text); text-decoration: none;
}
.brand-mark { display: block; border-radius: 12px; box-shadow: var(--shadow-1); }
.brand-text { min-width: 0; }
.brand-text strong { display: block; font-size: .97rem; font-weight: 700; letter-spacing: -.015em; }
.brand-text span { display: block; font-size: .76rem; color: var(--muted); }

.site-nav ul { list-style: none; display: flex; flex-wrap: wrap; gap: .1rem; margin: 0; padding: 0; }
.site-nav a {
  display: block; padding: .32rem .7rem; border-radius: var(--radius-pill);
  text-decoration: none; font-size: .9rem; font-weight: 500; color: var(--muted);
  white-space: nowrap;
}
.site-nav a:hover { color: var(--text); background: var(--surface-2); }
.site-nav a[aria-current="page"] {
  background: var(--accent-soft); color: var(--accent); font-weight: 700;
}

.lang-switch { margin: 0; }
.lang-switch a {
  display: inline-flex; align-items: center; gap: .35rem;
  padding: .32rem .75rem; border: 1px solid var(--border); border-radius: var(--radius-pill);
  background: var(--surface); text-decoration: none; font-size: .85rem; font-weight: 600;
  white-space: nowrap;
}
.lang-switch a:hover { border-color: var(--accent); }

/* On a phone the header gets one row for the mark and the language switch, and
   one scrollable strip of tabs underneath, instead of a three-line block that
   eats a third of the screen. The wordmark is still announced by a screen
   reader, because it stays in the document and is only moved out of sight. */
@media (max-width: 34rem) {
  .site-header .wrap { gap: .35rem .6rem; }
  .brand { flex: 1 1 auto; min-width: 0; }
  .brand-text {
    position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0;
    overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
  }
  .lang-switch { margin-left: auto; }
  .lang-switch a { padding: .3rem .6rem; font-size: .8rem; }
  .site-nav { order: 3; flex-basis: 100%; min-width: 0; }
  .site-nav ul {
    flex-wrap: nowrap; max-width: 100%;
    overflow-x: auto; scrollbar-width: none;
    -webkit-overflow-scrolling: touch;
  }
  .site-nav ul::-webkit-scrollbar { display: none; }
}

/* ---------- hero ---------- */
.hero {
  position: relative; overflow: hidden;
  margin: .6rem 0 1.6rem; padding: 1.5rem 1.2rem 1.6rem;
  border: 1px solid var(--border); border-radius: calc(var(--radius) + 8px);
  background-image: linear-gradient(135deg, var(--hero-1), var(--hero-2));
  box-shadow: var(--shadow-1);
}
.hero::after {
  content: ""; position: absolute; z-index: 0; pointer-events: none;
  width: 22rem; height: 22rem; right: -7rem; top: -9rem; border-radius: 50%;
  background-image: radial-gradient(circle at center, var(--accent-soft), transparent 68%);
}
.hero > * { position: relative; z-index: 1; }

.hero-copy { max-width: 40rem; }
.hero h1 { margin-bottom: .7rem; }

.kicker {
  display: inline-flex; align-items: center; gap: .45rem;
  margin: 0 0 .8rem; padding: .26rem .7rem;
  border: 1px solid var(--border); border-radius: var(--radius-pill);
  background: var(--surface); color: var(--muted);
  font-size: .72rem; font-weight: 700; letter-spacing: .09em; text-transform: uppercase;
}
.kicker::before {
  content: ""; width: .5rem; height: .5rem; border-radius: 50%;
  background-image: linear-gradient(135deg, var(--grad-1), var(--grad-2));
}

.hero-actions { display: flex; flex-wrap: wrap; gap: .6rem; margin: 1.2rem 0 0; }

.hero-art { margin: 1.4rem 0 0; display: flex; align-items: center; justify-content: center; }
/* Full width, so a small photograph still fills the column instead of sitting
   at its own pixel size inside a centred flex row. */
.hero-figure { margin: 0; width: 100%; }
.hero-photo {
  width: 100%; aspect-ratio: 4 / 3; object-fit: cover;
  border: 1px solid var(--border); border-radius: calc(var(--radius) + 2px);
  box-shadow: var(--shadow-2);
}

@media (min-width: 52rem) {
  .hero { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr); gap: 1.75rem; align-items: center; padding: 2.2rem 2.2rem 2.1rem; }
  .hero-art { margin: 0; }
  .hero-copy { max-width: none; }
}

/* ---------- buttons ---------- */
.button {
  display: inline-flex; align-items: center; justify-content: center; gap: .45rem;
  padding: .62rem 1.1rem; border: 1px solid transparent; border-radius: var(--radius-pill);
  background-image: linear-gradient(120deg, var(--grad-1), var(--grad-2));
  color: var(--accent-text); font: inherit; font-size: .95rem; font-weight: 600;
  text-decoration: none; cursor: pointer; box-shadow: var(--shadow-1);
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.button:hover { transform: translateY(-1px); box-shadow: var(--shadow-2); }
.button:active { transform: translateY(0); }
.button.secondary, .button.ghost {
  background-image: none; background-color: var(--surface);
  color: var(--accent); border-color: var(--border);
}
.button.secondary:hover { border-color: var(--accent); }
.button[disabled] { opacity: .6; cursor: not-allowed; transform: none; }

/* ---------- section headings ---------- */
.section {
  display: flex; align-items: center; gap: .65rem;
  margin: 2.3rem 0 .9rem; padding-bottom: .5rem;
  border-bottom: 1px solid var(--border);
}
.section > span:last-child { min-width: 0; }
.ico-chip {
  display: grid; place-items: center; flex: 0 0 auto;
  width: 2.1rem; height: 2.1rem; border-radius: 13px;
  border: 1px solid var(--border);
  background-image: linear-gradient(135deg, var(--accent-soft), var(--accent-2-soft));
  color: var(--accent);
}
h3 .ico-chip { width: 1.6rem; height: 1.6rem; border-radius: 10px; }

/* ---------- cards ---------- */
.card {
  position: relative;
  margin: 1.2rem 0; padding: 1.2rem 1.2rem 1.1rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-1);
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.card:hover { transform: translateY(-2px); box-shadow: var(--shadow-2); }
.card > :last-child { margin-bottom: 0; }
.card-title {
  margin: 0 0 .45rem; font-family: var(--font);
  font-size: .77rem; font-weight: 700; letter-spacing: .09em;
  text-transform: uppercase; color: var(--muted);
}
.card-headline { padding-top: 1.4rem; }
.card-headline::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 4px;
  border-radius: var(--radius) var(--radius) 0 0;
  background-image: linear-gradient(90deg, var(--grad-1), var(--grad-2));
}
.card-headline .lede { color: var(--text); font-weight: 500; margin-bottom: .8rem; }
.card-headline .card-title { color: var(--accent); }

.empty-state { border-style: dashed; box-shadow: none; }
.empty-state:hover { transform: none; box-shadow: none; }
.empty-state .card-title { color: var(--warn); }
.empty-state .card-title::before {
  content: ""; display: inline-block; vertical-align: middle;
  width: .55rem; height: .55rem; margin-right: .45rem; border-radius: 50%;
  background-image: linear-gradient(135deg, var(--warn), var(--accent-2));
}

/* ---------- metric band ---------- */
.metrics {
  display: grid; grid-template-columns: 1fr; gap: .85rem;
  margin: 1.3rem 0; padding: 0;
}
@media (min-width: 34rem) {
  .metrics { grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr)); }
}
.metric {
  position: relative; margin: 0; padding: 1.05rem 1.05rem .95rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-1);
  transition: transform .18s ease, box-shadow .18s ease;
}
.metric:hover { transform: translateY(-2px); box-shadow: var(--shadow-2); }
.metric::before {
  content: ""; position: absolute; inset: 0 0 auto 0; height: 3px;
  border-radius: var(--radius) var(--radius) 0 0;
  background-image: linear-gradient(90deg, var(--grad-1), var(--grad-2));
  opacity: .9;
}
.metric dt {
  display: flex; align-items: center; gap: .4rem; margin: 0 0 .4rem;
  font-size: .76rem; font-weight: 700; letter-spacing: .05em;
  text-transform: uppercase; color: var(--muted);
}
.metric-icon { color: var(--accent); display: inline-flex; }
.metric dd {
  margin: 0; font-size: clamp(1.75rem, 1.45rem + 1.3vw, 2.35rem);
  font-weight: 700; line-height: 1.05; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums;
}
.metric dd small {
  display: inline-block; margin-left: .32rem; font-size: .82rem; font-weight: 500;
  color: var(--muted); letter-spacing: 0;
}

/* ---------- target meter ---------- */
.meter { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; margin: .9rem 0 .3rem; }
.meter-ring { flex: 0 0 auto; display: flex; }
.meter-copy { flex: 1 1 12rem; min-width: 0; }
.art-meter { width: 7.25rem; height: 7.25rem; }
.am-track { fill: none; stroke: var(--surface-3); stroke-width: 10; }
.am-arc { fill: none; stroke-width: 10; stroke-linecap: round; transition: stroke-dashoffset .5s ease; }
.am-value { fill: var(--text); font-family: var(--font); font-size: 30px; font-weight: 700; }
.am-pct { fill: var(--muted); font-size: 15px; font-weight: 600; }

/* ---------- facts list ---------- */
.facts { display: grid; grid-template-columns: 1fr; gap: .15rem 1rem; margin: 1.2rem 0; padding: 0; }
.facts dt { color: var(--muted); font-size: .85rem; }
.facts dd { margin: 0 0 .55rem; font-weight: 650; font-variant-numeric: tabular-nums; }
@media (min-width: 34rem) {
  .facts { grid-template-columns: max-content 1fr; }
  .facts dd { margin-bottom: .3rem; }
}

/* ---------- charts ---------- */
figure { margin: 1.5rem 0; }
figure > figcaption { color: var(--muted); font-size: .88rem; margin-top: .6rem; line-height: 1.6; }
figure > figcaption strong { color: var(--text); }
.chart { width: 100%; height: auto; max-width: 42rem; display: block; overflow: visible; }
.chart text { font-family: var(--font); font-variant-numeric: tabular-nums; }
html[lang="bn"] .chart text { font-family: var(--font-bn); }

.c-grid { stroke: var(--border); stroke-width: 1; stroke-dasharray: 3 4; }
.c-axis { stroke: var(--surface-3); stroke-width: 1.5; }
.c-track { fill: var(--surface-2); }
.c-bar { fill: var(--series-1); }
.c-bar-2 { fill: var(--series-3); }
.c-area { fill: var(--series-2); opacity: .14; }
.c-line { fill: none; stroke: var(--series-2); stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; }
.c-dot { fill: var(--series-2); }
.c-dot-ring { fill: var(--surface); }
.c-median { stroke: var(--danger); stroke-width: 1.5; stroke-dasharray: 4 4; }
.c-median-text { fill: var(--danger); font-weight: 700; }
.c-label { fill: var(--text); }
.c-tick, .c-axis-label { fill: var(--muted); }
.c-value { fill: var(--text); font-weight: 700; font-variant-numeric: tabular-nums; }
.c-plot { fill: var(--surface-2); stroke: var(--border); stroke-width: 1; }
.c-node { fill: var(--series-1); opacity: .94; }
.c-node-ring { fill: var(--surface); }
.c-node-empty { fill: var(--surface-2); stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 3 3; }
.c-node-value { fill: var(--accent-text); font-weight: 700; }
.c-node-value-empty { fill: var(--muted); font-weight: 700; }
.c-empty { fill: var(--surface-2); stroke: var(--border); stroke-width: 1; stroke-dasharray: 5 5; }
.c-empty-mark { fill: var(--border); }
.c-empty-text { fill: var(--muted); }
.c-chip { fill: var(--surface); stroke: var(--border); }
.c-chip-text { fill: var(--text); font-weight: 700; }
.c-chip-median { fill: var(--danger-soft); stroke: var(--danger); }
.c-chip-median-text { fill: var(--danger); font-weight: 700; }

/* Gradient stops. The colours stay in the stylesheet: the SVG only points at
   the gradient by id, so light, dark and print all follow theme.json. */
.gs-a { stop-color: var(--grad-1); stop-opacity: 1; }
.gs-b { stop-color: var(--grad-2); stop-opacity: 1; }
.gs-wash-a { stop-color: var(--hero-1); stop-opacity: 1; }
.gs-wash-b { stop-color: var(--hero-2); stop-opacity: 1; }
.gs-bar-a { stop-color: var(--series-1); stop-opacity: 1; }
.gs-bar-b { stop-color: var(--series-3); stop-opacity: .92; }
.gs-bar2-a { stop-color: var(--series-2); stop-opacity: 1; }
.gs-bar2-b { stop-color: var(--series-5); stop-opacity: .95; }
.gs-area-a { stop-color: var(--series-2); stop-opacity: .32; }
.gs-area-b { stop-color: var(--series-2); stop-opacity: 0; }

/* ---------- illustrations ---------- */
.art { display: block; width: 100%; height: auto; }
.art-hero { max-width: 27rem; }
.art-empty { max-width: 14rem; }
.art-flow { max-width: 34rem; }

.hs-panel { fill: var(--surface); }
.hs-halo { fill: var(--accent-soft); opacity: .75; }
.hs-floor { fill: none; stroke: var(--border); stroke-width: 3; stroke-linecap: round; }
.hs-track { fill: var(--surface-3); }
.hs-track-dot { fill: var(--surface); stroke: var(--accent); stroke-width: 3.5; }
.hs-clock { fill: var(--surface); stroke: var(--border); stroke-width: 3; }
.hs-hand { fill: none; stroke: var(--accent); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
.hs-pin { fill: var(--accent); }
.hs-counter { fill: var(--surface-2); stroke: var(--border); stroke-width: 3; }
.hs-window { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 2.5; }
.hs-staff-head, .hs-staff-body { fill: var(--surface-3); stroke: var(--border); stroke-width: 2.5; }
.hs-person-head, .hs-person-body { fill: var(--surface-3); stroke: var(--border); stroke-width: 2.5; }
.hs-person-front-head, .hs-person-front-body { fill: var(--accent); stroke: var(--accent); }

.brand-mark .bm-plate { fill: var(--accent); }
.brand-mark .bm-face { fill: none; stroke: var(--accent-text); stroke-width: 2.6; }
.brand-mark .bm-hand { fill: none; stroke: var(--accent-text); stroke-width: 2.6; stroke-linecap: round; }
.brand-mark .bm-dot { fill: var(--accent-text); }

.flow-node { fill: var(--surface); stroke: var(--border); stroke-width: 2; }
.flow-node-accent { fill: var(--accent); stroke: var(--accent); }
.flow-glyph { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.flow-label { fill: var(--text); font-size: 12.5px; font-weight: 700; font-family: var(--font-mono); }
.flow-label-strong { fill: var(--accent-text); font-size: 12.5px; font-weight: 700; font-family: var(--font-mono); }
.flow-sub { fill: var(--muted); font-size: 10.5px; }
.flow-arrow { stroke: var(--border); stroke-width: 2.5; }
.flow-arrow-head { fill: none; stroke: var(--accent); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; }
.flow-node-group.accent .flow-glyph { stroke: var(--accent-text); }
.flow-node-group.accent .flow-label-strong { fill: var(--accent-text); }
.flow-node-group.accent .flow-sub { fill: var(--accent-text); opacity: .85; }

.ea-body, .ea-bump { fill: var(--surface-2); stroke: var(--border); stroke-width: 3; }
.ea-lens { fill: var(--surface); stroke: var(--border); stroke-width: 3; }
.ea-lens-inner { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 2.5; }
.ea-dot { fill: var(--accent-2); }
.ea-flash { fill: none; stroke: var(--accent); stroke-width: 3.5; stroke-linecap: round; }

/* ---------- tables ---------- */
.table-wrap {
  overflow-x: auto; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius-sm);
}
table { border-collapse: collapse; width: 100%; font-size: .88rem; font-variant-numeric: tabular-nums; }
caption { text-align: left; padding: .6rem .75rem; color: var(--muted); font-size: .85rem; }
th, td { padding: .5rem .75rem; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
th {
  background: var(--surface-2); font-size: .76rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: .05em; color: var(--muted);
}
tbody tr:last-child td { border-bottom: 0; }
td.wrap-cell { white-space: normal; min-width: 12rem; }
.row-ids { font-family: var(--font-mono); font-size: .78rem; color: var(--muted); white-space: normal; }

details {
  margin: .6rem 0 1.2rem; padding: .5rem .7rem;
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
}
details[open] { background: var(--surface); }
summary { cursor: pointer; font-weight: 600; font-size: .9rem; }
summary:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* ---------- evidence ---------- */
.evidence { display: grid; gap: .9rem; grid-template-columns: 1fr; margin: 1.2rem 0; }
@media (min-width: 34rem) { .evidence { grid-template-columns: 1fr 1fr; } }
.evidence figure {
  margin: 0; overflow: hidden; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-1);
  transition: transform .18s ease, box-shadow .18s ease;
}
.evidence figure:hover { transform: translateY(-3px); box-shadow: var(--shadow-2); }
.evidence img { width: 100%; aspect-ratio: 4 / 3; object-fit: cover; transition: transform .4s ease; }
.evidence figure:hover img { transform: scale(1.03); }
.evidence figcaption { padding: .7rem .85rem; margin: 0; font-size: .85rem; color: var(--muted); }
.evidence figcaption strong { color: var(--text); }

.evidence-empty { display: grid; place-items: center; text-align: center; gap: .3rem; padding: 1.6rem 1.2rem; }
.evidence-empty p { max-width: 46ch; }
.art-empty { opacity: .95; }

/* ---------- interview ---------- */
blockquote.quote {
  position: relative; margin: 1.3rem 0; padding: 1.25rem 1.2rem 1rem 3rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow-1);
}
blockquote.quote::before {
  content: "\201C"; position: absolute; left: .9rem; top: .25rem;
  font-family: var(--font-display); font-size: 2.9rem; line-height: 1;
  color: var(--accent); opacity: .5;
}
blockquote.quote p { margin: 0 0 .55rem; font-size: 1.06rem; font-style: italic; }
blockquote.quote footer { color: var(--muted); font-size: .85rem; }

/* ---------- forms and the action page ---------- */
form { margin: 1.3rem 0; }
.field { margin-bottom: 1rem; }
.field label { display: block; font-weight: 600; font-size: .9rem; margin-bottom: .25rem; }
.field .hint { display: block; color: var(--muted); font-size: .82rem; margin-bottom: .3rem; }
input, textarea, select {
  width: 100%; padding: .6rem .7rem; font: inherit; color: var(--text);
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
  transition: border-color .15s ease;
}
input:hover, textarea:hover, select:hover { border-color: var(--accent); }
textarea { min-height: 6.5rem; resize: vertical; }
input:focus-visible, textarea:focus-visible, select:focus-visible { outline: 3px solid var(--accent); outline-offset: 1px; }

.copy-note { font-size: .85rem; color: var(--muted); }
.is-copied { background-image: none; background-color: var(--ok); border-color: var(--ok); color: var(--accent-text); }
.copy-state .when-done { display: none; }
.copy-state.is-copied .when-idle { display: none; }
.copy-state.is-copied .when-done { display: inline; }

pre.message {
  white-space: pre-wrap; overflow-wrap: break-word; font-family: var(--font-mono);
  font-size: .85rem; line-height: 1.75; margin: .6rem 0 1rem; padding: .9rem;
  background: var(--surface-2); border: 1px solid var(--border); border-radius: var(--radius-sm);
}

.downloads { list-style: none; padding: 0; display: grid; gap: .55rem; margin: 1.2rem 0; }
.downloads a {
  display: flex; align-items: center; gap: .6rem; padding: .75rem .95rem;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
  text-decoration: none; font-weight: 600; box-shadow: var(--shadow-1);
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}
.downloads a::before {
  content: ""; flex: 0 0 auto; width: .55rem; height: .55rem; border-radius: 50%;
  background-image: linear-gradient(135deg, var(--grad-1), var(--grad-2));
}
.downloads a:hover { transform: translateY(-1px); border-color: var(--accent); box-shadow: var(--shadow-2); }

/* ---------- footer ---------- */
.site-footer {
  margin-top: 2.5rem; border-top: 1px solid var(--border);
  background: var(--surface); color: var(--muted); font-size: .86rem;
}
.site-footer .wrap { padding: 1.6rem 1rem 2.2rem; }
.footer-top {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: .8rem; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border);
}
.footer-brand { display: flex; align-items: center; gap: .65rem; color: var(--text); font-weight: 700; }
.footer-brand span { max-width: 22ch; line-height: 1.35; }
.site-footer p { max-width: 78ch; }
.site-footer a { color: var(--accent); text-decoration: none; }
.site-footer a:hover { text-decoration: underline; }
.site-footer ul { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: .3rem 1rem; }
.fingerprint { font-family: var(--font-mono); font-size: .76rem; word-break: break-all; }

/* ---------- phone: tables stack into labelled rows ---------- */
/* Under 34rem every row of a data table becomes a small labelled block, so the
   values are readable without sliding the table sideways. Each cell carries its
   column name in data-label, written by the build. */
@media (max-width: 34rem) {
  table { font-size: .85rem; }
  th, td { white-space: normal; }
  .row-ids { font-family: var(--font); }
  table.responsive thead { display: none; }
  table.responsive caption { padding-bottom: .3rem; }
  table.responsive tr { display: block; border-bottom: 1px solid var(--border); padding: .5rem 0; }
  table.responsive tr:last-child { border-bottom: 0; }
  table.responsive td {
    display: flex; gap: .75rem; justify-content: space-between; align-items: baseline;
    border: 0; padding: .15rem .75rem; text-align: right;
  }
  table.responsive td::before {
    content: attr(data-label); color: var(--muted); font-size: .78rem;
    text-align: left; flex: 0 0 42%;
  }
  table.responsive td:first-child {
    font-weight: 700; text-align: left; font-size: .95rem; padding-bottom: .35rem;
  }
  table.responsive td:first-child::before { content: none; }
  .wrap-cell { min-width: 0; }
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ---------- print ---------- */
@page { size: A4; margin: 12mm; }

@media print {
  :root {
    color-scheme: light;
    {{css:light_vars}}
  }
  html, body { overflow: visible; }
  body { background: #fff; color: #000; font-size: 10.5pt; }
  .site-header, .site-footer, .no-print, .skip-link, .ico-chip, .art-hero, .art-empty, .hero::after { display: none !important; }
  .wrap { max-width: none; padding: 0; }
  .hero { background-image: none; border: 1px solid #999; border-radius: 0; padding: 0 0 .5rem; box-shadow: none; }
  .card, .metric, .stat, .evidence figure, .table-wrap, .downloads a, blockquote.quote {
    border-color: #999; box-shadow: none !important;
  }
  .card:hover, .metric:hover, .evidence figure:hover, .downloads a:hover { transform: none; }
  .metric::before, .card-headline::before { display: none; }
  .button, .button.secondary {
    background-image: none !important; background-color: #fff !important;
    color: #000 !important; border: 1px solid #666; box-shadow: none;
  }
  figure, table, .card, .metric, blockquote.quote { break-inside: avoid; }
  .print-break { break-before: page; }
  details { border: 0; padding: 0; background: #fff; }
  details > summary { list-style: none; }
  details:not([open]) > *:not(summary) { display: block; }
  a[href^="http"]::after { content: " (" attr(href) ")"; font-size: .8em; color: #444; word-break: break-all; }
  .chart { max-width: 100%; }
  .art-flow { max-width: 100%; }
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
