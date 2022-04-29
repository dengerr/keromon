import datetime

import requests
from bs4 import BeautifulSoup

import rss


url = "https://снми.рф/"
title = "Средство НеМассовой Информации"
description = ('Проект предназначен не для тех, кому нужен "ещё один '
'источник информации", он предназначен для тех, кому хочется '
'поставить на входящий информационный поток максимально жестокий '
'(в меру патриотичный, не в меру циничный, и крайне опытный) '
'фильтр/файрвол.')


def prepare(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_content(soup):
    content = soup.body.find("div", class_="paper__content")
    # print(dir(content))
    title = ""
    description = []
    for tag in content.children:
        # print(type(tag), dir(tag))
        if tag.name == "h2":
            if title:
                yield {"title": title,
                       "description": "".join(description)}
            title = tag.text
            description = []
        elif hasattr(tag, 'decode_contents'):
            description.append(tag.decode_contents())
        else:
            if str(tag).strip() == "None":
                continue
            if tag.name:
                description.append(f"<{tag.name}>{tag}</{tag.name}>")
            else:
                description.append(f"<p>{tag}</p>")
    yield {"title": title, "description": "".join(description)}


if __name__ == "__main__":
    current = datetime.datetime.now()
    current_date = current.strftime("%Y-%m-%d")

    channel = dict(
        title=title,
        link=url,
        description=description,
        language="ru",
    )

    soup = prepare(url)
    date = soup.body.find("div", class_="paper__date").text
    content = get_content(soup)

    items = [dict(
        title=item['title'],
        link=url,
        description=item['description'],
        pubDate=current,
        guid=date + str(i),
    ) for i, item in enumerate(get_content(soup))]

    rss.print_rss2(channel, items)
