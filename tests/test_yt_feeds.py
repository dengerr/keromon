from datetime import datetime

import pytest
import requests

from yt_feeds import ensure_proxy_support, get_session, parse_atom_feed


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


def test_get_session_http_proxy():
    session = get_session("http://127.0.0.1:8881")
    assert session.proxies == {
        "http": "http://127.0.0.1:8881",
        "https": "http://127.0.0.1:8881",
    }


def test_get_session_socks5_proxy():
    proxy = "socks5://127.0.0.1:1080"
    session = get_session(proxy)
    assert session.proxies == {"http": proxy, "https": proxy}


def test_get_session_socks5h_proxy():
    proxy = "socks5h://user:pass@127.0.0.1:1080"
    session = get_session(proxy)
    assert session.proxies == {"http": proxy, "https": proxy}


def test_get_session_without_proxy():
    assert get_session().proxies == {}


def test_ensure_proxy_support_ignores_http(monkeypatch):
    monkeypatch.setattr("yt_feeds.importlib.util.find_spec", lambda name: None)
    ensure_proxy_support("http://127.0.0.1:8881")
    ensure_proxy_support("https://127.0.0.1:8881")


def test_ensure_proxy_support_missing_pysocks(monkeypatch):
    monkeypatch.setattr("yt_feeds.importlib.util.find_spec", lambda name: None)
    with pytest.raises(requests.exceptions.InvalidSchema, match="PySocks"):
        ensure_proxy_support("socks5://127.0.0.1:1080")


def test_get_session_socks_proxy_without_pysocks(monkeypatch):
    monkeypatch.setattr("yt_feeds.importlib.util.find_spec", lambda name: None)
    with pytest.raises(requests.exceptions.InvalidSchema, match="PySocks"):
        get_session("socks5://127.0.0.1:1080")
