import json
import os
import tempfile

from email_validator import validate_email

from ..time import now_tz
from .common import EmailSender


class DummyMailBox:
    """
    Dummy mail box for testing purposes
    """

    # FIXME: Not very efficient, but ok for now

    TMP_DIR = None

    @classmethod
    def dir_path(cls) -> str:
        if cls.TMP_DIR is None:
            cls.TMP_DIR = tempfile.TemporaryDirectory()
        return cls.TMP_DIR.name

    def __init__(self, email: str):
        validate_email(email, check_deliverability=False)
        self.email = email
        self.path = os.path.join(self.dir_path(), f"{email}.json")
        self._data = None

    def load(self) -> list[dict]:
        try:
            with open(self.path, "r") as fp:
                return json.load(fp)
        except FileNotFoundError:
            return []

    def add(self, sender: str, subject: str, body: str):
        data = self.load()
        data.append(
            {
                "date": str(now_tz()),
                "from": sender,
                "subject": subject,
                "body": body,
            }
        )
        with open(self.path, "w") as fp:
            json.dump(data, fp)

    def __iter__(self):
        self._data = reversed(self.load())
        return self

    def __next__(self) -> dict:
        assert self._data
        return next(self._data)


class DummyEmailSender(EmailSender):
    def __init__(self, sender: str):
        super().__init__(sender)

    def send_text(self, to: str, subject: str, text: str):
        mailbox = DummyMailBox(to)
        mailbox.add(self.sender, subject, text)
