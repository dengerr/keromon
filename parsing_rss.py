import html

from bs4 import BeautifulSoup


def save_from_file(filename):
    # другой вариант - fetch_file()
    content = open(filename).read()
    channel, items = parse_rss(content)
    print(channel)
    print(items)
    save_to_db(channel, items)


def parse_rss(content):
    soup = BeautifulSoup(content, "lxml")
    channel_node = soup.rss.channel
    channel = {
        "title": (str(channel_node.title.string) if channel_node.title else ""),
        "description": (
            str(channel_node.description.string) if channel_node.description else ""
        ),
    }
    items = []
    for item in soup.find_all("item"):
        di = {}
        for attr in "guid pubDate title author link description".split():
            node = getattr(item, attr)
            if node is not None:
                di[attr] = node.string
            else:
                di[attr] = None
        if di["description"]:
            di["description"] = html.unescape(di["description"])
        items.append(di)
    return channel, items


def save_to_db(channel, items): ...


if __name__ == "__main__":
    save_from_file("oleg.rss.xml")
