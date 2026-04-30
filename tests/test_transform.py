from transform import html_row_format, md_task_format


def test_md_task_format():
    article = {"voting": "+10", "text": "Test Article", "url": "https://example.com"}
    result = md_task_format(article)
    assert result == "- [ ] +10 [Test Article](https://example.com)"


def test_html_row_format():
    article = {"voting": "+5", "text": "Another Article", "url": "https://test.com"}
    result = html_row_format(article)
    assert result == '- [ ] +5 <a href="https://test.com">Another Article</a>'
