import datetime
import os
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, ClassVar, TypeVar

import pandas as pd

from . import (
    get_file_staleness,
)
from .jsonutil import JSONObject, read_json, write_json
from .logging import Loggable

T = TypeVar("T")


class SimpleFileCache(Loggable):
    SUPPORTED_FORMATS: ClassVar[set[str]] = {"json"}

    def __init__(self, path: Path, name: str):
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
            self: SimpleFileCache,
            *args: Any,
            max_age: datetime.timedelta | None = None,
            **kwargs: Any,
        ) -> T | None:
            if not self.check_validity(max_age=max_age):
                return None
            return func(self, *args, **kwargs)

        return wrapper

    @check
    def read_dict(self) -> JSONObject:
        self.log.info("read")

        if self.format == "json":
            data = read_json(self.path)
            if isinstance(data, dict):
                return data
            raise ValueError(f"Expected a JSON object, got {type(data).__name__}")

        raise ValueError(f"Unknown format: {self.format}")

    @check
    def read_series(self) -> pd.Series:
        self.log.info("read")

        if self.format == "json":
            return pd.read_json(self.path, typ="series")

        raise ValueError(f"Unknown format: {self.format}")

    def ensure_directory(self):
        path = os.path.dirname(self.path)
        os.makedirs(path, exist_ok=True)

    def write_json(self, data: JSONObject | pd.Series):
        self.ensure_directory()

        if isinstance(data, pd.Series):
            data.to_json(self.path, indent=2)
        else:
            write_json(data, self.path)

    def write(self, data: JSONObject | pd.Series):
        self.log.info("write")

        if self.format == "json":
            self.write_json(data)
        else:
            raise ValueError(f"Unknown format: {self.format}")
