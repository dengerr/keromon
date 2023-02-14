MD_BODY_TEMPLATE = """\
- [ ] {voting} [{text}]({url})\
"""
HTML_BODY_TEMPLATE = """\
- [ ] {voting} <a href="{url}">{text}</a>\
"""


def md_task_format(article: dict) -> str:
    return MD_BODY_TEMPLATE.format(**article)


def html_row_format(article: dict) -> str:
    return HTML_BODY_TEMPLATE.format(**article)
