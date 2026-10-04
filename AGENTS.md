# AGENTS.md

- Python 3.12 flat script repo (no src package), deps via uv. Lint: `uv run ruff check .`, Format: `uv run ruff format .`, Test: `uv run pytest -v` (unit tests only; no network/DB in tests).

## Habr email / RSS pipeline (ETL)
- `scrap.py daily|weekly|print`: scrape (`extract.py`) → processor (`habr_processor.py`) → format (`transform.py`) → email (`load.py`). Needs `email.ini` (copy from `email-example.ini`); `load.py` exits if absent.
- `habr_rss.py > habr_weekly.xml`: weekly RSS grouped 20/cast via `rss.GroupedRssPrint` (make target `habr_weekly.xml`). `rss.py` is the shared RSS 2.0 printer.

## YouTube feeds (`yt_feeds.py` + web UI)
- `yt_feeds.py`: OPML manager over SQLite `feeds.db`. Commands: `init`, `import-opml <file>`, `import-url <url>`, `fetch [--proxy] [--all]`, `list [--status] [--limit]`, `update-status --guid --status`, `stats`, `channel-stats`, `mark-viewed` (URLs from stdin → guid `yt:video:<id>`). Default proxy `http://127.0.0.1:8881`; `--proxy` also accepts SOCKS5 (`socks5://` = local DNS, `socks5h://` = DNS через прокси) — requires the PySocks dep (`yt_feeds.ensure_proxy_support` raises a readable error if it's missing). without `--all` it fetches only channels with videos in last 30 days. Statuses: `new`, `not_interested`, `viewed`, `todo`. Shorts are stored but excluded from the new-video count.
- `yt_feeds_web.py`: Flask web UI at http://localhost:5000, htmx-driven buttons (не смотреть / посмотреть / отложить). "посмотреть" appends video URL to `viewed_file` from `yt_feeds_config.json` (default `~/Nextcloud/yt.txt`); deleting a channel dumps JSONL to `deleted.txt`.
- `yt_info.py`: print channel + video title for each URL in `~/Nextcloud/yt.txt` by looking up `feeds.db`.
- `yt_rss.py`: needs `subscriptions` file (raw YouTube subscriptions page HTML). Outputs RSS to stdout (`make yt` writes `yt.xml`).

## YouTube subscriptions workflow
- Extract cookies → download → make RSS:
  - `./extract_cookies.sh ~/.mozilla/firefox/*default*/cookies.sqlite | grep youtube.com > yt_cookies.txt`
  - `make subscriptions` (uses `wget --load-cookies`)
  - `make yt` or `python3 yt_rss.py`
- Makefile `update_killdozer_cookies` / `update_karak_cookies` / `update_cubic_cookies` deploy cookies to remote servers (scp + ssh) and regenerate remote `yt.xml`.

## Web app styling
- `static/scss/style.scss` compiles to committed `static/style.css` via dart-sass CLI (`make sass`, `make sass-watch`). sass is NOT a Python dep; templates point at `/static/style.css`, so remote servers never compile it.

## Misc
- `readability_md.py`: HTML article → Markdown via the vendored local module `markdownify.py` (markdownify 0.10.3 snapshot, imported as `markdownify`; tests exercise it directly alongside the vendored `six` dep).
- `snmi_rss.py`: generate RSS for снми.рф.
- Git-ignored runtime files (don't commit): `email.ini`, `subscriptions`, `yt_cookies.txt`, `*.xml`, `feeds.db`, `viewed_urls.txt`.