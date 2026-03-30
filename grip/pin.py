import secrets
from typing import Any, Self

from pwdlib import PasswordHash
from pydantic import GetCoreSchemaHandler, SecretStr
from pydantic_core import CoreSchema, core_schema

_pin_hash = PasswordHash.recommended()


class Pin6Str(SecretStr):
    """
    6-digit PIN string (digits only, length 6). Validated by Pydantic.
    """

    def __new__(cls, secret_value: str) -> "Pin6Str":
        if len(secret_value) != 6 or not secret_value.isdigit():
            raise ValueError("Pin6Str must be exactly 6 digits")
        return object.__new__(cls)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_wrap_validator_function(
            cls._pydantic_validate,
            core_schema.str_schema(
                min_length=6,
                max_length=6,
                pattern=r"^\d{6}$",
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda x: str(x)),
        )

    @classmethod
    def _pydantic_validate(cls, value: Any, handler: Any) -> "Pin6Str":
        validated = handler(value)
        return cls(validated)

    @classmethod
    def generate(cls) -> Self:
        """
        Generate a secure random 6-digit PIN.
        """
        return cls(f"{secrets.randbelow(1_000_000):06d}")
