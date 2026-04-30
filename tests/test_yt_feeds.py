from datetime import datetime

from yt_feeds import parse_atom_feed


def test_parse_atom_feed_basic():
    atom_xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Test Video</title>
    <link rel="alternate" href="https://youtube.com/watch?v=123"/>
    <summary>Video description</summary>
    <published>2024-01-15T12:00:00Z</published>
    <id>yt:video:123</id>
  </entry>
</feed>"""
    items = parse_atom_feed(atom_xml)
    assert len(items) == 1
    assert items[0]["title"] == "Test Video"
    assert items[0]["link"] == "https://youtube.com/watch?v=123"
    assert isinstance(items[0]["pub_date"], datetime)
    assert items[0]["guid"] == "yt:video:123"
    assert items[0]["shorts"] == 0


def test_parse_atom_feed_shorts():
    atom_xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Short Video</title>
    <link rel="alternate" href="https://youtube.com/shorts/abc"/>
    <published>2024-01-15T12:00:00Z</published>
    <id>yt:video:abc</id>
  </entry>
</feed>"""
    items = parse_atom_feed(atom_xml)
    assert items[0]["shorts"] == 1


def test_parse_atom_feed_empty():
    atom_xml = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""
    items = parse_atom_feed(atom_xml)
    assert len(items) == 0
