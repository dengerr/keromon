import datetime
import requests
from collections import namedtuple
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bs4 import BeautifulSoup

smtp_host = 'smtp.gmail.com'
smtp_user = ''
smtp_password = ''
sent_from = smtp_user
to = ['']


def get_habr_articles():
    url = 'https://habr.com/ru/top/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    articles = soup.find_all('article', class_='post')
    for article in articles:
        link = article.find('a', class_='post__title_link')
        voting = article.find('span', class_='post-stats__result-counter')
        yield dict(text=link.text, voting=voting.text, url=link.get('href'))

BODY_TEMPLATE = """\
{voting} {text}
{url}
"""

def send_email(subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sent_from
    msg["To"] = ", ".join(to)
    part1 = MIMEText(body, "plain", "utf-8")
    msg.attach(part1)

    server = smtplib.SMTP_SSL(smtp_host, 465)
    server.ehlo()
    server.login(smtp_user, smtp_password)
    server.sendmail(sent_from, to, msg.as_string())
    server.close()


def send_articles():
    articles = get_habr_articles()
    current = datetime.datetime.now()
    subject = 'New HABR articles {}'.format(current.strftime('%Y-%m-%d'))
    texts = [BODY_TEMPLATE.format(**article) for article in articles]
    body = "\n".join(texts)
    send_email(subject, body)

send_articles()
