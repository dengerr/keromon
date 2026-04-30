import argparse
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import html

ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
DB_FILE = 'feeds.db'

def adapt_datetime(val):
    return val.isoformat()

def convert_datetime(val):
    return datetime.fromisoformat(val.decode('utf-8'))

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter('TIMESTAMP', convert_datetime)

def get_db():
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            xml_url TEXT UNIQUE NOT NULL,
            html_url TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            description TEXT,
            pub_date TIMESTAMP,
            guid TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (channel_id) REFERENCES channels(id)
        )
    ''')
    conn.commit()
    conn.close()

def parse_atom_feed(content):
    root = ET.fromstring(content)
    entries = root.findall('atom:entry', ATOM_NS)
    items = []
    for entry in entries:
        title = entry.find('atom:title', ATOM_NS).text
        link = ''
        for link_elem in entry.findall('atom:link', ATOM_NS):
            if link_elem.get('rel') == 'alternate' and link_elem.get('href') is not None:
                link = link_elem.get('href')
                break
        desc_elem = entry.find('atom:summary', ATOM_NS) or entry.find('atom:content', ATOM_NS)
        description = html.unescape(desc_elem.text) if desc_elem is not None and desc_elem.text else ''
        pub_date_str = entry.find('atom:published', ATOM_NS).text
        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')) if pub_date_str else None
        guid = entry.find('atom:id', ATOM_NS).text
        items.append({
            'title': title,
            'link': link,
            'description': description,
            'pub_date': pub_date,
            'guid': guid,
        })
    return items

def get_session(proxy=None):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    return session

def fetch_feed(url, proxy=None):
    try:
        session = get_session(proxy)
        resp = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        resp.raise_for_status()
        return parse_atom_feed(resp.text)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return []

def import_opml(opml_path):
    conn = get_db()
    c = conn.cursor()
    tree = ET.parse(opml_path)
    root = tree.getroot()
    outlines = root.findall('.//outline[@type="rss"]')
    for outline in outlines:
        title = outline.get('title') or outline.get('text')
        xml_url = outline.get('xmlUrl')
        html_url = outline.get('htmlUrl')
        if not xml_url:
            continue
        c.execute('''
            INSERT OR IGNORE INTO channels (title, xml_url, html_url)
            VALUES (?, ?, ?)
        ''', (title, xml_url, html_url))
    conn.commit()
    conn.close()
    print(f"Imported {len(outlines)} channels from {opml_path}")

def fetch_all_feeds(proxy=None):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, xml_url FROM channels')
    channels = c.fetchall()
    total_videos = 0
    for channel in channels:
        channel_id = channel['id']
        xml_url = channel['xml_url']
        print(f"Fetching {xml_url}...")
        items = fetch_feed(xml_url, proxy)
        for item in items:
            try:
                c.execute('''
                    INSERT OR IGNORE INTO videos (channel_id, title, link, description, pub_date, guid, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'new')
                ''', (channel_id, item['title'], item['link'], item['description'], item['pub_date'], item['guid']))
                if c.lastrowid:
                    total_videos += 1
            except sqlite3.Error as e:
                print(f"Error inserting video {item['guid']}: {e}")
    conn.commit()
    conn.close()
    print(f"Fetched {total_videos} new videos")

def list_videos(status=None, limit=None):
    conn = get_db()
    c = conn.cursor()
    query = '''
        SELECT videos.*, channels.title as channel_title
        FROM videos
        LEFT JOIN channels ON videos.channel_id = channels.id
    '''
    params = ()
    if status:
        query += ' WHERE videos.status = ?'
        params = (status,)
    query += ' ORDER BY videos.pub_date DESC'
    if limit:
        query += ' LIMIT ?'
        params = params + (limit,)
    c.execute(query, params)
    videos = c.fetchall()
    for v in videos:
        print(f"GUID: {v['guid']}")
        print(f"Title: {v['title']}")
        print(f"Channel: {v['channel_title']}")
        print(f"Link: {v['link']}")
        print(f"Status: {v['status']}")
        print(f"Published: {v['pub_date']}")
        print("-" * 80)
    conn.close()

def update_status(guid, status):
    valid_statuses = ['new', 'not_interested', 'viewed', 'todo']
    if status not in valid_statuses:
        print(f"Invalid status {status}. Valid: {valid_statuses}")
        return
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE videos SET status = ? WHERE guid = ?', (status, guid))
    if c.rowcount == 0:
        print(f"Video with GUID {guid} not found")
    else:
        print(f"Updated status of {guid} to {status}")
    conn.commit()
    conn.close()

def show_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM channels')
    total_channels = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM videos')
    total_videos = c.fetchone()[0]
    c.execute('SELECT status, COUNT(*) FROM videos GROUP BY status')
    status_counts = c.fetchall()
    print(f"Total channels: {total_channels}")
    print(f"Total videos: {total_videos}")
    print("Status counts:")
    for row in status_counts:
        print(f"  {row[0]}: {row[1]}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='YouTube OPML Feed Manager with SQLite')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    init_parser = subparsers.add_parser('init', help='Initialize database')
    import_parser = subparsers.add_parser('import-opml', help='Import OPML file')
    import_parser.add_argument('opml_file', help='Path to OPML file')
    fetch_parser = subparsers.add_parser('fetch', help='Fetch feeds from channels')
    fetch_parser.add_argument('--proxy', default='http://127.0.0.1:8881', help='HTTP proxy (default: http://127.0.0.1:8881)')
    list_parser = subparsers.add_parser('list', help='List videos')
    list_parser.add_argument('--status', help='Filter by status (new, not_interested, viewed, todo)')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    update_parser = subparsers.add_parser('update-status', help='Update video status')
    update_parser.add_argument('--guid', required=True, help='Video GUID')
    update_parser.add_argument('--status', required=True, help='New status')
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
        print(f"Initialized database {DB_FILE}")
    elif args.command == 'import-opml':
        import_opml(args.opml_file)
    elif args.command == 'fetch':
        fetch_all_feeds(args.proxy)
    elif args.command == 'list':
        list_videos(args.status, args.limit)
    elif args.command == 'update-status':
        update_status(args.guid, args.status)
    elif args.command == 'stats':
        show_stats()
    else:
        parser.print_help()

if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    main()
