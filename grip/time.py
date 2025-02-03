import datetime
import dateutil.parser
import pytimeparse.timeparse
from pydantic_core import core_schema


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


class TimeDelta(datetime.timedelta):
    @classmethod
    def validate(cls, value) -> datetime.timedelta:
        try:
            value = float(value)
        except ValueError:
            pass

        if isinstance(value, int) or isinstance(value, float):
            seconds = value
        else:
            seconds = pytimeparse.timeparse.timeparse(value)
            if seconds is None:
                raise ValueError("invalid time delta")

        return datetime.timedelta(seconds=seconds)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        """
        Define the Pydantic core schema for validation.
        """
        return core_schema.no_info_plain_validator_function(cls.validate)
