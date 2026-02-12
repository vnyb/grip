import tomllib

import pydantic


class Error(Exception):
    """
    Base exception for all errors in the config package.
    """


class TOMLDecodeError(Error, tomllib.TOMLDecodeError):
    """
    Raised when a TOML file cannot be decoded.
    """


class FileError(Error, OSError):
    """
    Raised when a file operation fails.
    """


class ValidationError(Error, pydantic.ValidationError):
    """
    Raised when a configuration model fails validation.
    """


class ConfigNotLoadedError(Error):
    """
    Raised when get_config is called before load_config.
    """


class SecretsNotLoadedError(Error):
    """
    Raised when secrets are accessed before they are loaded.
    """
