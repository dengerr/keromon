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


def get_content(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.body.find("div", class_="paper__title").text
    content = soup.body.find("div", class_="paper__content").decode_contents()
    return title, content


if __name__ == "__main__":
    current = datetime.datetime.now()
    current_date = current.strftime("%Y-%m-%d")

    channel = dict(
        title=title,
        link=url,
        description=description,
        language="ru",
    )

    title, content = get_content(url)

    item = dict(
        title=title,
        link=url,
        description=content,
        pubDate=current,
        guid=current_date,
    )
    rss.print_rss2(channel, [item])
