import re
import secrets
import string
from collections.abc import Sequence
from typing import Annotated

from pwdlib import PasswordHash
from pydantic import SecretStr
from zxcvbn import zxcvbn

_MIN_LENGTH = 10
_MAX_LENGTH = 128
_MAX_CONSECUTIVE_IDENTICAL = 2
_MIN_ZXCVBN_SCORE = 3

_CONSECUTIVE_RE = re.compile(r"(.)\1{2,}")

_pwd_hash = PasswordHash.recommended()


class PasswordHashStr(str):
    """
    A strongly-typed password hash.
    """


class WeakPasswordError(ValueError):
    """
    Raised when a password fails strength validation.
    """

    def __init__(self, reasons: Sequence[str]) -> None:
        self.reasons = reasons
        super().__init__(f"weak password: {'; '.join(reasons)}")


def _has_uppercase(password: str) -> bool:
    """
    Check whether the password contains at least one uppercase letter.
    """
    return any(c.isupper() for c in password)


def _has_lowercase(password: str) -> bool:
    """
    Check whether the password contains at least one lowercase letter.
    """
    return any(c.islower() for c in password)


def _has_digit(password: str) -> bool:
    """
    Check whether the password contains at least one digit.
    """
    return any(c.isdigit() for c in password)


def _has_special(password: str) -> bool:
    """
    Check whether the password contains at least one special character (including space).
    """
    return any(not c.isalnum() for c in password)


def _has_consecutive_identical(password: str) -> bool:
    """
    Check whether the password contains 3 or more identical consecutive characters.
    """
    return _CONSECUTIVE_RE.search(password) is not None


def password_hash(password: SecretStr | str) -> PasswordHashStr:
    """
    Hash a password using Argon2id.
    """
    return PasswordHashStr(
        _pwd_hash.hash(
            password.get_secret_value() if isinstance(password, SecretStr) else password,
        )
    )


def password_verify(password: SecretStr | str, hash: PasswordHashStr) -> bool:
    """
    Verify a password against an Argon2id hash.

    Returns False on mismatch; lets InvalidHashError propagate.
    """
    return _pwd_hash.verify(
        password.get_secret_value() if isinstance(password, SecretStr) else password,
        hash,
    )


def password_check_strength(password: SecretStr | str) -> None:
    """
    Validate password strength against OWASP rules and zxcvbn entropy.

    Raises WeakPasswordError with all failed checks collected.
    """
    reasons: list[str] = []

    if isinstance(password, SecretStr):
        password = password.get_secret_value()

    if len(password) < _MIN_LENGTH:
        reasons.append(f"must be at least {_MIN_LENGTH} characters")

    if len(password) > _MAX_LENGTH:
        reasons.append(f"must be at most {_MAX_LENGTH} characters")

    complexity_classes = sum(
        [
            _has_uppercase(password),
            _has_lowercase(password),
            _has_digit(password),
            _has_special(password),
        ]
    )
    if complexity_classes < 3:
        reasons.append("must contain at least 3 of: uppercase, lowercase, digit, special")

    if _has_consecutive_identical(password):
        reasons.append(
            f"must not contain more than {_MAX_CONSECUTIVE_IDENTICAL} identical consecutive"
            " characters"
        )

    if len(password) <= _MAX_LENGTH:
        # zxcvbn returns an untyped dict — isolate the score extraction
        result = zxcvbn(password)
        score: int = result["score"]
        if score < _MIN_ZXCVBN_SCORE:
            reasons.append(f"too easily guessable (score {score}/{_MIN_ZXCVBN_SCORE})")

    if reasons:
        raise WeakPasswordError(reasons)


_LOWERCASE = string.ascii_lowercase
_UPPERCASE = string.ascii_uppercase
_DIGITS = string.digits
_SPECIAL = string.punctuation


def password_generate(
    length: Annotated[
        int,
        "Desired password length",
    ] = 16,
    check_strength: Annotated[
        bool,
        "Whether to check the password strength",
    ] = False,
) -> str:
    """
    Generate a cryptographically secure random password
    """

    if check_strength:
        if length < _MIN_LENGTH:
            raise ValueError(f"length must be at least {_MIN_LENGTH}, got {length}")
        if length > _MAX_LENGTH:
            raise ValueError(f"length must be at most {_MAX_LENGTH}, got {length}")

    alphabet = _LOWERCASE + _UPPERCASE + _DIGITS + _SPECIAL

    while True:
        mandatory = [
            secrets.choice(_LOWERCASE),
            secrets.choice(_UPPERCASE),
            secrets.choice(_DIGITS),
            secrets.choice(_SPECIAL),
        ]
        remaining = [secrets.choice(alphabet) for _ in range(length - len(mandatory))]
        chars = mandatory + remaining
        secrets.SystemRandom().shuffle(chars)
        candidate = "".join(chars)

        if not check_strength:
            return candidate

        try:
            password_check_strength(candidate)
        except WeakPasswordError:
            continue

        return candidate
