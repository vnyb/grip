import pytest

from grip import (
    TCPAddress,
)


def test_parse_tcp_addr():
    # With hostname
    assert TCPAddress.parse("host", port=80) == ("host", 80)
    assert TCPAddress.parse("host:443", port=80) == ("host", 443)
    assert TCPAddress.parse("host:443") == ("host", 443)

    with pytest.raises(ValueError):
        TCPAddress.parse("host")

    # IPv4
    assert TCPAddress.parse("192.168.1.1", port=80) == ("192.168.1.1", 80)
    assert TCPAddress.parse("192.168.1.1:443", port=80) == (
        "192.168.1.1",
        443,
    )
    assert TCPAddress.parse("192.168.1.1:443") == ("192.168.1.1", 443)

    with pytest.raises(ValueError):
        TCPAddress.parse("192.168.1.1")

    # IPv6
    assert TCPAddress.parse(
        "2001:db8::8a2e:370:7334",
        port=80,
    ) == ("2001:db8::8a2e:370:7334", 80)

    assert TCPAddress.parse(
        "[2001:db8::8a2e:370:7334]",
        port=80,
    ) == ("2001:db8::8a2e:370:7334", 80)

    assert TCPAddress.parse(
        "[2001:db8::8a2e:370:7334]:443",
        port=80,
    ) == ("2001:db8::8a2e:370:7334", 443)

    assert TCPAddress.parse("[2001:db8::8a2e:370:7334]:443") == (
        "2001:db8::8a2e:370:7334",
        443,
    )

    with pytest.raises(ValueError):
        TCPAddress.parse("2001:db8::8a2e:370:7334")

    with pytest.raises(ValueError):
        TCPAddress.parse("[2001:db8::8a2e:370:7334]")

    with pytest.raises(ValueError):
        TCPAddress.parse("[2001:db8::8a2e:370:7334")

    # to string
    assert str(TCPAddress("host", 443)) == "host:443"
    assert (
        str(
            TCPAddress(
                "2001:db8::8a2e:370:7334",
                443,
            )
        )
        == "[2001:db8::8a2e:370:7334]:443"
    )
