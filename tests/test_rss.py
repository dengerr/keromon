from datetime import datetime

from rss import _date, prepare


def test_prepare_with_string():
    result = prepare("hello & world <test> goodbye")
    assert result == "hello &amp; world &lt;test&gt; goodbye"


def test_prepare_with_datetime():
    dt = datetime(2024, 1, 15, 12, 30, 45)
    result = prepare(dt)
    assert result == "Mon, 15 Jan 2024 12:30:45 GMT"


def test_prepare_with_none_datetime():
    result = prepare(None)
    assert result is None


def test_date_with_valid_datetime():
    dt = datetime(2024, 6, 5, 9, 0, 0)
    result = _date(dt)
    assert result == "Wed, 05 Jun 2024 09:00:00 GMT"


def test_date_with_none():
    result = _date(None)
    assert result is None
