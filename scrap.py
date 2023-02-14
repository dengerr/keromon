"""
send email with today most rating article from habr

create file email.ini from template email-example.ini
"""

import sys

import habr_processor
import extract
import load
import transform


def main():
    if "weekly" in sys.argv:
        processor = habr_processor.WeeklyHabrProcessor()
    else:
        processor = habr_processor.DaylyHabrProcessor()

    # extract
    articles = [
        article
        for url in processor.urls
        for article in extract.get_habr_articles(url)
    ]

    # load to markdown + email (or std out)
    texts = [transform.md_task_format(article) for article in articles]
    body = "\n".join(texts)

    if "print" in sys.argv:
        print(processor.subject)
        print(body)
    else:
        load.send_email(processor.subject, body)


if __name__ == "__main__":
    main()
