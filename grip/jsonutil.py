"""
Strongly-typed wrappers around json.load() and json.loads().

Replaces the default Any return type with a recursive JSONValue type
that accurately represents the JSON data model.
"""

import json

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Any

if TYPE_CHECKING:
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
