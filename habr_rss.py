import datetime

import rss
from scrap import get_habr_articles


BODY_TEMPLATE = """\
- [ ] {voting} <a href="{url}">{text}</a>\
"""


if __name__ == "__main__":
    current = datetime.datetime.now()
    current_date = current.strftime("%Y-%m-%d")

    urls = [
        "https://habr.com/ru/top/weekly/",
        "https://habr.com/ru/top/weekly/page2/",
        "https://habr.com/ru/top/weekly/page3/",
    ]

    channel = dict(
        title="Weekly HABR articles",
        link=urls[0],
        description="Weekly HABR articles for copypaste to markdown editor",
        language="ru",
        pubDate=current,
        lastBuildDate=current,
        # docs="http://blogs.law.harvard.edu/tech/rss",
        # generator="Weblog Editor 2.0",
        # managingEditor="editor@example.com",
        # webMaster="webmaster@example.com",
    )

    texts = [
        BODY_TEMPLATE.format(**article)
        for url in urls
        for article in get_habr_articles(url)
    ]
    body = "<br/>\n".join(texts)

    item = dict(
        title=f"Weekly HABR {current_date}",
        link=urls[0],
        description=body,
        pubDate=current,
        guid=current_date,
    )
    rss.print_rss2(channel, [item])
