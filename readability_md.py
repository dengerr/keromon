#!/bin/python3
"""
get text (article) from a html text and convert to markdown
"""
import os.path
import argparse

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

parser = argparse.ArgumentParser()
parser.add_argument('--save', type=bool, default=False)
parser.add_argument('url', nargs='?')
args = parser.parse_args()
print(args)


def get_url() -> str:
    url = args.url or 'https://habr.com/ru/post/499168/'
    return url


def get_filename(url) -> str:
    return url.rstrip('/').split('/')[-1]


def main():
    url = get_url()
    filename = get_filename(url)
    if not os.path.exists(f'{filename}.html'):
        save_file(url, f'{filename}.html')
    with open(f'{filename}.html') as html_file:
        soup = BeautifulSoup(html_file.read(), "lxml")
        article_tag = get_article_tag(soup)
    filename_md = f'{filename}.md'
    save_to_markdown(url, article_tag, filename_md)


def save_file(url, filename):
    response = requests.get(url)
    with open(filename, 'w') as output:
        output.write(response.text)


def get_article_tag(soup):
    return soup.find("article")


def save_to_markdown(url, soup, filename):
    text_md = ImageBlockConverter().convert_soup(soup)
    with open(filename, 'w') as output:
        output.write(f"Original: {url}\n\n")
        output.write(text_md)


class ImageBlockConverter(MarkdownConverter):
    def convert_img(self, el, text, convert_as_inline):
        return super().convert_img(el, text, convert_as_inline) + '\n\n'

    def convert_hr(self, el, text, convert_as_inline):
        return '\n\n----\n\n'

    # def convert_div(self, el, text, convert_as_inline):
    #     text = text.strip()
    #     if convert_as_inline:
    #         # print(text)
    #         return text
    #     print(text)
    #     return '%s\n\n' % text if text else ''

    def convert_hn(self, n, el, text, convert_as_inline):
        md = super().convert_hn(n, el, text, convert_as_inline)
        md = '\n\n' + md.lstrip()
        return md


def main2(**options):
    url = get_url()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    article = soup.find("article")
    text_md = ImageBlockConverter(**options).convert_soup(article)
    print(url, '\n')
    print(text_md)


if __name__ == "__main__":
    if args.save:
        main()
    else:
        main2()
