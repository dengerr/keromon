import datetime

from scrap import get_habr_articles


BODY_TEMPLATE = """\
- [ ] {voting} <a href="{url}">{text}</a>\
"""


def print_rss2(channel, items):
    print('<?xml version="1.0"?>')
    print('<rss version="2.0">')
    print("  <channel>")
    for k, v in channel.items():
        print(f"    <{k}>{v}</{k}>")
    for item in items:
        print("    <item>")
        for k, v in item.items():
            print(f"      <{k}>{v}</{k}>")
        print("    </item>")
    print("  </channel>")
    print("</rss>")


def _date(date):
    if date is None:
        return None

    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][date.weekday()],
        date.day,
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ][date.month - 1],
        date.year,
        date.hour,
        date.minute,
        date.second,
    )


if __name__ == "__main__":
    current = datetime.datetime.now()
    current_date = current.strftime("%Y-%m-%d")

    channel = dict(
        title="Weekly HABR articles",
        link="https://habr.com/ru/top/weekly/",
        description="Weekly HABR articles for copypaste to markdown editor",
        language="ru",
        pubDate=_date(current),
        lastBuildDate=_date(current),
        # docs="http://blogs.law.harvard.edu/tech/rss",
        # generator="Weblog Editor 2.0",
        # managingEditor="editor@example.com",
        # webMaster="webmaster@example.com",
    )

    urls = [
        "https://habr.com/ru/top/weekly/",
        "https://habr.com/ru/top/weekly/page2/",
        "https://habr.com/ru/top/weekly/page3/",
    ]

    texts = [
        BODY_TEMPLATE.format(**article)
        for url in urls
        for article in get_habr_articles(url)
    ]
    body = "<br/>\n".join(texts)
    body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    item = dict(
        title=f"Weekly HABR {current_date}",
        link=urls[0],
        description=body,
        pubDate=_date(current),
        guid=current_date,
    )
    print_rss2(channel, [item])
