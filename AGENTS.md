# AGENTS.md

- Python 3.12, flat script repo (no src package)
- Lint: `uv run ruff check .`, Format: `uv run ruff format .`, Test: `uv run pytest -v`
- `scrap.py`: Email top Habr articles. Needs `email.ini` (copy from `email-example.ini`). Args: `daily`, `weekly`, `print`
- `yt_rss.py`: Generate YouTube subscriptions RSS. Requires `subscriptions` file (see Makefile)
- `yt_feeds.py`: YouTube OPML feed manager with SQLite. Import OPML, fetch with proxy, track video status (new, not_interested, viewed, todo). Default proxy: `http://127.0.0.1:8881`
  - Commands: `init`, `import-opml <file>`, `fetch [--proxy]`, `list [--status] [--limit]`, `update-status --guid --status`, `stats`
- `habr_rss.py`: Generate weekly Habr RSS
- YouTube workflow: extract cookies → download subscriptions → generate RSS
  - Extract: `./extract_cookies.sh ~/.mozilla/firefox/*default*/cookies.sqlite | grep youtube.com > yt_cookies.txt`
  - Download: `make subscriptions` (uses `wget --load-cookies`)
  - RSS: `make yt` or `python3 yt_rss.py`
- Makefile has deployment targets for remote servers (killdozer, karak, cubic)
