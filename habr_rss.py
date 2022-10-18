import datetime

import rss
from scrap import get_habr_articles


BODY_TEMPLATE = """\
- [ ] {voting} <a href="{url}">{text}</a>\
"""

ALL_IN_ONE_POST = False
ARTICLES_COUNT_IN_ONE_POST = 5


def texts_generator(texts):
    i = 0
    while (i * ARTICLES_COUNT_IN_ONE_POST) < len(texts):
        i1 = i * ARTICLES_COUNT_IN_ONE_POST
        i2 = (i + 1) * ARTICLES_COUNT_IN_ONE_POST
        yield texts[i1:i2]
        i += 1


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
    )

    texts = [
        BODY_TEMPLATE.format(**article)
        for url in urls
        for article in get_habr_articles(url)
    ]

    items = []
    if ALL_IN_ONE_POST:
        body = "<br/>\n".join(texts)
        items.append(dict(
            title=f"Weekly HABR {current_date}",
            link=urls[0],
            description=body,
            pubDate=current,
            guid=current_date,
        ))
    else:
        for i, mini_texts in enumerate(texts_generator(texts)):
            body = "<br/>\n".join(mini_texts)
            if body:
                items.append(dict(
                    title=f"Weekly HABR {current_date}",
                    link=urls[0],
                    description=body,
                    pubDate=current,
                    guid=current_date + f'-{i}',
                ))

    rss.print_rss2(channel, items)
