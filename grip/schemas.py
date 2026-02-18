from typing import Annotated, Any, TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class NotNullable:
    """
    Pydantic annotation for optional but non-nullable fields.
    - Field omitted: OK, value = None
    - Field = None/null: validation error
    """

    def __get_pydantic_core_schema__(
        self,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        schema = handler(source)
        assert schema["type"] == "nullable"
        
        # Extract inner schema (without None)
        inner_schema = schema["schema"]
        
        # Create schema with None default, but rejects None as input
        return core_schema.with_default_schema(
            inner_schema,
            default=None,
        )


T = TypeVar("T")
Omissible = Annotated[T | None, NotNullable()]
