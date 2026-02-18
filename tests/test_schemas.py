import pytest
from pydantic import BaseModel, ValidationError

from grip.schemas import Omissible


def test_omissible():
    """
    Verify that Omissible allows omitting a field (value = None)
    but rejects explicit None.
    """

    class _DummySchema(BaseModel):
        required: str
        nullable: str | None
        optional: str | None = None
        omissible: Omissible[str]

    # Field omitted: OK, value = None
    data = _DummySchema.model_validate({"required": "value", "nullable": None})
    assert data.required == "value"
    assert data.nullable is None
    assert data.optional is None
    assert data.omissible is None

    # Field provided: OK
    data = _DummySchema.model_validate(
        {"required": "value", "nullable": None, "omissible": "present"}
    )
    assert data.omissible == "present"

    # Field = None: error
    with pytest.raises(ValidationError):
        _DummySchema.model_validate({"required": "value", "nullable": None, "omissible": None})

    # JSON schema verification
    schema = _DummySchema.model_json_schema()
    
    # Required fields: required and nullable only
    assert set(schema["required"]) == {"required", "nullable"}
    
    # required: non-nullable string, no default
    assert schema["properties"]["required"] == {"title": "Required", "type": "string"}
    
    # nullable: string or null, no default
    assert schema["properties"]["nullable"] == {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "title": "Nullable",
    }
    
    # optional: string or null, with None default
    assert schema["properties"]["optional"] == {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "default": None,
        "title": "Optional",
    }
    
    # omissible: string only (not null), with None default
    assert schema["properties"]["omissible"] == {
        "default": None,
        "title": "Omissible",
        "type": "string",
    }

    from pprint import pprint

    pprint(_DummySchema.model_json_schema())
