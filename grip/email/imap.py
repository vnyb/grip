import logging
import time
import imap_tools

from contextlib import contextmanager

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
            self.imap = imap_tools.MailBoxTls(addr.host, addr.port)
        else:
            self.imap = imap_tools.MailBox(addr.host, addr.port)

        self.user = user
        self.password = password

    @contextmanager
    def login(self):
        with self.imap.login(self.user, self.password) as mailbox:
            yield mailbox

    def wait_for(
        self,
        sender: str,
        to: str,
        subject: str,
        timeout=120,
    ):
        """
        Check mailbox and wait for the receipt of a mail matching
        <sender>, <to> (could be an alias) and <subject>.
        Read messages are ignored.
        """

        until = time.time() + timeout

        logging.info(f"to:{to}:")

        criteria = imap_tools.AND(
            from_=sender,
            # to=to, # Seems bogus
            subject=subject,
            seen=False,
            new=True,
        )

        with self.login() as mailbox:
            while True:
                logging.info("checking mailbox %s...", to)
                for msg in mailbox.fetch(criteria):
                    if to not in msg.to:
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
