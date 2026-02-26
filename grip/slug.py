"""
URL slug validation and Pydantic SlugStr type.
"""

from typing import Any

from pydantic_core import core_schema
from slugify import slugify


def is_valid_slug(slug: str) -> bool:
    """
    Check whether a string is a valid URL slug.
    """
    return slugify(slug) == slug


class SlugStr(str):
    """
    Pydantic-validated string that must be a valid URL slug.

    Use in models like: slug: SlugStr
    """

    @classmethod
    def validate(cls, value: Any) -> "SlugStr":
        """
        Validate a raw value into a SlugStr instance.
        """
        if not isinstance(value, str):
            raise ValueError(f"expected str, got {type(value).__name__}")
        if not is_valid_slug(value):
            raise ValueError("invalid slug")
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
        handler: Any,
    ) -> core_schema.CoreSchema:
        """
        Define the Pydantic core schema for validation.
        """
        return core_schema.chain_schema([
            core_schema.str_schema(),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: core_schema.CoreSchema,
        handler: Any,
    ) -> dict[str, Any]:
        """
        Define the JSON schema representation as a plain string.
        """
        return {"type": "string"}
