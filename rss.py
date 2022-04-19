import datetime


def print_rss2(channel, items):
    current = datetime.datetime.now()
    channel = channel.copy()
    channel.update(
        pubDate=current,
        lastBuildDate=current,
        # docs="http://blogs.law.harvard.edu/tech/rss",
        # generator="Weblog Editor 2.0",
        # managingEditor="editor@example.com",
        # webMaster="webmaster@example.com",
    )
    print('<?xml version="1.0"?>')
    print('<rss version="2.0">')
    print("  <channel>")
    for k, v in channel.items():
        print(f"    <{k}>{prepare(v)}</{k}>")
    for item in items:
        print("    <item>")
        for k, v in item.items():
            print(f"      <{k}>{prepare(v)}</{k}>")
        print("    </item>")
    print("  </channel>")
    print("</rss>")


def prepare(value):
    if isinstance(value, datetime.datetime):
        return _date(value)
    else:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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


