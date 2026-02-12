"""
Strongly-typed wrappers around the json standard library.

Replaces the default Any return type with a recursive JSONValue type
that accurately represents the JSON data model.
"""

import json
import pathlib
from collections.abc import Callable
from typing import Annotated, Any

from _typeshed import SupportsRead

type JSONValue = str | int | float | bool | None | JSONObject | JSONArray
type JSONObject = dict[str, JSONValue]
type JSONArray = list[JSONValue]


def json_load(
    fp: Annotated[
        SupportsRead[str | bytes],
        "File-like object containing JSON data.",
    ],
    *,
    cls: Annotated[
        type[json.JSONDecoder] | None,
        "Custom JSONDecoder subclass.",
    ] = None,
    object_hook: Annotated[
        Callable[[dict[Any, Any]], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the result of any object literal decoded.",
    ] = None,
    parse_float: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of every JSON float to be decoded.",
    ] = None,
    parse_int: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of every JSON int to be decoded.",
    ] = None,
    parse_constant: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of JSON constants (NaN, Infinity, -Infinity).",
    ] = None,
    object_pairs_hook: Annotated[
        Callable[[list[tuple[Any, Any]]], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with an ordered list of pairs for any object literal decoded.",
    ] = None,
    **kwds: Any,  # pyright: ignore[reportAny, reportExplicitAny]
) -> JSONValue:
    """
    Strongly-typed wrapper around json.load().
    """
    return json.load(  # pyright: ignore[reportAny]
        fp,
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        **kwds,
    )


def json_loads(
    s: Annotated[
        str | bytes | bytearray,
        "JSON string or bytes to deserialize.",
    ],
    *,
    cls: Annotated[
        type[json.JSONDecoder] | None,
        "Custom JSONDecoder subclass.",
    ] = None,
    object_hook: Annotated[
        Callable[[dict[Any, Any]], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the result of any object literal decoded.",
    ] = None,
    parse_float: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of every JSON float to be decoded.",
    ] = None,
    parse_int: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of every JSON int to be decoded.",
    ] = None,
    parse_constant: Annotated[
        Callable[[str], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with the string of JSON constants (NaN, Infinity, -Infinity).",
    ] = None,
    object_pairs_hook: Annotated[
        Callable[[list[tuple[Any, Any]]], Any] | None,  # pyright: ignore[reportExplicitAny]
        "Function called with an ordered list of pairs for any object literal decoded.",
    ] = None,
    **kwds: Any,  # pyright: ignore[reportAny, reportExplicitAny]
) -> JSONValue:
    """
    Strongly-typed wrapper around json.loads().
    """
    return json.loads(  # pyright: ignore[reportAny]
        s,
        cls=cls,
        object_hook=object_hook,
        parse_float=parse_float,
        parse_int=parse_int,
        parse_constant=parse_constant,
        object_pairs_hook=object_pairs_hook,
        **kwds,
    )


def read_json(
    path: Annotated[
        pathlib.Path | str,
        "Path to the JSON file to read.",
    ],
) -> JSONValue:
    """
    Read and deserialize a JSON file.
    """
    with open(path, encoding="utf-8") as file:
        return json.load(file)  # pyright: ignore[reportAny]


def write_json(
    data: Annotated[
        JSONValue,
        "JSON-serializable data to write.",
    ],
    path: Annotated[
        pathlib.Path | str,
        "Path to the JSON file to write.",
    ],
    *,
    indent: Annotated[
        int | None,
        "Number of spaces for indentation. None for compact output.",
    ] = 2,
) -> None:
    """
    Serialize data and write it to a JSON file.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=indent)
