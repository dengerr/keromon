import rss
import extract
import habr_processor
import load


if __name__ == "__main__":
    processor = habr_processor.WeeklyHabrProcessor()

    articles = [
        article
        for url in processor.urls
        for article in extract.get_habr_articles(url)
    ]
    texts = [load.html_row_format(article) for article in articles]

    channel = dict(
        title="Weekly HABR articles",
        link=processor.urls[0],
        description="Weekly HABR articles for copypaste to markdown editor",
        language="ru",
    )
    title = f"Weekly HABR {processor.current_date}"
    printer = rss.GroupedRssPrint(channel, processor, title)
    printer(texts)
