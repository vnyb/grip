import logging


class Loggable:
    _base_log: logging.Logger | None = None
    _log: logging.Logger | None = None

    def setup_logger(self, name: str):
        self._base_log = self._log = logging.getLogger(name)

    @property
    def log(self) -> logging.Logger:
        assert self._log
        return self._log

    @staticmethod
    def sublog(name: str):
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                self._log = logging.getLogger(f"{self._base_log}.{name}")
                try:
                    result = func(self, *args, **kwargs)
                finally:
                    self._log = self._base_log
                return result

            return wrapper

        return decorator
