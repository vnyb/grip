import secrets

from pydantic import EmailStr

from grip import ALNUM_CHARS, ALNUM_LOWERCASE_CHARS


def generate_random_lower_alnum(length=16) -> str:
    """
    Generate a secure random lowercase alphanumeric string.
    """
    return "".join(secrets.choice(ALNUM_LOWERCASE_CHARS) for _ in range(length))


def generate_random_alnum(length=16) -> str:
    """
    Generate a secure random alphanumeric string.
    """
    return "".join(secrets.choice(ALNUM_CHARS) for _ in range(length))


def generate_random_email(*, domain="example.org") -> EmailStr:
    """
    Generate a random e-mail address.
    """
    username = generate_random_lower_alnum(12)
    return f"{username}@{domain}".lower()
