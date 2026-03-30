import pydantic
import pytest
from pydantic import BaseModel, SecretStr

from grip.pin import Pin6Str


def test_pin6():
    pin = Pin6Str("123456")
    assert isinstance(pin, SecretStr)
    assert pin.get_secret_value() == "123456"

    with pytest.raises(ValueError):
        Pin6Str("1234567")

    with pytest.raises(ValueError):
        Pin6Str("12345a")

    class _DummyModel(BaseModel):
        pin: Pin6Str

    dummy = _DummyModel.model_validate({"pin": "123456"})
    assert dummy.pin.get_secret_value() == "123456"

    with pytest.raises(pydantic.ValidationError):
        _DummyModel.model_validate({"pin": "1234567"})

    with pytest.raises(pydantic.ValidationError):
        _DummyModel.model_validate({"pin": "12345a"})
