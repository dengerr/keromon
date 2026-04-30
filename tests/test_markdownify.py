from markdownify import chomp, escape


def test_escape_with_underscores():
    result = escape("hello_world_test", True)
    assert result == "hello\\_world\\_test"


def test_escape_without_underscores():
    result = escape("hello_world", False)
    assert result == "hello_world"


def test_escape_with_none():
    result = escape(None, True)
    assert result == ""


def test_escape_with_empty_string():
    result = escape("", True)
    assert result == ""


def test_chomp_with_spaces():
    prefix, suffix, text = chomp("  hello world  ")
    assert prefix == " "
    assert suffix == " "
    assert text == "hello world"


def test_chomp_with_only_leading_spaces():
    prefix, suffix, text = chomp("  hello")
    assert prefix == " "
    assert suffix == ""
    assert text == "hello"
