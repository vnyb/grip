import pytest

from grip.password import (
    WeakPasswordError,
    password_check_strength,
    password_generate,
    password_hash,
    password_verify,
)

# A reasonably strong password for positive tests
STRONG_PASSWORD = "C0rrect-Horse!42"


def test_returns_argon2_encoded_string() -> None:
    hashed = password_hash(STRONG_PASSWORD)
    assert hashed.startswith("$argon2")


def test_different_hashes_for_same_password() -> None:
    h1 = password_hash(STRONG_PASSWORD)
    h2 = password_hash(STRONG_PASSWORD)
    assert h1 != h2


def test_correct_password() -> None:
    hashed = password_hash(STRONG_PASSWORD)
    assert password_verify(STRONG_PASSWORD, hashed) is True


def test_wrong_password() -> None:
    hashed = password_hash(STRONG_PASSWORD)
    assert password_verify("wrong-password", hashed) is False


def test_empty_password() -> None:
    hashed = password_hash(STRONG_PASSWORD)
    assert password_verify("", hashed) is False


def test_strong_password_passes() -> None:
    password_check_strength(STRONG_PASSWORD)


def test_too_short() -> None:
    with pytest.raises(WeakPasswordError, match="at least 10"):
        password_check_strength("Ab1!")


def test_too_long() -> None:
    with pytest.raises(WeakPasswordError, match="at most 128"):
        password_check_strength("A1!" + "a" * 126)


def test_insufficient_complexity() -> None:
    # Only lowercase and digits — missing 2 of 4 classes
    with pytest.raises(WeakPasswordError, match="at least 3 of"):
        password_check_strength("abcdefghij123")


def test_consecutive_identical_rejected() -> None:
    with pytest.raises(WeakPasswordError, match="identical consecutive"):
        password_check_strength("Aaaa1!bcdefgh")


def test_two_consecutive_identical_ok() -> None:
    # 2 consecutive identical chars should be fine
    password_check_strength("Aab1!cDefgh99")


def test_low_zxcvbn_score() -> None:
    with pytest.raises(WeakPasswordError, match="easily guessable"):
        password_check_strength("Password1!")


def test_multiple_reasons_collected() -> None:
    with pytest.raises(WeakPasswordError) as exc_info:
        password_check_strength("aaa")
    assert len(exc_info.value.reasons) >= 2


def test_generate():
    for _ in range(10):
        password = password_generate(check_strength=True)
        password_check_strength(password)
