import json
import tomllib
import typing
from pathlib import Path
from typing import Annotated, Any, ClassVar, Self, TypeVar, override

import pydantic_core
from pydantic import BaseModel, ConfigDict, SecretStr

from . import exceptions

_SENTINEL = object()


class Secret(SecretStr):
    """
    A secret field that can be left uninitialized at parse time.

    Use as a type annotation with a default value::

        my_secret: Secret = Secret()

    Accessing a field whose value is still the default sentinel
    raises ``SecretsNotLoadedError``.
    """

    _is_sentinel: bool

    def __init__(self, secret_value: str | object = _SENTINEL) -> None:
        if secret_value is _SENTINEL:
            super().__init__("")
            self._is_sentinel = True
        else:
            assert isinstance(secret_value, str)
            super().__init__(secret_value)
            self._is_sentinel = False

    def is_loaded(self) -> bool:
        """
        Return whether this secret has been initialized with a real value.
        """
        return not self._is_sentinel


class BaseConfig(BaseModel):
    """
    Base configuration model.

    All project configuration models should inherit from this class.

    Secret fields (typed as ``Secret``) are optional at parse time.
    Accessing a secret that has not been loaded yet raises
    ``SecretsNotLoadedError``.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(strict=True)

    @override
    def __getattribute__(self, name: str) -> object:
        """
        Intercept attribute access to detect unloaded secrets.
        """
        value = typing.cast(object, super().__getattribute__(name))
        if isinstance(value, Secret) and not value.is_loaded():
            raise exceptions.SecretsNotLoadedError(
                f"Secret field '{name}' has not been loaded yet"
            )
        return value


TBaseConfig = TypeVar("TBaseConfig", bound=BaseConfig)


def _read_toml(path: Path) -> dict[str, object]:
    """
    Read and parse a TOML file, raising config exceptions on failure.
    """
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except OSError as exc:
        raise FileNotFoundError(f"Cannot read {path}: {exc}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"Invalid TOML in {path}: {exc}") from exc


def _read_json_dict(path: Path) -> dict[str, Any]:
    """
    Read a JSON file and ensure it contains a top-level object.
    """
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise FileNotFoundError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}, got {type(data).__name__}")

    return data


def _inject_secrets(
    model: BaseConfig,
    secrets: dict[str, object],
    _errors: list[pydantic_core.InitErrorDetails] | None = None,
    _prefix: tuple[str | int, ...] = (),
) -> None:
    """
    Recursively inject secret values into a BaseConfig model.

    Raises ``exceptions.ValidationError`` (via pydantic) when *secrets*
    contains keys that don't map to ``Secret`` fields, or values that
    are not strings.
    """
    is_root = _errors is None
    errors: list[pydantic_core.InitErrorDetails] = (
        _errors if _errors is not None else []
    )

    for key, value in secrets.items():
        loc = (*_prefix, key)

        # Unknown field
        if key not in type(model).model_fields:
            errors.append({"type": "extra_forbidden", "loc": loc, "input": value})
            continue

        # Use object.__getattribute__ to bypass the Secret sentinel guard
        current = typing.cast(object, object.__getattribute__(model, key))

        # Recurse into nested BaseConfig sub-models
        if isinstance(current, BaseConfig) and isinstance(value, dict):
            nested_secrets = typing.cast(dict[str, object], value)
            _inject_secrets(current, nested_secrets, _errors=errors, _prefix=loc)
            continue

        # Leaf: must be a Secret field receiving a str value
        if not isinstance(current, Secret):
            errors.append({"type": "extra_forbidden", "loc": loc, "input": value})
            continue

        if not isinstance(value, str):
            errors.append({"type": "string_type", "loc": loc, "input": value})
            continue

        object.__setattr__(model, key, Secret(value))

    if is_root and errors:
        raise exceptions.ValidationError.from_exception_data(
            title=type(model).__name__,
            line_errors=errors,
        )


class ConfigLoader[TBaseConfig: BaseConfig]:
    """
    A class for loading and validating configuration from a TOML file.

    Subclass with a concrete type argument to use:

        class MyLoader(ConfigLoader[MyConfig]):
            pass

    The config_type is extracted automatically from the generic argument
    via __init_subclass__.
    """

    config_type: ClassVar[type[BaseConfig]]
    _singleton: ClassVar[Self | None] = None
    path: Path | None
    _config: TBaseConfig | None = None

    def __init_subclass__(
        cls, *, config_type: type[BaseConfig], **kwargs: object
    ) -> None:
        super().__init_subclass__(**kwargs)

        # Verify consistency between the keyword argument and the Generic type
        orig_bases: tuple[type, ...] = getattr(cls, "__orig_bases__", ())
        for base in orig_bases:
            origin = typing.get_origin(base)
            if origin is None or not issubclass(origin, ConfigLoader):
                continue
            args = typing.get_args(base)
            if args and isinstance(args[0], type) and args[0] is not config_type:
                msg = (
                    f"{cls.__name__}: config_type={config_type.__name__}"
                    f" does not match generic argument {args[0].__name__}"
                )
                raise TypeError(msg)

        cls.config_type = config_type

    def __init__(
        self,
        path: Annotated[
            Path | None,
            "Optional path to a TOML file to load immediately on init.",
        ] = None,
    ):
        self.path = path
        self._config = None

        if path is not None:
            self._config = self.load_file(path)

    @property
    def config(self) -> TBaseConfig:
        """
        Get the configuration.
        """
        if self._config is None:
            raise exceptions.ConfigNotLoadedError("No configuration loaded")
        return self._config

    def load(
        self,
        config: Annotated[
            TBaseConfig,
            "A validated configuration instance to store.",
        ],
    ) -> None:
        """
        Load the configuration from the given configuration instance.
        """
        self._config = config

    def load_file(
        self,
        path: Annotated[
            Path | None,
            "Path to the TOML file. Falls back to self.path if None.",
        ] = None,
    ) -> TBaseConfig:
        """
        Load the configuration from the TOML file.
        """
        if path is None:
            path = self.path

        if path is None:
            raise exceptions.Error("No configuration path provided")

        data = _read_toml(path)
        config = typing.cast(TBaseConfig, self.config_type.model_validate(data))
        self.load(config)
        return config

    def load_secrets(
        self,
        secrets: Annotated[
            dict[str, object],
            "Nested dict mirroring the config structure. Leaf values are secret strings.",
        ],
    ) -> None:
        """
        Inject secret values into the already-loaded configuration.

        Raises ``exceptions.ValidationError`` when a key does not correspond
        to a ``Secret`` field or a value is not a ``str``.
        """
        config = self.config  # raises ConfigNotLoadedError if not loaded
        _inject_secrets(config, secrets)

    def load_secrets_from_file(
        self,
        path: Annotated[
            Path,
            "Path to a TOML or JSON secrets file. Format is detected from the extension.",
        ],
    ) -> None:
        """
        Load secrets from a file and inject them into the configuration.

        Supported formats: ``.toml``, ``.json``. The format is detected
        automatically from the file extension.

        Raises ``exceptions.Error`` for unsupported extensions.
        """
        suffix = path.suffix.lower()
        if suffix == ".toml":
            secrets = _read_toml(path)
        elif suffix == ".json":
            secrets = _read_json_dict(path)
        else:
            raise exceptions.Error(f"Unsupported secrets file extension '{suffix}'")
        self.load_secrets(secrets)

    def set_secret(
        self,
        path: Annotated[
            str,
            "Dotted path to the Secret field, e.g. 'database.password'.",
        ],
        value: Annotated[
            str | SecretStr,
            "The secret value to inject. A SecretStr is unwrapped automatically.",
        ],
    ) -> None:
        """
        Set a single secret by dotted path.

        Traverses nested ``BaseConfig`` sub-models and sets the leaf
        ``Secret`` field. Raises ``exceptions.Error`` if the path is
        invalid or the target field is not a ``Secret``.
        """
        config: BaseConfig = self.config
        parts = path.split(".")

        # Traverse to the parent model
        for part in parts[:-1]:
            child = typing.cast(object, object.__getattribute__(config, part))
            if not isinstance(child, BaseConfig):
                raise exceptions.Error(
                    f"'{part}' in path '{path}' is not a nested config model"
                )
            config = child

        field_name = parts[-1]
        if field_name not in type(config).model_fields:
            raise exceptions.Error(
                f"Unknown field '{field_name}' in {type(config).__name__}"
            )

        current = typing.cast(object, object.__getattribute__(config, field_name))
        if not isinstance(current, Secret):
            raise exceptions.Error(
                f"Field '{field_name}' in {type(config).__name__} is not a Secret"
            )

        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        object.__setattr__(config, field_name, Secret(raw))

    @classmethod
    def singleton(cls) -> Self:
        """
        Return a singleton instance of the ConfigLoader.
        """
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    @classmethod
    def get(cls) -> TBaseConfig:
        """
        Get the configuration from the singleton instance.
        """
        return cls.singleton().config
