"""
SMTP e-mail sender
"""

from os import walk
import smtplib
import ssl

from contextlib import contextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from typing import Self

from grip.email.config import SMTPConfig

from .common import (
    EmailSender,
    EmailSenderConnection,
)


class SMTPSenderConnection(EmailSenderConnection):
    def __init__(
        self,
        sender: str,
        smtp_connection,
    ):
        super().__init__(sender)
        self.smtp_connection = smtp_connection

    def check_config(self):
        self.smtp_connection.noop()

    def _send(self, msg):
        to = [msg["To"]]
        self.smtp_connection.sendmail(self.sender, to, msg.as_string())

    def _set_metadata(self, msg, to, subject):
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject

    def send_text(
        self,
        to,
        subject,
        text,
    ):
        msg = EmailMessage()
        self._set_metadata(msg, to, subject)
        msg.set_content(text)
        self._send(msg)

    def send_html(
        self,
        to,
        subject,
        html,
    ):
        msg = MIMEMultipart()
        self._set_metadata(msg, to, subject)
        body = MIMEText(html, "html", "utf-8")
        msg.attach(body)
        self._send(msg)


class SMTPEmailSender(EmailSender):
    """SMTP e-mail sender"""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        sender: str,
        starttls: bool = False,
        timeout: int = 30,
    ):
        super().__init__(sender)

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.starttls = starttls
        self.timeout = timeout

    @classmethod
    def from_config(cls, config: SMTPConfig) -> Self:
        assert config.sender
        return cls(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password.get_secret_value(),
            sender=config.sender,
            starttls=config.starttls,
            timeout=config.timeout,
        )

    @contextmanager
    def connect(self):
        if self.starttls:
            with smtplib.SMTP(
                self.host,
                self.port,
                timeout=self.timeout,
            ) as connection:
                # STARTTLS
                context = ssl.create_default_context()
                connection.ehlo()
                connection.starttls(context=context)
                connection.ehlo()
                connection.login(self.user, self.password)
                yield SMTPSenderConnection(
                    self.sender,
                    connection,
                )
        else:
            # SSL
            with smtplib.SMTP_SSL(
                self.host,
                self.port,
                timeout=self.timeout,
            ) as connection:
                connection.login(self.user, self.password)
                yield SMTPSenderConnection(
                    self.sender,
                    connection,
                )

    def check_config(self):
        with self.connect() as conn:
            conn.check_config()

    def send_text(self, to: str, subject: str, text: str):
        with self.connect() as conn:
            conn.send_text(to, subject, text)
