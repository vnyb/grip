import datetime
import os
import pandas as pd
from functools import wraps
from typing import Callable, TypeVar
from . import (
    get_file_staleness,
    read_json,
    write_json,
)
from .logging import Loggable

T = TypeVar("T")


class SimpleFileCache(Loggable):
    SUPPORTED_FORMATS = {"json"}

    def __init__(self, path: str, name: str):
        self.path = path
        self.format = os.path.splitext(self.path)[1].lower().lstrip(".")
        self.name = name
        self.setup_logger(name)

        if self.format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"unknown format: {self.format}")

    def check_validity(self, max_age: datetime.timedelta | None = None) -> bool:
        try:
            age = get_file_staleness(self.path)
        except FileNotFoundError:
            self.log.info("miss")
            return False

        if max_age and age > max_age:
            self.log.info("stale")
            return False

        return True

    @staticmethod
    def check(func: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(func)
        def wrapper(
            self,
            *args,
            max_age: datetime.timedelta | None = None,
            **kwargs,
        ) -> T | None:
            if not self.check_validity(max_age=max_age):
                return None
            return func(self, *args, **kwargs)

        return wrapper

    @check
    def read_dict(self) -> dict:
        self.log.info("read")

        if self.format == "json":
            return read_json(self.path)

        assert False

    @check
    def read_series(self) -> pd.Series:
        self.log.info("read")

        if self.format == "json":
            return pd.read_json(self.path, typ="series")

        assert False

    def ensure_directory(self):
        path = os.path.dirname(self.path)
        os.makedirs(path, exist_ok=True)

    def write_json(self, data: dict | pd.Series):
        self.ensure_directory()

        if isinstance(data, pd.Series):
            data.to_json(self.path, indent=2)
        else:
            write_json(data, self.path)

    def write(self, data: dict | pd.Series):
        self.log.info("write")

        if self.format == "json":
            self.write_json(data)
        else:
            assert False
