import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

# Reuse datetime adapters from yt_feeds if available, otherwise define locally
try:
    from yt_feeds import VALID_STATUSES, adapt_datetime, convert_datetime
except ImportError:
    VALID_STATUSES = ["new", "not_interested", "viewed", "todo"]

    def adapt_datetime(val):
        return val.isoformat()

    def convert_datetime(val):
        val_str = val.decode("utf-8")
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
DELETED_FILE = "deleted.txt"


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


def video_card_html(v):
    """Generate HTML for a video card."""
    return f"""
<div class="video {v["status"]}">
    <div class="title">
        {v["channel_title"]} <br>
        <a href="{v["link"]}" target="_blank">{v["title"]}</a>
    </div>
    <div class="meta">
        Published: {v["pub_date"]}
        <span class="status {v["status"]}">{v["status"]}</span>
    </div>
    <div class="buttons">
        <button class="btn-not-interested"
            hx-post="/api/update-status"
            hx-vals='{{"guid": "{v["guid"]}", "status": "not_interested"}}'
            hx-target="closest .video"
            hx-swap="outerHTML swap:0.1s">
            не смотреть
        </button>
        <button class="btn-viewed"
            hx-post="/api/update-status"
            hx-vals='{{"guid": "{v["guid"]}", "status": "viewed"}}'
            hx-target="closest .video"
            hx-swap="outerHTML swap:0.1s">
            посмотреть
        </button>
        <button class="btn-todo"
            hx-post="/api/update-status"
            hx-vals='{{"guid": "{v["guid"]}", "status": "todo"}}'
            hx-target="closest .video"
            hx-swap="outerHTML swap:0.1s">
            отложить
        </button>
    </div>
</div>
"""


@app.route("/")
def index():
    status_filter = request.args.get("status", "new")

    with db_connection() as conn:
        c = conn.cursor()

        def query_videos(shorts_val):
            if status_filter and status_filter != "all":
                c.execute(
                    """
                    SELECT videos.*, channels.title as channel_title
                    FROM videos
                    LEFT JOIN channels ON videos.channel_id = channels.id
                    WHERE videos.status = ? AND videos.shorts = ?
                    AND videos.pub_date >= date('now', '-1 year')
                    ORDER BY videos.pub_date DESC
                    LIMIT 20
                """,
                    (status_filter, shorts_val),
                )
            else:
                c.execute(
                    """
                    SELECT videos.*, channels.title as channel_title
                    FROM videos
                    LEFT JOIN channels ON videos.channel_id = channels.id
                    WHERE videos.shorts = ?
                    AND videos.pub_date >= date('now', '-1 year')
                    ORDER BY videos.pub_date DESC
                    LIMIT 20
                """,
                    (shorts_val,),
                )
            return c.fetchall()

        regular_videos_raw = query_videos(0)
        shorts_videos_raw = query_videos(1)

    def build_video_data(videos):
        result = []
        for v in videos:
            video_dict = {
                "guid": v["guid"],
                "title": v["title"],
                "channel_title": v["channel_title"],
                "link": v["link"],
                "status": v["status"],
                "shorts": bool(v["shorts"]),
                "pub_date": str(v["pub_date"]),
            }
            video_dict["html"] = video_card_html(video_dict)
            result.append(video_dict)
        return result

    videos_data = build_video_data(regular_videos_raw + shorts_videos_raw)
    regular_videos = [v for v in videos_data if not v["shorts"]]
    shorts_videos = [v for v in videos_data if v["shorts"]]

    return render_template(
        "yt_feeds_template.html",
        regular_videos=regular_videos,
        shorts_videos=shorts_videos,
        status_filter=status_filter,
    )


@app.route("/api/update-status", methods=["POST"])
def api_update_status():
    guid = request.form.get("guid") or request.json.get("guid")
    status = request.form.get("status") or request.json.get("status")

    if status not in VALID_STATUSES:
        return "Invalid status", 400

    with db_connection() as conn:
        c = conn.cursor()
        if status == "viewed":
            c.execute("SELECT link FROM videos WHERE guid = ?", (guid,))
            row = c.fetchone()
            if row:
                with open(VIEWED_FILE, "a") as f:
                    f.write(row["link"] + "\n")

        c.execute("UPDATE videos SET status = ? WHERE guid = ?", (status, guid))
        conn.commit()

    return "", 200


@app.route("/channels")
def channels():
    with db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id, title FROM channels ORDER BY title")
        all_channels = c.fetchall()

    return render_template(
        "yt_channels_template.html",
        channels=all_channels,
        active_channel_id=None,
    )


@app.route("/api/channel/<int:channel_id>/videos")
def channel_videos(channel_id):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT videos.*, channels.title as channel_title
            FROM videos
            LEFT JOIN channels ON videos.channel_id = channels.id
            WHERE videos.channel_id = ?
            ORDER BY videos.pub_date DESC
        """,
            (channel_id,),
        )
        videos = c.fetchall()

    videos_data = []
    for v in videos:
        video_dict = {
            "guid": v["guid"],
            "title": v["title"],
            "channel_title": v["channel_title"],
            "link": v["link"],
            "status": v["status"],
            "shorts": bool(v["shorts"]),
            "pub_date": str(v["pub_date"]),
        }
        video_dict["html"] = video_card_html(video_dict)
        videos_data.append(video_dict)

    regular_videos = [v for v in videos_data if not v["shorts"]]
    shorts_videos = [v for v in videos_data if v["shorts"]]

    html = '<div class="container">'
    html += '<div class="column"><h2>Videos</h2>'
    for v in regular_videos:
        html += v["html"]
    html += "</div>"
    html += '<div class="column"><h2>Shorts</h2>'
    for v in shorts_videos:
        html += v["html"]
    html += "</div></div>"

    return html


@app.route("/api/channel/<int:channel_id>/mark-viewed", methods=["POST"])
def api_channel_mark_viewed(channel_id):
    with db_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT link FROM videos WHERE channel_id = ? AND status = 'new'",
            (channel_id,),
        )
        c.execute(
            "UPDATE videos SET status = 'viewed'"
            " WHERE channel_id = ? AND status = 'new'",
            (channel_id,),
        )
        conn.commit()
    return "", 200


@app.route("/api/channel/<int:channel_id>", methods=["DELETE"])
def api_delete_channel(channel_id):
    with db_connection() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        channel = c.fetchone()
        if not channel:
            return "Channel not found", 404

        c.execute("SELECT * FROM videos WHERE channel_id = ?", (channel_id,))
        videos = c.fetchall()

        with open(DELETED_FILE, "a") as f:
            f.write(
                json.dumps({"type": "channel", **dict(channel)}, default=str) + "\n"
            )
            for v in videos:
                f.write(json.dumps({"type": "video", **dict(v)}, default=str) + "\n")

        c.execute("DELETE FROM videos WHERE channel_id = ?", (channel_id,))
        c.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        conn.commit()

    return "", 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
