from parsing_rss import parse_rss


def test_parse_rss_basic():
    xml_content = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test Channel</title>
    <description>A test feed</description>
    <item>
      <guid>1</guid>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
      <title>First Item</title>
      <author>test@example.com</author>
      <link>http://example.com/1</link>
      <description>First item description</description>
    </item>
  </channel>
</rss>"""
    channel, items = parse_rss(xml_content)
    assert str(channel["title"]) == "Test Channel"
    assert str(channel["description"]) == "A test feed"
    assert len(items) == 1
    assert items[0]["title"] == "First Item"
    assert items[0]["guid"] == "1"


def test_parse_rss_multiple_items():
    xml_content = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Test</title>
    <description>Test</description>
    <item><title>Item 1</title><guid>1</guid></item>
    <item><title>Item 2</title><guid>2</guid></item>
    <item><title>Item 3</title><guid>3</guid></item>
  </channel>
</rss>"""
    _, items = parse_rss(xml_content)
    assert len(items) == 3
    assert items[0]["title"] == "Item 1"
    assert items[2]["title"] == "Item 3"
