# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GRIP (General Resources & Implementations for Python) is a Python 3.12 utility library providing typed helpers for configuration management, email (SMTP/IMAP), JSON/YAML, time/datetime, caching, logging, and more. Built on Pydantic v2 with strict validation throughout.

## Commands

```bash
# Package management — always use uv, never pip
uv sync                        # Install/sync dependencies
uv add <package>               # Add a dependency

# Testing
uv run pytest                  # Run all tests
uv run pytest tests/test_config.py              # Run a single test file
uv run pytest tests/test_config.py::test_name   # Run a single test
uv run pytest --config config.toml              # Run with external config (enables email tests)

# Linting & formatting
uv run ruff check grip/ tests/       # Lint
uv run ruff check --fix grip/ tests/ # Lint with auto-fix
uv run ruff format grip/ tests/      # Format

# Type checking
uv run basedpyright
```

## Architecture

- **`grip/__init__.py`** — Core utilities: `TCPAddress` (Pydantic-compatible host:port parser), file I/O (`read_file`, `write_file`, `read_toml`), string helpers, process control (`die`, `require_env`)
- **`grip/config/`** — `ConfigLoader[T]` generic class loading TOML configs with deferred secret injection; `BaseConfig` strict Pydantic base; `Secret` sentinel for unloaded secrets
- **`grip/email/`** — Abstract `EmailSender`/`EmailSenderConnection` interfaces with `SMTPEmailSender` and `IMAPMailBox` implementations; `Dummy*` classes for testing (stores to JSON files)
- **`grip/time.py`** — `TimeDelta` Pydantic validator for duration parsing, ISO date/datetime parsing
- **`grip/cache.py`** — `SimpleFileCache` decorator for JSON file-based caching with staleness
- **`grip/jsonutil.py`** / **`grip/yamlutil.py`** — Strongly-typed wrappers (`JSONValue`, `YAMLValue` recursive types) replacing `Any`
- **`grip/logging.py`** — `Loggable` mixin with `setup_logger()`, `sublogger()`, `@sublog` decorator
- **`grip/country.py`** — Country/locale lookups via pycountry

## Coding Conventions

### Python

- **Python 3.12** syntax, PEP 8 and modern idioms.
- Use `pathlib` not `os.path`, f-strings exclusively.
- **`import datetime`** as module, then `datetime.datetime`, `datetime.date`, etc. Use timezone-aware timestamps (`datetime.datetime.now().astimezone()`).
- Keep functions small and focused. Raise explicit, meaningful exceptions.
- Prefer composition over inheritance. Prefix module-private functions with `_`.
- Avoid magic values; use named constants. Never leave TODOs without context.
- All comments, docstrings, and documentation **must be in English**.

### Typing

- Built-in generics (`list`, `dict`, `set`, `tuple`, `type`) not `typing` equivalents. `X | None` not `Optional[X]`.
- Avoid `Any` and `# type: ignore`. When `Any` is unavoidable (untyped third-party code), document the reason explicitly.
- Public APIs must have fully explicit parameter and return types.
- Collection type choice:
  - `Iterable[T]`: immutable, size doesn't matter, only iteration needed.
  - `Sequence[T]`: immutable, size or indexing matters.
  - `list[T]`: order matters, mutability required.

### Docstrings

- Always multi-line with description on a separate line. **Never** inline `"""..."""`.
- Document arguments via `Annotated[]` with trailing commas — **never** use `Args:` sections.

```python
def func(
    arg0: Annotated[
        str,
        "<description>",
    ],
) -> ReturnType:
    """
    <description>
    """
```

### Pydantic

- **Pydantic v2.12 APIs only** with strict validation.
- Use `Annotated` types. Use `model_validate` and `model_dump` correctly.
- Avoid unnecessary custom validators. Keep validation logic explicit and readable.

### Testing (Pytest)

- Small, focused tests. Name tests clearly and descriptively.
- Use pytest fixtures effectively. Avoid over-mocking.
- Test behavior over implementation details. Use `pytest-asyncio` for async code.

### CLI (Typer)

- Use Typer idioms and annotations. Keep commands small and composable.
- Provide clear help messages and defaults. Ensure CLI APIs are fully typed.

### Linting & Type Checking

- **Ruff**: line-length 100, rules: F, E, W, I, N, UP, B, SIM, TCH, RUF.
- **basedpyright**: standard mode.
