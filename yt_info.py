#!/usr/bin/env python3
"""Show channel and video title for each URL in yt.txt from feeds.db."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "feeds.db"
YT_FILE = Path.home() / "Nextcloud" / "yt.txt"


def main():
    urls = [line.strip() for line in YT_FILE.read_text().splitlines() if line.strip()]

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for url in urls:
        cur.execute(
            """
            SELECT v.link, c.title, v.title
            FROM videos v
            JOIN channels c ON c.id = v.channel_id
            WHERE v.link = ?
            """,
            (url,),
        )
        row = cur.fetchone()
        if row:
            link, channel, title = row
            print(f"{link} | {channel} | {title}")
        else:
            print(f"NOT FOUND: {url}")

    conn.close()


if __name__ == "__main__":
    main()
