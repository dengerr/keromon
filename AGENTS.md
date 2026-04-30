# AGENTS.md

- Python 3.12, flat script repo (no src package)
- No tests, lint, or typecheck configured
- `scrap.py`: Email top Habr articles. Needs `email.ini` (copy from `email-example.ini`). Args: `daily`, `weekly`, `print`
- `yt_rss.py`: Generate YouTube subscriptions RSS. Requires `subscriptions` file (see Makefile)
- `habr_rss.py`: Generate weekly Habr RSS
- YouTube workflow: extract cookies → download subscriptions → generate RSS
  - Extract: `./extract_cookies.sh ~/.mozilla/firefox/*default*/cookies.sqlite | grep youtube.com > yt_cookies.txt`
  - Download: `make subscriptions` (uses `wget --load-cookies`)
  - RSS: `make yt` or `python3 yt_rss.py`
- Makefile has deployment targets for remote servers (killdozer, karak, cubic)
