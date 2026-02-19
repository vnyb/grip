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


def test_tcp_addr_as_str():
    # TCPAddress should be usable as a string since it inherits from str
    addr = TCPAddress("host", 443)
    assert addr == "host:443"
    assert isinstance(addr, str)
    assert addr.startswith("host")
    assert addr.endswith("443")

    # IPv6 address
    addr_ipv6 = TCPAddress("2001:db8::8a2e:370:7334", 443)
    assert addr_ipv6 == "[2001:db8::8a2e:370:7334]:443"
    assert isinstance(addr_ipv6, str)
    assert addr_ipv6.startswith("[2001")

    # Access host and port attributes
    assert addr.host == "host"
    assert addr.port == 443
    assert addr_ipv6.host == "2001:db8::8a2e:370:7334"
    assert addr_ipv6.port == 443
