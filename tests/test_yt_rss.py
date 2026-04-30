from yt_rss import helper_get_from_dict


def test_helper_get_from_dict_with_single_key_dict():
    data = {"content": {"title": "Test"}}
    result = helper_get_from_dict(data)
    assert result == "Test"


def test_helper_get_from_dict_with_list():
    data = [{"item": 1}]
    result = helper_get_from_dict(data)
    assert result == 1


def test_helper_get_from_dict_with_empty_list():
    data = []
    result = helper_get_from_dict(data)
    assert result == []


def test_helper_get_from_dict_with_nested_structure():
    data = {"contents": {"content": {"items": [1, 2, 3]}}}
    result = helper_get_from_dict(data)
    assert result == [1, 2, 3]


def test_helper_get_from_dict_with_fields():
    data = {"other": "value", "title": "Found"}
    result = helper_get_from_dict(data, ["title"])
    assert result == "Found"
