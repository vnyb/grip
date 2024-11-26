import logging
import time
from types import ClassMethodDescriptorType
from typing import Self
import imap_tools

from contextlib import contextmanager

from grip.email.config import IMAPConfig

from .. import TCPAddress


class IMAPMailBox:
    def __init__(
        self,
        server: str,
        user: str,
        password: str,
        starttls: bool = False,
    ):
        addr = TCPAddress(server, 993)

        if starttls:
            self.imap = imap_tools.mailbox.MailBoxTls(addr.host, addr.port)
        else:
            self.imap = imap_tools.mailbox.MailBox(addr.host, addr.port)

        self.user = user
        self.password = password

    @classmethod
    def from_config(cls, config: IMAPConfig) -> Self:
        return cls(
            server=config.server,
            user=config.user,
            password=config.password.get_secret_value(),
            starttls=config.starttls,
        )

    @contextmanager
    def login(self):
        with self.imap.login(self.user, self.password) as mailbox:
            yield mailbox

    def wait_for(
        self,
        sender: str | None = None,
        to: str | None = None,
        subject: str | None = None,
        timeout=120,
    ):
        """
        Check mailbox and wait for the receipt of a mail matching
        <sender>, <to> (could be an alias) and <subject>.
        Read messages are ignored.
        """

        until = time.time() + timeout

        logging.info(f"to:{to}:")

        predicates = {}

        if sender:
            predicates["from_"] = sender

        if subject:
            predicates["subject"] = subject

        criteria = imap_tools.AND(
            **predicates,
            seen=False,
            new=True,
        )

        with self.login() as mailbox:
            while True:
                logging.info("checking mailbox %s...", to)

                for msg in mailbox.fetch(criteria):
                    if to and to not in msg.to:
                        continue
                    return msg

                timeout = max(int(until - time.time()), 1)
                logging.info(
                    "%s: waiting for email... (timeout = %d)",
                    to,
                    timeout,
                )
                logging.info(f"{sender}, {to}, {subject}")
                mailbox.idle.wait(timeout=timeout)
                if time.time() > until:
                    return None
