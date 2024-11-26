import pydantic
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from .. import TCPAddress


class IMAPConfig(BaseModel):
    server: str = Field(min_length=1)
    user: str = Field(min_length=1)
    password: SecretStr = Field(min_length=1)
    starttls: bool = Field(default=False)


class SMTPConfig(BaseModel):
    server: str = Field(min_length=1)
    user: str = Field(min_length=1)
    password: SecretStr = Field(min_length=1)
    starttls: bool = Field(default=False)
    timeout: int = Field(ge=1, default=30)
    sender: EmailStr | None = None

    _address: TCPAddress | None = None

    @property
    def address(self) -> TCPAddress:
        if self._address is None:
            self._address = TCPAddress(self.server)
        return self._address

    @property
    def host(self) -> str:
        return self.address.host

    @property
    def port(self) -> int:
        return self.address.port
