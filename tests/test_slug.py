import pytest
from pydantic import BaseModel, ValidationError

from grip.slug import SlugStr, is_valid_slug


def test_is_valid_slug():
    assert is_valid_slug("hello") is True
    assert is_valid_slug("my-post-123") is True
    assert is_valid_slug("a") is True

    assert is_valid_slug("Hello World") is False
    assert is_valid_slug("café") is False
    assert is_valid_slug("a b") is False
    assert is_valid_slug("UPPERCASE") is False


def test_check_slug():
    slug_str = SlugStr.validate("hello")
    assert slug_str == "hello"
    assert isinstance(slug_str, SlugStr)

    with pytest.raises(ValueError, match="invalid slug"):
        SlugStr.validate("invalid slug")
    with pytest.raises(ValueError, match="invalid slug"):
        SlugStr.validate("Café")


def test_slug_str_in_model():
    class MyModel(BaseModel):
        slug: SlugStr

    m = MyModel.model_validate({"slug": "valid-slug"})
    assert m.slug == "valid-slug"
    assert isinstance(m.slug, SlugStr)

    with pytest.raises(ValidationError):
        MyModel.model_validate({"slug": "invalid slug"})

    with pytest.raises(ValidationError):
        MyModel.model_validate({"slug": {"invalid": "value"}})

    with pytest.raises(ValidationError):
        MyModel.model_validate({"slug": None})

    with pytest.raises(ValidationError):
        MyModel.model_validate({"slug": 123})
