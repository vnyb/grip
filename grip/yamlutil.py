"""
Strongly-typed wrappers around the PyYAML library.

Replaces the default Any return type with a recursive YAMLValue type
that accurately represents the YAML data model (as produced by SafeLoader).
"""

import datetime
import pathlib
from collections.abc import Iterator
from typing import Annotated

import yaml

type YAMLValue = (
    str
    | int
    | float
    | bool
    | None
    | datetime.datetime
    | datetime.date
    | bytes
    | YAMLObject
    | YAMLArray
)
type YAMLObject = dict[str, YAMLValue]
type YAMLArray = list[YAMLValue]


def _yaml_str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """
    Custom representer that uses block style for multi-line strings.
    """
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _yaml_str_representer)


def yaml_safe_load(
    stream: Annotated[
        str | bytes,
        "YAML string or bytes to deserialize (single document).",
    ],
) -> YAMLValue:
    """
    Strongly-typed wrapper around yaml.safe_load().

    Parses a single YAML document and returns a typed value.
    Only uses SafeLoader — arbitrary Python objects cannot be deserialized.
    """
    return yaml.safe_load(stream)  # pyright: ignore[reportAny]


def yaml_safe_load_all(
    stream: Annotated[
        str | bytes,
        "YAML string or bytes to deserialize (multiple documents).",
    ],
) -> Iterator[YAMLValue]:
    """
    Strongly-typed wrapper around yaml.safe_load_all().

    Parses multiple YAML documents separated by '---' and yields typed values.
    Only uses SafeLoader — arbitrary Python objects cannot be deserialized.
    """
    return yaml.safe_load_all(stream)  # pyright: ignore[reportAny]


def read_yaml(
    path: Annotated[
        pathlib.Path | str,
        "Path to the YAML file to read.",
    ],
) -> YAMLValue:
    """
    Read and deserialize a YAML file using SafeLoader.
    """
    with open(path, encoding="utf-8") as file:
        return yaml.safe_load(file)  # pyright: ignore[reportAny]


def write_yaml(
    data: Annotated[
        YAMLValue,
        "YAML-serializable data to write.",
    ],
    path: Annotated[
        pathlib.Path | str,
        "Path to the YAML file to write.",
    ],
    *,
    sort_keys: Annotated[
        bool,
        "Whether to sort dictionary keys in the output.",
    ] = False,
) -> None:
    """
    Serialize data and write it to a YAML file.
    """
    with open(path, "w", encoding="utf-8") as file:
        yaml.dump(data, file, allow_unicode=True, sort_keys=sort_keys)
