import datetime
import io
import logging
import os
import pathlib
import secrets
import string
import sys
import tomllib
from collections.abc import Callable, Sequence
from functools import lru_cache
from typing import Any, NoReturn

from pydantic_core import core_schema

ALNUM_LOWERCASE_CHARS = string.ascii_lowercase + string.digits
ALNUM_CHARS = string.ascii_letters + string.digits

BOOL_STRING_FALSE = {"0", "false", "n", "no", "non"}
BOOL_STRING_TRUE = {"1", "true", "y", "yes", "o", "oui"}


def remove_suffix(string: str, suffix: str) -> str:
    """
    Remove the given suffix from a string if it ends with it.
    """
    if string.endswith(suffix):
        return string[: -len(suffix)]
    return string


def die(message: str, *, logger: logging.Logger | None = None) -> NoReturn:
    """
    Log an error message and exit the process.
    """
    if logger is None:
        logger = logging.getLogger()
    logging.error(message)
    sys.exit(1)


def eprint(
    *args: object,
    sep: str | None = " ",
    end: str | None = "\n",
    flush: bool = False,
) -> None:
    """
    Print to stderr.
    """
    print(*args, file=sys.stderr, sep=sep, end=end, flush=flush)


@lru_cache
def string_to_bool(string: str | None, default: bool | None = None) -> bool:
    """
    Convert a string to a boolean value.
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
    """
    Return the value of an environment variable or die if it is not set.
    """
    try:
        return os.environ[name]
    except KeyError:
        die(f"environment variable '{name}' is not set")


def get_file_age(path: pathlib.Path) -> datetime.timedelta:
    """
    Return the time elapsed since the file was created.
    """
    stat = path.stat()
    creation_date = datetime.datetime.fromtimestamp(
        stat.st_ctime,
        tz=datetime.UTC,
    )
    return datetime.datetime.now(tz=datetime.UTC) - creation_date


def get_file_staleness(path: pathlib.Path) -> datetime.timedelta:
    """
    Return the time elapsed since the file was last modified.
    """
    stat = path.stat()
    last_modified_date = datetime.datetime.fromtimestamp(
        stat.st_mtime,
        tz=datetime.UTC,
    )
    return datetime.datetime.now(tz=datetime.UTC) - last_modified_date


def read_file(path: pathlib.Path, mode: str = "r") -> str:
    """
    Read and return the entire contents of a file.
    """
    with open(path, mode) as file:
        return file.read()


def write_file(data: str | bytes, path: pathlib.Path) -> None:
    """
    Write data to a file.
    """
    mode = "w" if isinstance(data, str) else "wb"

    with open(path, mode) as file:
        file.write(data)


def read_last_line(
    fp: io.BufferedReader,
    ignore_empty_lines: bool = False,
) -> str | None:
    """
    Read the last line of a binary buffered file.
    """
    fp.seek(0, 2)  # Move to the end of the file
    pos = start = end = fp.tell()

    def _read() -> bytes | None:
        nonlocal pos

        pos -= 1
        fp.seek(pos)
        return fp.read(1)

    while pos > 0:
        char = _read()

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


def read_toml(path: pathlib.Path) -> dict[str, Any]:
    """
    Read and parse a TOML file.

    Returns dict[str, Any] because TOML values are heterogeneous.
    """
    with open(path, "rb") as file:
        return tomllib.load(file)


def deep_dict_equal(
    a: dict[str, object],
    b: dict[str, object],
) -> bool:
    """
    Recursively compare two dictionaries for equality.
    """
    for key in a:
        if key not in b:
            return False
        val_a = a[key]
        val_b = b[key]
        if (
            isinstance(val_a, dict)
            and isinstance(val_b, dict)
            and not deep_dict_equal(val_a, val_b)
        ):
            return False
        if val_a != val_b:
            return False

    return all(key in a for key in b)


def all_equal(values: Sequence[object]) -> bool:
    """
    Check whether all elements in a non-empty sequence are equal.
    """
    assert len(values) > 0
    value = values[0]

    return all(i == value for i in values)


def apply_or_none[T, R](func: Callable[[T], R], value: T | None) -> R | None:
    """
    Apply a function to a value, or return None if the value is None.
    """
    return None if value is None else func(value)


class TCPAddress(str):
    """
    A TCP address consisting of a host and a port.

    Supports IPv4, IPv6 (bracketed notation), and Pydantic validation.
    Inherits from str, allowing direct string usage.
    """

    host: str
    port: int

    def __new__(cls, host: str, port: int | None = None) -> "TCPAddress":
        parsed_host, parsed_port = cls.parse(host, port)

        # Format the string representation
        if ":" in parsed_host:
            addr_str = f"[{parsed_host}]:{parsed_port}"
        else:
            addr_str = f"{parsed_host}:{parsed_port}"

        # Create the string instance
        instance = str.__new__(cls, addr_str)
        instance.host = parsed_host
        instance.port = parsed_port
        return instance

    @classmethod
    def parse(cls, addr: str, port: int | None = None) -> tuple[str, int]:
        """
        Parse a string address into a (host, port) tuple.
        """

        def _default() -> int:
            if port is None:
                raise ValueError("No port specified")
            return port

        segments = addr.split(":")
        if len(segments) == 1:
            # Plain hostname or IPv4 without port (e.g. "127.0.0.1")
            return addr, _default()

        if len(segments) == 2:
            # IPv4 with port (e.g. "127.0.0.1:8080")
            return segments[0], int(segments[1])

        # IPv6 address — must use bracketed notation for port disambiguation
        if not addr.startswith("["):
            return addr, _default()
        if addr.endswith("]"):
            return addr[1:-1], _default()
        if not segments[-2].endswith("]"):
            raise ValueError("Invalid host")
        host, _port = addr.rsplit(":", 1)
        return host[1:-1], cls.validate_port(_port)

    @staticmethod
    def validate_port(value: str | int) -> int:
        """
        Validate and return a port number in the range [0, 65535].
        """
        try:
            result = int(value)
        except ValueError as exc:
            raise ValueError("Port must be an integer") from exc

        if not (0 <= result <= 65535):
            raise ValueError("Port must be in [0-65535]")

        return result

    @classmethod
    def validate(cls, value: str | dict[str, Any]) -> "TCPAddress":
        """
        Validate a raw value (str or dict) into a TCPAddress instance.
        """
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

        raise TypeError(f"Cannot validate {type(value)} as TCPAddress")

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type,
        handler: Callable[..., core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        """
        Define the Pydantic core schema for validation.
        """
        return core_schema.no_info_plain_validator_function(cls.validate)
