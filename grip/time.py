import datetime
import dateutil.parser


def now_tz() -> datetime.datetime:
    return datetime.datetime.now().astimezone()


def date_to_str(date: datetime.date | datetime.datetime) -> str:
    return date.strftime("%Y-%m-%d")


def parse_iso_date(string: str) -> datetime.date:
    if len(string) == 7:
        string = string + "-01"
    return datetime.datetime.strptime(string, "%Y-%m-%d").date()


def parse_iso_datetime(string: str) -> datetime.datetime:
    if len(string) == 7:
        string = string + "-01"
    return dateutil.parser.isoparse(string).astimezone()
