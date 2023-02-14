import datetime


class BaseEtlProcessor():
    def __init__(self):
        self.current = datetime.datetime.now()
        self.date_str = self.current.strftime("%Y-%m-%d")


class WeeklyHabrProcessor(BaseEtlProcessor):
    urls = [
        "https://habr.com/ru/top/weekly/",
        "https://habr.com/ru/top/weekly/page2/",
        "https://habr.com/ru/top/weekly/page3/",
    ]

    @property
    def subject(self):
        return f"New weekly HABR articles {self.date_str}"


class DaylyHabrProcessor(BaseEtlProcessor):
    urls = ["https://habr.com/ru/top/daily/"]

    @property
    def subject(self):
        return f"New HABR articles {self.date_str}"


