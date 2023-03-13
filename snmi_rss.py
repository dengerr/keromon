import datetime

import requests
from bs4 import BeautifulSoup

import rss


base_url = "https://снми.рф/"
title = "Средство НеМассовой Информации"
description = ('Проект предназначен не для тех, кому нужен "ещё один '
'источник информации", он предназначен для тех, кому хочется '
'поставить на входящий информационный поток максимально жестокий '
'(в меру патриотичный, не в меру циничный, и крайне опытный) '
'фильтр/файрвол.')


def main():
    current = datetime.datetime.now()

    archive_soup = get_soup(base_url + "архив/")
    first_link = archive_soup.body.find("a", class_="news-list__link")
    url = first_link.attrs["href"]

    channel = dict(
        title=title,
        link=url,
        description=description,
        language="ru",
    )

    soup = get_soup(url)
    date = soup.body.find("div", class_="paper__date").text

    items = [dict(
        title=item['title'],
        link=url,
        description=item['description'],
        pubDate=current,
        guid=date + str(i),
    ) for i, item in enumerate(get_content(soup))]

    rss.print_rss2(channel, items)


def get_soup(url) -> BeautifulSoup:
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_content(soup):
    content = soup.body.find("div", class_="paper__content")
    title = ""
    description = []
    for tag in content.children:
        if tag.name == "h1":
            if title:
                yield {"title": title,
                       "description": "".join(description)}
            title = tag.text
            description = []
        elif hasattr(tag, 'decode_contents'):
            description.append(f"<{tag.name}>{tag.decode_contents()}</{tag.name}>")
        else:
            if str(tag).strip() not in ["None", "\n"]:
                continue
            if tag.name:
                description.append(f"<{tag.name}>{tag}</{tag.name}>")
            else:
                description.append(f"<p>{tag}</p>")
    yield {"title": title, "description": "".join(description)}


if __name__ == "__main__":
    main()
