import datetime
import io
import json
import logging
import os
import sys
import tomllib
import yaml

from functools import lru_cache
from typing import Callable, NoReturn, Tuple, TypeVar
from pydantic_core import core_schema
from slugify import slugify
from typing import Callable, NoReturn, Tuple, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def remove_suffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[: -len(suffix)]
    return string


def die(message: str, *, logger: logging.Logger | None = None) -> NoReturn:
    if logger is None:
        logger = logging.getLogger()
    logging.error(message)
    sys.exit(1)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


BOOL_STRING_FALSE = {"0", "false", "n", "no", "non"}
BOOL_STRING_TRUE = {"1", "true", "y", "yes", "o", "oui"}


@lru_cache
def string_to_bool(string: str | None, default: bool | None = None) -> bool:
    """
    Convert string to boolean
    """

    if string is not None:
        string = string.strip().lower()

        if string in BOOL_STRING_FALSE:
            return False
        if string in BOOL_STRING_TRUE:
            return True

    if default is None:
        raise ValueError("Cannot convert string to boolean")

    return default


def require_env(name: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        die(f"environment variable '{name}' is not set")


def is_valid_slug(slug: str) -> bool:
    return slugify(slug) == slug


def check_slug(slug: str) -> str:
    if not is_valid_slug(slug):
        raise ValueError("invalid slug")
    return slug


def get_file_age(path: str) -> datetime.timedelta:
    timestamp = os.path.getctime(path)
    creation_date = datetime.datetime.fromtimestamp(timestamp)
    return datetime.datetime.now() - creation_date


def get_file_staleness(path: str) -> datetime.timedelta:
    timestamp = os.path.getmtime(path)
    last_modified_date = datetime.datetime.fromtimestamp(timestamp)
    return datetime.datetime.now() - last_modified_date


def read_file(path: str, mode="r") -> str:
    with open(path, mode) as file:
        return file.read()


def write_file(data: str | bytes, path: str):
    mode = "w" if isinstance(data, str) else "wb"

    with open(path, mode) as file:
        file.write(data)


def read_last_line(fp: io.BufferedReader, ignore_empty_lines=False) -> str | None:
    fp.seek(0, 2)  # Move to the end of the file
    pos = start = end = fp.tell()

    def read() -> bytes | None:
        nonlocal pos

        pos -= 1
        fp.seek(pos)
        return fp.read(1)

    while pos > 0:
        char = read()

        if char == b"\n":
            if end - start == 0 and ignore_empty_lines:
                end = start = pos
                continue
            break
        else:
            start = pos

    n = end - start
    if n <= 0:
        return None if ignore_empty_lines else ""

    fp.seek(start)
    return fp.read(n).decode()


def read_json(path: str):
    with open(path, "r") as file:
        return json.load(file)


def write_json(data, path: str, indent=True):
    with open(path, "w") as file:
        json.dump(data, file, indent=indent)


def read_yaml(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def save_yaml(data, path: str):
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(data, file, allow_unicode=True, sort_keys=False)


def yaml_str_representer(dumper, data):
    if "\n" in data:  # Si la chaîne contient plusieurs lignes
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, yaml_str_representer)


def read_toml(path: str) -> dict:
    with open(path, "rb") as file:
        return tomllib.load(file)


def deep_dict_equal(a: dict, b: dict) -> bool:
    for key in a.keys():
        if key not in b:
            return False
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            if not deep_dict_equal(a[key], b[key]):
                return False
        if a[key] != b[key]:
            return False

    for key in b.keys():
        if key not in a:
            return False

    return True


def all_equal(values) -> bool:
    assert len(values) > 0
    value = values[0]

    for i in values:
        if i != value:
            return False
    return True


def apply_or_none(func: Callable[[T], R], value: T | None) -> R | None:
    return None if value is None else func(value)


class TCPAddress:
    def __init__(self, host: str, port: int | None = None):
        self.host, self.port = self.parse(host, port)

    def __str__(self):
        if ":" in self.host:
            return f"[{self.host}]:{self.port}"
        return f"{self.host}:{self.port}"

    @classmethod
    def parse(cls, addr: str, port: int | None = None) -> Tuple[str, int]:
        def default():
            if port is None:
                raise ValueError("No port specified")
            return port

        segments = addr.split(":")
        if len(segments) == 1:
            # TODO check IPv4 format
            return addr, default()

        if len(segments) == 2:
            # TODO check IPv4 format
            return segments[0], int(segments[1])

        # TODO check IPv6 format
        if not addr.startswith("["):
            return addr, default()
        if addr.endswith("]"):
            return addr[1:-1], default()
        if not segments[-2].endswith("]"):
            raise ValueError("Invalid host")
        host, _port = addr.rsplit(":", 1)
        return host[1:-1], cls.validate_port(_port)

    @staticmethod
    def validate_port(value) -> int:
        try:
            port = int(value)
        except ValueError as exc:
            raise ValueError("Port must be an integer") from exc

        if not (0 <= port <= 65535):
            raise ValueError("Port must be in [0-65535]")

        return port

    @classmethod
    def validate(cls, value):
        if isinstance(value, dict):
            host = value.get("host")
            if host is None:
                raise ValueError("No host specified")
            port = value.get("port")
            if port is None:
                raise ValueError("No port specified")
            port = cls.validate_port(port)
            return cls(host, port)

        if isinstance(value, str):
            host, port = cls.parse(value)
            return cls(host, port)

    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        """
        Define the Pydantic core schema for validation.
        """
        return core_schema.no_info_plain_validator_function(cls.validate)
