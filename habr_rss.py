import extract
import habr_processor
import rss
import transform


if __name__ == "__main__":
    processor = habr_processor.WeeklyHabrProcessor()

    # extract
    articles = [
        article
        for url in processor.urls
        for article in extract.get_habr_articles(url)
    ]

    # load to rss+html std output
    channel = dict(
        title="Weekly HABR articles",
        link=processor.urls[0],
        description="Weekly HABR articles for copypaste to markdown editor",
        language="ru",
    )
    title = f"Weekly HABR {processor.date_str}"

    printer = rss.GroupedRssPrint(channel, title, processor.current)
    texts = [transform.html_row_format(article) for article in articles]
    printer(texts)
