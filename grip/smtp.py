"""
Async SMTP client with TLS/STARTTLS support.
"""

import enum
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import cached_property
from typing import Annotated

import aiosmtplib
from pydantic import EmailStr, Field

from . import TCPAddress
from .config import BaseConfig, Secret


class TlsMode(enum.StrEnum):
    """
    TLS mode for SMTP connections.
    """

    TLS = "TLS"
    STARTTLS = "STARTTLS"


class SmtpError(Exception):
    """
    SMTP error.
    """


class SmtpConfig(BaseConfig):
    """
    SMTP email configuration.
    """

    address: TCPAddress = Field(
        description="SMTP server address",
        min_length=1,
    )

    username: str | None = Field(
        description="SMTP username",
        min_length=1,
    )

    from_email: EmailStr = Field(
        description="SMTP from email address",
        min_length=1,
    )

    from_name: str | None = Field(
        description="SMTP from name",
        min_length=1,
    )

    tls_mode: TlsMode = Field(
        description="TLS mode for SMTP connection",
        default=TlsMode.STARTTLS,
    )

    password: Secret | None = Field(
        description="SMTP password",
    )

    validate_certs: bool = Field(
        description="Validate SSL certificates (disable for testing with self-signed certs)",
        default=True,
    )

    def get_password(self) -> str | None:
        """
        Get SMTP password as plain string, or None if not loaded/empty.
        """
        if self.password is not None and self.password.is_loaded():
            pw = self.password.get_secret_value()
            return pw if pw else None
        return None


class SmtpClient:
    """
    Async SMTP email client.
    """

    def __init__(
        self,
        config: Annotated[
            SmtpConfig,
            "Application configuration",
        ],
    ) -> None:
        """
        Initialize email client with configuration.
        """
        self._config = config

    @property
    def config(self) -> SmtpConfig:
        return self._config

    @cached_property
    def _format_from(self) -> str:
        return f"{self.config.from_name} <{self.config.from_email}>"

    def _get_tls_context(self) -> ssl.SSLContext | None:
        """
        Create TLS context based on configuration.
        """
        if not self.config.validate_certs:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            return context
        return None

    async def send_email(
        self,
        *,
        to: Annotated[
            EmailStr,
            "Recipient email address",
        ],
        subject: Annotated[
            str,
            "Email subject",
        ],
        html_content: Annotated[
            str,
            "HTML email content",
        ],
        text_content: Annotated[
            str | None,
            "Plain text email content (fallback)",
        ] = None,
    ) -> None:
        """
        Send an email via SMTP.
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self._format_from
        message["To"] = to

        if not html_content and not text_content:
            text_content = ""

        if text_content is not None:
            part_text = MIMEText(text_content, "plain")
            message.attach(part_text)

        if html_content:
            part_html = MIMEText(html_content, "html")
            message.attach(part_html)

        try:
            tls_context = self._get_tls_context()

            if self.config.tls_mode == TlsMode.TLS:
                await aiosmtplib.send(
                    message,
                    hostname=self.config.address.host,
                    port=self.config.address.port,
                    username=self.config.username,
                    password=self.config.get_password(),
                    use_tls=True,
                    tls_context=tls_context,
                )
            else:
                await aiosmtplib.send(
                    message,
                    hostname=self.config.address.host,
                    port=self.config.address.port,
                    username=self.config.username,
                    password=self.config.get_password(),
                    start_tls=True,
                    tls_context=tls_context,
                )
        except aiosmtplib.SMTPException as e:
            raise SmtpError(f"Failed to send email to {to}: {e}") from e
