import argparse
import html
import sqlite3
import sys
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
DB_FILE = "feeds.db"
VALID_STATUSES = ["new", "not_interested", "viewed", "todo"]


def adapt_datetime(val):
    return val.isoformat()


def convert_datetime(val):
    return datetime.fromisoformat(val.decode("utf-8"))


sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


def get_db():
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                xml_url TEXT UNIQUE NOT NULL,
                html_url TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                description TEXT,
                pub_date TIMESTAMP,
                guid TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'new',
                shorts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id)
            )
        """)
        c.execute("PRAGMA table_info(videos)")
        columns = [row[1] for row in c.fetchall()]
        if "shorts" not in columns:
            c.execute("ALTER TABLE videos ADD COLUMN shorts INTEGER DEFAULT 0")
        conn.commit()


def parse_atom_feed(content):
    root = ET.fromstring(content)
    entries = root.findall("atom:entry", ATOM_NS)
    items = []
    for entry in entries:
        title = entry.find("atom:title", ATOM_NS).text
        link = ""
        for link_elem in entry.findall("atom:link", ATOM_NS):
            if (
                link_elem.get("rel") == "alternate"
                and link_elem.get("href") is not None
            ):
                link = link_elem.get("href")
                break
        desc_elem = entry.find("atom:summary", ATOM_NS) or entry.find(
            "atom:content", ATOM_NS
        )
        description = (
            html.unescape(desc_elem.text)
            if desc_elem is not None and desc_elem.text
            else ""
        )
        pub_date_str = entry.find("atom:published", ATOM_NS).text
        pub_date = (
            datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
            if pub_date_str
            else None
        )
        guid = entry.find("atom:id", ATOM_NS).text
        is_shorts = 1 if "/shorts/" in link else 0
        items.append(
            {
                "title": title,
                "link": link,
                "description": description,
                "pub_date": pub_date,
                "guid": guid,
                "shorts": is_shorts,
            }
        )
    return items


def parse_atom_channel(content):
    root = ET.fromstring(content)
    title_elem = root.find("atom:title", ATOM_NS)
    title = title_elem.text if title_elem is not None else "Unknown"
    html_url = ""
    for link_elem in root.findall("atom:link", ATOM_NS):
        if link_elem.get("rel") in ("alternate", None) and link_elem.get("href"):
            html_url = link_elem.get("href")
            break
    return title, html_url


def get_session(proxy=None):
    session = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session


def fetch_feed(url, proxy=None):
    try:
        session = get_session(proxy)
        resp = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        return parse_atom_feed(resp.text)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return []


def import_opml(opml_path):
    with db_connection() as conn:
        c = conn.cursor()
        tree = ET.parse(opml_path)
        root = tree.getroot()
        outlines = root.findall('.//outline[@type="rss"]')
        for outline in outlines:
            title = outline.get("title") or outline.get("text")
            xml_url = outline.get("xmlUrl")
            html_url = outline.get("htmlUrl")
            if not xml_url:
                continue
            c.execute(
                """
                INSERT OR IGNORE INTO channels (title, xml_url, html_url)
                VALUES (?, ?, ?)
            """,
                (title, xml_url, html_url),
            )
        conn.commit()
    print(f"Imported {len(outlines)} channels from {opml_path}")


def import_url(rss_url, proxy=None):
    try:
        session = get_session(proxy)
        resp = session.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        title, html_url = parse_atom_channel(resp.text)
        with db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO channels (title, xml_url, html_url) "
                "VALUES (?, ?, ?)",
                (title, rss_url, html_url),
            )
            conn.commit()
        print(f"Imported channel: {title} ({rss_url})")
    except Exception as e:
        print(f"Error importing {rss_url}: {e}")


def fetch_all_feeds(proxy=None, all_channels=False):
    with db_connection() as conn:
        c = conn.cursor()
        if all_channels:
            c.execute("SELECT id, xml_url FROM channels")
        else:
            c.execute("""
                SELECT DISTINCT c.id, c.xml_url
                FROM channels c
                INNER JOIN videos v ON c.id = v.channel_id
                WHERE v.pub_date >= datetime('now', '-30 days')
            """)
        channels = c.fetchall()
        total_videos = 0
        for channel in channels:
            channel_id = channel["id"]
            xml_url = channel["xml_url"]
            print(f"Fetching {xml_url}...")
            items = fetch_feed(xml_url, proxy)
            for item in items:
                try:
                    c.execute(
                        """
                        INSERT OR IGNORE INTO videos
                        (channel_id, title, link, description,
                         pub_date, guid, status, shorts)
                        VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
                    """,
                        (
                            channel_id,
                            item["title"],
                            item["link"],
                            item["description"],
                            item["pub_date"],
                            item["guid"],
                            item.get("shorts", 0),
                        ),
                    )
                    if c.rowcount:
                        total_videos += 1
                except sqlite3.Error as e:
                    print(f"Error inserting video {item['guid']}: {e}")
        conn.commit()
    print(f"Fetched {total_videos} new videos")


def list_videos(status=None, limit=None):
    with db_connection() as conn:
        c = conn.cursor()
        query = """
            SELECT videos.*, channels.title as channel_title
            FROM videos
            LEFT JOIN channels ON videos.channel_id = channels.id
        """
        params = ()
        if status:
            query += " WHERE videos.status = ?"
            params = (status,)
        query += " ORDER BY videos.pub_date DESC"
        if limit:
            query += " LIMIT ?"
            params = params + (limit,)
        c.execute(query, params)
        videos = c.fetchall()
        for v in videos:
            print(f"GUID: {v['guid']}")
            print(f"Title: {v['title']}")
            print(f"Channel: {v['channel_title']}")
            print(f"Link: {v['link']}")
            print(f"Status: {v['status']}")
            print(f"Shorts: {bool(v['shorts'])}")
            print(f"Published: {v['pub_date']}")
            print("-" * 80)


def update_status(guid, status):
    if status not in VALID_STATUSES:
        print(f"Invalid status {status}. Valid: {VALID_STATUSES}")
        return
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE videos SET status = ? WHERE guid = ?", (status, guid))
        if c.rowcount == 0:
            print(f"Video with GUID {guid} not found")
        else:
            print(f"Updated status of {guid} to {status}")
        conn.commit()


def show_stats():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM channels")
        total_channels = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM videos")
        total_videos = c.fetchone()[0]
        c.execute("SELECT status, COUNT(*) FROM videos GROUP BY status")
        status_counts = c.fetchall()
        print(f"Total channels: {total_channels}")
        print(f"Total videos: {total_videos}")
        print("Status counts:")
        for row in status_counts:
            print(f"  {row[0]}: {row[1]}")


def show_channel_stats():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT
                c.title,
                COUNT(v.id) as total_videos,
                SUM(CASE WHEN v.status = 'new' THEN 1 ELSE 0 END)
                    as new_count,
                SUM(CASE WHEN v.status = 'not_interested' THEN 1 ELSE 0 END)
                    as not_interested_count,
                SUM(CASE WHEN v.status = 'viewed' THEN 1 ELSE 0 END)
                    as viewed_count,
                SUM(CASE WHEN v.status = 'todo' THEN 1 ELSE 0 END)
                    as todo_count,
                MAX(v.pub_date) as last_video_date
            FROM channels c
            LEFT JOIN videos v ON c.id = v.channel_id
            GROUP BY c.id, c.title
            ORDER BY last_video_date DESC
        """)
        channels = c.fetchall()
        if not channels:
            print("No channels found")
            return
        for ch in channels:
            print(f"Channel: {ch['title']}")
            print(
                f"  Total: {ch['total_videos']}, "
                f"new={ch['new_count']}, "
                f"not_interested={ch['not_interested_count']}, "
                f"viewed={ch['viewed_count']}, "
                f"todo={ch['todo_count']}"
            )
            print(f"  Last: {ch['last_video_date']}")
            print()


def extract_video_id(url_or_id):
    url_or_id = url_or_id.strip()
    if url_or_id.startswith("yt:video:"):
        return url_or_id.split(":", 2)[2]
    parsed = urlparse(url_or_id)
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/")
    if "youtube" in (parsed.netloc or ""):
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[-1]
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    return url_or_id


def mark_viewed_from_stdin():
    with db_connection() as conn:
        c = conn.cursor()
        updated = 0
        for line in sys.stdin:
            video_id = extract_video_id(line)
            if not video_id:
                continue
            guid = f"yt:video:{video_id}"
            c.execute("UPDATE videos SET status = 'viewed' WHERE guid = ?", (guid,))
            if c.rowcount:
                updated += 1
        conn.commit()
    print(f"Updated {updated} videos to viewed")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube OPML Feed Manager with SQLite"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("init", help="Initialize database")
    import_parser = subparsers.add_parser("import-opml", help="Import OPML file")
    import_parser.add_argument("opml_file", help="Path to OPML file")
    import_url_parser = subparsers.add_parser("import-url", help="Import RSS/Atom URL")
    import_url_parser.add_argument("url", help="RSS/Atom feed URL")
    import_url_parser.add_argument(
        "--proxy",
        default=None,
        help="HTTP proxy (default: no proxy)",
    )
    fetch_parser = subparsers.add_parser("fetch", help="Fetch feeds from channels")
    fetch_parser.add_argument(
        "--proxy",
        default="http://127.0.0.1:8881",
        help="HTTP proxy (default: http://127.0.0.1:8881)",
    )
    fetch_parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Fetch from all channels "
            "(default: only channels with videos in last 30 days)"
        ),
    )
    list_parser = subparsers.add_parser("list", help="List videos")
    list_parser.add_argument(
        "--status", help="Filter by status (new, not_interested, viewed, todo)"
    )
    list_parser.add_argument("--limit", type=int, help="Limit number of results")
    update_parser = subparsers.add_parser("update-status", help="Update video status")
    update_parser.add_argument("--guid", required=True, help="Video GUID")
    update_parser.add_argument("--status", required=True, help="New status")
    subparsers.add_parser("stats", help="Show statistics")
    subparsers.add_parser("channel-stats", help="Show per-channel statistics")
    subparsers.add_parser("mark-viewed", help="Mark videos as viewed from stdin URLs")

    args = parser.parse_args()

    if args.command == "init":
        init_db()
        print(f"Initialized database {DB_FILE}")
    elif args.command == "import-opml":
        import_opml(args.opml_file)
    elif args.command == "import-url":
        import_url(args.url, args.proxy)
    elif args.command == "fetch":
        fetch_all_feeds(args.proxy, args.all)
    elif args.command == "list":
        list_videos(args.status, args.limit)
    elif args.command == "update-status":
        update_status(args.guid, args.status)
    elif args.command == "stats":
        show_stats()
    elif args.command == "channel-stats":
        show_channel_stats()
    elif args.command == "mark-viewed":
        mark_viewed_from_stdin()
    else:
        parser.print_help()


if __name__ == "__main__":
    import signal

    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
