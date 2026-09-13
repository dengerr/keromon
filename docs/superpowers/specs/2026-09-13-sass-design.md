# Add SASS to keromon

Date: 2026-09-13

## Goal

Introduce SASS into the `yt_feeds_web` web app: a structured SCSS source compiles
to the existing `static/style.css` served by Flask. The CSS output must be
visually identical to the current stylesheet.

## Background

- Flask app `yt_feeds_web.py` serves `static/style.css` at `/static/style.css`.
- Two templates reference it: `yt_feeds_template.html` and
  `yt_channels_template.html`.
- The repo is Python 3.12 + uv, flat scripts, Makefile-driven tasks.
- No sass binary is currently installed on the dev machine.
- Deployment targets (killdozer, karak, cubic) run the Python app but are not
  assumed to have sass installed.

## Approach

Makefile + dart-sass CLI. The compiled CSS is committed so remote servers never
need sass.

### File layout

- `static/scss/style.scss` — new structured SCSS source (variables, nesting,
  `@each` status loop).
- `static/style.css` — compiled output, committed to the repo.

Templates are NOT changed; they keep pointing at `/static/style.css`.

### Makefile targets

```make
sass:
	sass static/scss/style.scss static/style.css

sass-watch:
	sass --watch static/scss/style.scss:static/style.css
```

`make sass` compiles once; `make sass-watch` watches for edits during dev.
Requires dart-sass installed locally (e.g. `npm i -g sass`). Remote deployments
need only the committed CSS.

### SCSS structure

Reorganize `static/style.css` 1:1 into `static/scss/style.scss`:

- Color palette as `$variables` (bg, box-bg, border, text, muted, link blue).
- Status colors (`new`, `not_interested`, `viewed`, `todo`) as a `$statuses`
  map with `@each` to generate `.video.<status>` left borders and
  `.status.<status>` badges from one source of truth.
- Nesting: `.video { .title, .meta, .buttons, &.<status> }`,
  `.channel-item { &, &:hover, &.active, .channel-link, .btn-* }`.
- Keep the existing media query for `.container` at 768px.

### Acceptance criteria

- `make sass` produces `static/style.css` identical in appearance to the
  current stylesheet.
- Templates render unchanged; both pages work.
- A single source of truth for status colors (the `$statuses` map).
- CSS is committed; deployments need no sass tooling.