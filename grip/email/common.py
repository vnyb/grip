from contextlib import contextmanager


class EmailSenderConnection:
    """Base class for e-mail sender connection"""

    def __init__(self, sender: str):
        self.sender = sender

    def check_config(self):
        raise NotImplementedError

    def send_text(self, to, subject, text):
        raise NotImplementedError

    def send_html(self, to, subject, html):
        raise NotImplementedError


class EmailSender:
    """Base class for e-mail sender"""

    def __init__(self, sender):
        self.sender = sender

    @contextmanager
    def connect(self):
        raise NotImplementedError

    def send_text(self, to: str, subject: str, text: str):
        raise NotImplementedError
