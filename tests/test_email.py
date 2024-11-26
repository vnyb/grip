from pydantic_core.core_schema import datetime_schema
import pytest

from grip import now_tz, read_toml
from grip.email.config import IMAPConfig, SMTPConfig
from grip.email.dummy import (
    DummyEmailSender,
    DummyMailBox,
)
from grip.email.imap import IMAPMailBox
from grip.email.smtp import SMTPEmailSender


@pytest.fixture
def config_path(request) -> str | None:
    return request.config.getoption("--config", None)


@pytest.fixture
def config(config_path: str | None) -> dict | None:
    if config_path is None:
        return None

    return read_toml(config_path)


@pytest.fixture
def smtp_config(config: dict | None) -> SMTPConfig | None:
    if config is None:
        return None

    if "smtp" not in config:
        return None

    return SMTPConfig.model_validate(config["smtp"])


@pytest.fixture
def imap_config(config: dict | None) -> IMAPConfig | None:
    if config is None:
        return None

    if "imap" not in config:
        return None

    return IMAPConfig.model_validate(config["imap"])


def test_real_mail(smtp_config: SMTPConfig | None, imap_config: IMAPConfig | None):
    if smtp_config is None:
        pytest.skip("No SMTP configuration")
    if imap_config is None:
        pytest.skip("No IMAP configuration")

    assert smtp_config.sender
    sender = SMTPEmailSender.from_config(smtp_config)
    sender.check_config()
    subject = "grip email test {}".format(now_tz().isoformat())
    text = "test body"
    sender.send_text(smtp_config.sender, subject, text)

    mailbox = IMAPMailBox.from_config(imap_config)
    msg = mailbox.wait_for(
        sender=smtp_config.sender,
        subject=subject,
        timeout=180,
    )

    assert msg
    assert msg.to[0] == smtp_config.sender
    assert msg.subject == subject
    assert msg.text.strip() == text.strip()


def test_dummy():
    sender = DummyEmailSender("foo@example.org")

    sender.send_text("bar@example.org", "Coucou 1", "Bonjour")
    sender.send_text("bar@example.org", "Coucou 2", "Bonjour")

    sender.send_text("bar+alias@example.org", "Coucou", "Bonjour")

    # Mailbox iterates backwards (latest mail first)
    mailbox = DummyMailBox("bar@example.org")
    iterator = iter(mailbox)

    mail = next(iterator)
    assert mail["from"] == sender.sender
    assert mail["subject"] == "Coucou 2"
    assert mail["body"] == "Bonjour"

    mail = next(iterator)
    assert mail["from"] == sender.sender
    assert mail["subject"] == "Coucou 1"
    assert mail["body"] == "Bonjour"

    with pytest.raises(StopIteration):
        next(iterator)

    # Alias = separate mailbox
    mailbox = DummyMailBox("bar+alias@example.org")
    iterator = iter(mailbox)

    mail = next(iterator)
    assert mail["from"] == sender.sender
    assert mail["subject"] == "Coucou"
    assert mail["body"] == "Bonjour"

    with pytest.raises(StopIteration):
        next(iterator)
