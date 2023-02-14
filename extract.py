import requests
from bs4 import BeautifulSoup


def get_habr_articles(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    articles = soup.find_all("article", class_="tm-articles-list__item")
    for article in articles:
        link = article.find("a", class_="tm-article-snippet__title-link")
        if not link:
            continue
        voting = article.find("span", class_="tm-votes-meter__value")
        url = "https://habr.com" + link.get("href")
        yield dict(text=link.text, voting=voting.text, url=url)
