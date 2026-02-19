import pytest

from grip import TCPAddress
from grip.config import Secret
from grip.smtp import SmtpClient, SmtpConfig, TlsMode


@pytest.fixture
def smtp_config_starttls(smtpd):
    """
    Create SMTP configuration for STARTTLS mode.
    """
    smtpd.config.use_starttls = True
    return SmtpConfig(
        address=TCPAddress(host=smtpd.hostname, port=smtpd.port),
        username=None,
        from_email="sender@example.org",
        from_name="Test Sender",
        tls_mode=TlsMode.STARTTLS,
        password=None,
        validate_certs=False,
    )


@pytest.fixture
def smtp_config_tls(smtpd):
    """
    Create SMTP configuration for TLS mode.
    """
    smtpd.config.use_ssl = True
    return SmtpConfig(
        address=TCPAddress(host=smtpd.hostname, port=smtpd.port),
        username=None,
        from_email="sender@example.org",
        from_name="Test Sender",
        tls_mode=TlsMode.TLS,
        password=None,
        validate_certs=False,
    )


@pytest.mark.asyncio
async def test_send_email_html_only(smtpd, smtp_config_starttls):
    """
    Test sending an email with HTML content only.
    """
    client = SmtpClient(smtp_config_starttls)

    await client.send_email(
        to="recipient@example.org",
        subject="Test Subject",
        html_content="<html><body><h1>Hello World</h1></body></html>",
    )

    assert len(smtpd.messages) == 1
    message = smtpd.messages[0]
    assert message["Subject"] == "Test Subject"
    assert message["From"] == "Test Sender <sender@example.org>"
    assert message["To"] == "recipient@example.org"


@pytest.mark.asyncio
async def test_send_email_html_and_text(smtpd, smtp_config_starttls):
    """
    Test sending an email with both HTML and plain text content.
    """
    client = SmtpClient(smtp_config_starttls)

    await client.send_email(
        to="recipient@example.org",
        subject="Test Subject",
        html_content="<html><body><h1>Hello World</h1></body></html>",
        text_content="Hello World",
    )

    assert len(smtpd.messages) == 1
    message = smtpd.messages[0]
    assert message["Subject"] == "Test Subject"
    assert message.is_multipart()


@pytest.mark.asyncio
async def test_send_email_text_only(smtpd, smtp_config_starttls):
    """
    Test sending an email with plain text content only.
    """
    client = SmtpClient(smtp_config_starttls)

    await client.send_email(
        to="recipient@example.org",
        subject="Test Subject",
        html_content="",
        text_content="Hello World",
    )

    assert len(smtpd.messages) == 1
    message = smtpd.messages[0]
    assert message["Subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_send_email_empty_content(smtpd, smtp_config_starttls):
    """
    Test sending an email with empty content (should default to empty text).
    """
    client = SmtpClient(smtp_config_starttls)

    await client.send_email(
        to="recipient@example.org",
        subject="Test Subject",
        html_content="",
    )

    assert len(smtpd.messages) == 1
    message = smtpd.messages[0]
    assert message["Subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_send_email_tls_mode(smtpd, smtp_config_tls):
    """
    Test sending an email using TLS mode.
    """
    client = SmtpClient(smtp_config_tls)

    await client.send_email(
        to="recipient@example.org",
        subject="TLS Test",
        html_content="<html><body>TLS Content</body></html>",
    )

    assert len(smtpd.messages) == 1
    message = smtpd.messages[0]
    assert message["Subject"] == "TLS Test"


@pytest.mark.asyncio
async def test_send_email_with_auth(smtpd):
    """
    Test sending an email with authentication.
    """
    smtpd.config.use_starttls = True
    smtpd.config.login_username = "testuser"
    smtpd.config.login_password = "testpass"

    config = SmtpConfig(
        address=TCPAddress(host=smtpd.hostname, port=smtpd.port),
        username="testuser",
        from_email="sender@example.org",
        from_name="Test Sender",
        tls_mode=TlsMode.STARTTLS,
        password=Secret(secret_value="testpass"),
        validate_certs=False,
    )

    client = SmtpClient(config)

    await client.send_email(
        to="recipient@example.org",
        subject="Auth Test",
        html_content="<html><body>Auth Content</body></html>",
    )

    assert len(smtpd.messages) == 1


@pytest.mark.asyncio
async def test_send_multiple_emails(smtpd, smtp_config_starttls):
    """
    Test sending multiple emails sequentially.
    """
    client = SmtpClient(smtp_config_starttls)

    await client.send_email(
        to="recipient1@example.org",
        subject="First Email",
        html_content="<html><body>First</body></html>",
    )

    await client.send_email(
        to="recipient2@example.org",
        subject="Second Email",
        html_content="<html><body>Second</body></html>",
    )

    assert len(smtpd.messages) == 2
    assert smtpd.messages[0]["To"] == "recipient1@example.org"
    assert smtpd.messages[1]["To"] == "recipient2@example.org"


@pytest.mark.asyncio
async def test_config_property(smtp_config_starttls):
    """
    Test that config property returns the configuration.
    """
    client = SmtpClient(smtp_config_starttls)
    assert client.config == smtp_config_starttls
    assert client.config.from_email == "sender@example.org"


def test_smtp_config_password_loading():
    """
    Test password loading in SmtpConfig.
    """
    config = SmtpConfig(
        address=TCPAddress(host="localhost", port=587),
        username="user",
        from_email="test@example.org",
        from_name="Test",
        tls_mode=TlsMode.STARTTLS,
        password=Secret(secret_value="mypassword"),
    )

    password = config.get_password()
    assert password == "mypassword"


def test_smtp_config_password_none():
    """
    Test password loading when password is not set.
    """
    config = SmtpConfig(
        address=TCPAddress(host="localhost", port=587),
        username="user",
        from_email="test@example.org",
        from_name="Test",
        tls_mode=TlsMode.STARTTLS,
        password=None,
    )

    password = config.get_password()
    assert password is None


def test_smtp_config_default_tls_mode():
    """
    Test that default TLS mode is STARTTLS.
    """
    config = SmtpConfig(
        address=TCPAddress(host="localhost", port=587),
        username="user",
        from_email="test@example.org",
        from_name="Test",
        password=None,
    )

    assert config.tls_mode == TlsMode.STARTTLS


def test_tls_mode_enum():
    """
    Test TlsMode enum values.
    """
    assert TlsMode.TLS == "TLS"
    assert TlsMode.STARTTLS == "STARTTLS"
    assert str(TlsMode.TLS) == "TLS"
    assert str(TlsMode.STARTTLS) == "STARTTLS"


def test_smtp_config_default_validate_certs():
    """
    Test that default validate_certs is True.
    """
    config = SmtpConfig(
        address=TCPAddress(host="localhost", port=587),
        username="user",
        from_email="test@example.org",
        from_name="Test",
        password=None,
    )

    assert config.validate_certs is True


def test_smtp_config_validate_certs_false():
    """
    Test setting validate_certs to False.
    """
    config = SmtpConfig(
        address=TCPAddress(host="localhost", port=587),
        username="user",
        from_email="test@example.org",
        from_name="Test",
        password=None,
        validate_certs=False,
    )

    assert config.validate_certs is False
