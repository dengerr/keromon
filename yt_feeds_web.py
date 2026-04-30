import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request

app = Flask(__name__)


def adapt_datetime(val):
    return val.isoformat()


def convert_datetime(val):
    val_str = val.decode("utf-8")
    # Handle ISO format with Z or +00:00
    val_str = val_str.replace("Z", "+00:00")
    return datetime.fromisoformat(val_str)


sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)

CONFIG_FILE = Path(__file__).parent / "yt_feeds_config.json"

if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        config = json.load(f)
else:
    config = {
        "viewed_file": "viewed_urls.txt",
        "db_file": "feeds.db",
        "proxy": "http://127.0.0.1:8881",
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

VIEWED_FILE = config.get("viewed_file", "viewed_urls.txt")
DB_FILE = config.get("db_file", "feeds.db")


def get_db():
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    status_filter = request.args.get("status", "new")

    conn = get_db()
    c = conn.cursor()

    if status_filter and status_filter != "all":
        c.execute("""
            SELECT videos.*, channels.title as channel_title
            FROM videos
            LEFT JOIN channels ON videos.channel_id = channels.id
            WHERE videos.status = ?
            ORDER BY videos.pub_date DESC
            LIMIT 20
        """, (status_filter,))
    else:
        c.execute("""
            SELECT videos.*, channels.title as channel_title
            FROM videos
            LEFT JOIN channels ON videos.channel_id = channels.id
            ORDER BY videos.pub_date DESC
            LIMIT 20
        """)

    videos = c.fetchall()
    conn.close()

    videos_data = []
    for v in videos:
        videos_data.append(
            {
                "guid": v["guid"],
                "title": v["title"],
                "channel_title": v["channel_title"],
                "link": v["link"],
                "status": v["status"],
                "shorts": bool(v["shorts"]),
                "pub_date": str(v["pub_date"]),
            }
        )

    regular_videos = [v for v in videos_data if not v["shorts"]]
    shorts_videos = [v for v in videos_data if v["shorts"]]

    html_template = """
<!DOCTYPE html>
<html>
<head>
<title>YT Feeds</title>
<meta charset="utf-8">
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
<style>
body {
    font-family: monospace;
    margin: 20px;
    background: #1a1a1a;
    color: #e0e0e0;
}
.video {
    border: 1px solid #444;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 5px;
    background: #2a2a2a;
}
.video.new { border-left: 4px solid #4CAF50; }
.video.not_interested { border-left: 4px solid #f44336; }
.video.viewed { border-left: 4px solid #2196F3; }
.video.todo { border-left: 4px solid #FF9800; }
.title {
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 5px;
}
.meta {
    font-size: 12px;
    color: #999;
    margin-bottom: 10px;
}
.buttons { margin-top: 10px; }
button {
    padding: 8px 16px;
    margin-right: 10px;
    border: none;
    border-radius: 3px;
    cursor: pointer;
    font-size: 14px;
}
.btn-not-interested { background: #f44336; color: white; }
.btn-viewed { background: #2196F3; color: white; }
.btn-todo { background: #FF9800; color: white; }
button:hover { opacity: 0.8; }
.status {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 12px;
    margin-left: 10px;
}
.status.new { background: #4CAF50; color: white; }
.status.not_interested { background: #f44336; color: white; }
.status.viewed { background: #2196F3; color: white; }
.status.todo { background: #FF9800; color: white; }
a { color: #64B5F6; text-decoration: none; }
a:hover { text-decoration: underline; }
.filters {
    margin-bottom: 20px;
    font-size: 14px;
}
.filters a {
    margin-right: 10px;
    padding: 5px 10px;
    border-radius: 3px;
}
.filters a.active {
    background: #2196F3;
    color: white;
    font-weight: bold;
}
.container {
    display: flex;
    gap: 20px;
}
.column {
    flex: 1;
}
.column h2 {
    font-size: 18px;
    margin-bottom: 15px;
    color: #aaa;
}
@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }
}
</style>
</head>
<body>
<h1>YT Feeds - Recent Videos</h1>
<div class="filters">
    <a href="/?status=all"
        class="{% if status_filter == 'all' %}active{% endif %}">
        Все
    </a> |
    <a href="/?status=new"
        class="{% if status_filter == 'new' or not status_filter %}active{% endif %}">
        New
    </a> |
    <a href="/?status=not_interested"
        class="{% if status_filter == 'not_interested' %}active{% endif %}">
        Не смотреть
    </a> |
    <a href="/?status=viewed"
        class="{% if status_filter == 'viewed' %}active{% endif %}">
        Посмотрел
    </a> |
    <a href="/?status=todo"
        class="{% if status_filter == 'todo' %}active{% endif %}">
        Отложить
    </a>
</div>
<div class="container">
    <div class="column">
        <h2>Videos</h2>
        {% for v in regular_videos %}
        <div class="video {{ v.status }}">
            <div class="title">
                <a href="{{ v.link }}" target="_blank">{{ v.title }}</a>
            </div>
            <div class="meta">
                Channel: {{ v.channel_title }} |
                Published: {{ v.pub_date }}
                <span class="status {{ v.status }}">{{ v.status }}</span>
            </div>
        <div class="buttons">
            <button class="btn-not-interested"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "not_interested"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                не смотреть
            </button>
            <button class="btn-viewed"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "viewed"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                посмотреть
            </button>
            <button class="btn-todo"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "todo"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                отложить
            </button>
        </div>
    </div>
    {% endfor %}
</div>
<div class="column">
    <h2>Shorts</h2>
    {% for v in shorts_videos %}
    <div class="video {{ v.status }}">
        <div class="title">
            <a href="{{ v.link }}" target="_blank">{{ v.title }}</a>
        </div>
        <div class="meta">
            Channel: {{ v.channel_title }} |
            Published: {{ v.pub_date }}
            <span class="status {{ v.status }}">{{ v.status }}</span>
        </div>
        <div class="buttons">
            <button class="btn-not-interested"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "not_interested"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                не смотреть
            </button>
            <button class="btn-viewed"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "viewed"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                посмотреть
            </button>
            <button class="btn-todo"
                hx-post="/api/update-status"
                hx-vals='{"guid": "{{ v.guid }}", "status": "todo"}'
                hx-target="closest .video"
                hx-swap="outerHTML swap:0.1s">
                отложить
            </button>
        </div>
    </div>
    {% endfor %}
    </div>
</div>

</body>
</html>
"""

    return render_template_string(
        html_template,
        regular_videos=regular_videos,
        shorts_videos=shorts_videos,
        status_filter=status_filter,
    )


@app.route("/api/update-status", methods=["POST"])
def api_update_status():
    guid = request.form.get("guid") or request.json.get("guid")
    status = request.form.get("status") or request.json.get("status")

    valid_statuses = ["new", "not_interested", "viewed", "todo"]
    if status not in valid_statuses:
        return "Invalid status", 400

    conn = get_db()
    c = conn.cursor()

    if status == "viewed":
        c.execute("SELECT link FROM videos WHERE guid = ?", (guid,))
        row = c.fetchone()
        if row:
            with open(VIEWED_FILE, "a") as f:
                f.write(row["link"] + "\n")

    c.execute("UPDATE videos SET status = ? WHERE guid = ?", (status, guid))
    conn.commit()
    conn.close()

    return "", 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
