from abc import abstractmethod
import datetime


WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def print_rss2(channel, items):
    current = datetime.datetime.now()
    channel = channel.copy()
    channel.update(
        lastBuildDate=current,
        # docs="http://blogs.law.harvard.edu/tech/rss",
        # generator="Weblog Editor 2.0",
        # managingEditor="editor@example.com",
        # webMaster="webmaster@example.com",
    )
    if not channel.get('pubDate'):
        channel['pubDate'] = current

    print('<?xml version="1.0"?>')
    print('<rss version="2.0">')
    print("  <channel>")
    for k, v in channel.items():
        print(f"    <{k}>{prepare(v)}</{k}>")
    for item in items:
        print("    <item>")
        for k, v in item.items():
            print(f"      <{k}>{prepare(v)}</{k}>")
        print("    </item>")
    print("  </channel>")
    print("</rss>")


def prepare(value):
    if isinstance(value, datetime.datetime):
        return _date(value)
    else:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _date(date):
    if date is None:
        return None

    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
        WEEKDAYS[date.weekday()],
        date.day,
        MONTHS[date.month - 1],
        date.year,
        date.hour,
        date.minute,
        date.second,
    )


class RssPrint:
    channel: dict
    processor: 'BaseEtlProcessor'
    title: str

    def __init__(self, channel, processor, title):
        self.channel = channel
        self.processor = processor
        self.title = title

    @property
    def url(self):
        return self.processor.urls[0]

    def __call__(self, texts):
        print_rss2(self.channel, self.get_items(texts))

    @abstractmethod
    def get_items(self, texts):
        pass


class AllInOneRssPrint(RssPrint):
    def get_items(self, texts):
        body = "<br/>\n".join(texts)
        items = [dict(
            title=self.title,
            link=self.url,
            description=body,
            pubDate=self.processor.current,
            guid=self.processor.current_date,
        )]
        return items

class GroupedRssPrint(RssPrint):
    articles_count_in_one_post: int = 5

    def get_items(self, texts):
        items = []
        for i, mini_texts in enumerate(self._texts_generator(texts)):
            body = "<br/>\n".join(mini_texts)
            if body:
                items.append(dict(
                    title=f"{self.title} {i+1}",
                    link=self.url,
                    description=body,
                    pubDate=self.processor.current,
                    guid=self.processor.current_date + f'-{i}',
                ))
        return items

    def _texts_generator(self, texts):
        i = 0
        while (i * self.articles_count_in_one_post) < len(texts):
            i1 = i * self.articles_count_in_one_post
            i2 = (i + 1) * self.articles_count_in_one_post
            yield texts[i1:i2]
            i += 1
