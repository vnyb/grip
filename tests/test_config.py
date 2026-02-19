from pathlib import Path

import pydantic
import pytest
from pydantic import Field, SecretStr

from grip.config import BaseConfig, ConfigLoader, Secret, exceptions


class FirstConfig(BaseConfig):
    foo: int = Field(ge=42)
    bar: str
    baz: bool = Field(default=True)
    first_secret: Secret = Secret()


class SecondConfig(BaseConfig):
    integer: int = Field(ge=42)
    string: str
    second_secret: Secret = Secret()


class DummyConfig(BaseConfig):
    top_level_secret: Secret = Secret()
    first: FirstConfig
    second: SecondConfig


class DummyConfigLoader(ConfigLoader[DummyConfig], config_type=DummyConfig):
    pass


def test_config_type_mismatch() -> None:
    """
    The config_type keyword must match the Generic type argument.
    """

    class OtherConfig(BaseConfig):
        x: int

    with pytest.raises(TypeError, match="does not match generic argument"):

        class _BadLoader(ConfigLoader[DummyConfig], config_type=OtherConfig):  # pyright: ignore[reportUnusedClass]
            pass


def test_load_file_not_found(tmp_path: Path) -> None:
    """
    A missing file must raise FileNotFoundError.
    """
    loader = DummyConfigLoader()
    missing = tmp_path / "nope.toml"

    with pytest.raises(FileNotFoundError):
        _ = loader.load_file(missing)


def test_load_invalid_toml(tmp_path: Path) -> None:
    """
    A syntactically invalid TOML file must raise ValueError.
    """
    loader = DummyConfigLoader()
    bad_toml = tmp_path / "bad.toml"
    _ = bad_toml.write_text("this is not = [valid toml", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid TOML"):
        _ = loader.load_file(bad_toml)


def test_load_validation_error(tmp_path: Path) -> None:
    """
    A valid TOML file whose values fail Pydantic validation
    must raise pydantic.ValidationError.
    """
    loader = DummyConfigLoader()
    invalid_values = tmp_path / "invalid.toml"
    # foo < 42 violates the ge=42 constraint, bar is missing
    _ = invalid_values.write_text("foo = 1\n", encoding="utf-8")

    with pytest.raises(pydantic.ValidationError):
        _ = loader.load_file(invalid_values)


def test_load_ok(tmp_path: Path) -> None:
    """
    A valid TOML file must be loaded correctly.
    """
    loader = DummyConfigLoader()
    good = tmp_path / "good.toml"
    _ = good.write_text(
        """\
[first]
foo = 42
bar = "hello"
baz = false

[second]
integer = 42
string = "hello"
""",
        encoding="utf-8",
    )

    config = loader.load_file(good)

    assert isinstance(config, DummyConfig)
    assert config.first.foo == 42
    assert config.first.bar == "hello"
    assert config.first.baz is False
    assert config.second.integer == 42
    assert config.second.string == "hello"

    with pytest.raises(exceptions.SecretsNotLoadedError):
        assert config.second.second_secret.get_secret_value() == "hello"

    config.second.second_secret = Secret("hello")
    assert config.second.second_secret.get_secret_value() == "hello"


def test_load_secrets():
    loader = DummyConfigLoader()
    loader.load(
        DummyConfig(
            first=FirstConfig(
                foo=42,
                bar="hello",
                first_secret=Secret("hello"),
            ),
            second=SecondConfig(
                integer=42,
                string="hello",
                second_secret=Secret("hello"),
            ),
        )
    )

    with pytest.raises(exceptions.ValidationError):
        loader.load_secrets(
            {
                "first": {
                    "first_secret": 43,  # wrong type
                },
                "second": {
                    "wrong_key": "secret1",
                },
            }
        )

    loader.load_secrets(
        {
            "top_level_secret": "secret0",
            "first": {
                "first_secret": "secret1",
            },
            "second": {
                "second_secret": "secret2",
            },
        }
    )
    assert loader.config.top_level_secret.get_secret_value() == "secret0"
    assert loader.config.first.first_secret.get_secret_value() == "secret1"
    assert loader.config.second.second_secret.get_secret_value() == "secret2"

    loader.set_secret("second.second_secret", "secret3")
    assert loader.config.second.second_secret.get_secret_value() == "secret3"

    loader.set_secret("second.second_secret", SecretStr("secret4"))
    assert loader.config.second.second_secret.get_secret_value() == "secret4"


def test_load_ok_default_value(tmp_path: Path) -> None:
    """
    When baz is omitted, the default value (True) must be used.
    """
    loader = DummyConfigLoader()
    minimal = tmp_path / "minimal.toml"
    _ = minimal.write_text(
        """\
[first]
foo = 42
bar = "hello"

[second]
integer = 42
string = "hello"
""",
        encoding="utf-8",
    )

    loaded = loader.load_file(minimal)

    assert loaded.first.foo == 42
    assert loaded.first.bar == "hello"
    assert loaded.first.baz is True
    assert loaded.second.integer == 42
    assert loaded.second.string == "hello"


def test_singleton() -> None:
    """
    DummyLoader.get() must return the config loaded via the singleton.
    """
    config = DummyConfig(
        first=FirstConfig(
            foo=42,
            bar="singleton",
            first_secret=Secret("hello"),
        ),
        second=SecondConfig(
            integer=42,
            string="hello",
            second_secret=Secret("hello"),
        ),
    )
    DummyConfigLoader.singleton().load(config)

    result = DummyConfigLoader.get()

    assert result is config
    assert result.first.foo == 42
    assert result.first.bar == "singleton"
    assert result.first.baz is True
    assert result.second.integer == 42
    assert result.second.string == "hello"


def test_unknown_field_attribute_error() -> None:
    """
    Accessing an unknown field must raise AttributeError.
    """
    config = DummyConfig(
        first=FirstConfig(
            foo=42,
            bar="test",
            first_secret=Secret("hello"),
        ),
        second=SecondConfig(
            integer=42,
            string="hello",
            second_secret=Secret("hello"),
        ),
    )

    # Test accessing a non-existent field
    with pytest.raises(AttributeError, match="'DummyConfig' object has no attribute"):
        _ = config.unknown_field  # type: ignore

    with pytest.raises(AttributeError, match="'FirstConfig' object has no attribute"):
        _ = config.first.nonexistent  # type: ignore
