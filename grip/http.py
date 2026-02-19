"""
HTTP utilities
"""

from functools import cached_property

import httpx

from .jsonutil import JSONObject, JSONValue


def is_http_success(status_code: int) -> bool:
    """
    Check if a HTTP status code is a success code.
    """
    return 200 <= status_code < 300


def _get_content_type(resp: httpx.Response) -> str | None:
    """
    Get the Content-Type header from an httpx response
    """
    return resp.headers.get("Content-Type")


def get_response_json(resp: httpx.Response) -> JSONValue | None:
    """
    Parse Sanic or httpx JSON data if present in the response, return None otherwise
    """
    if _get_content_type(resp) != "application/json":
        return None
    return resp.json()


def _response_json_to_str(resp: httpx.Response) -> str | None:
    data = get_response_json(resp)
    return str(data) if data else None


def assert_http_status(
    resp: httpx.Response,
    status: int | None = None,
):
    """
    Assert that the HTTP response status matches the expected status.
    """

    response_status = resp.status_code

    if status is None:
        assert is_http_success(response_status), (
            f"{response_status} is not a success: {_response_json_to_str(resp)}"
        )
    else:
        assert response_status == status, (
            f"{response_status} != {status}: {_response_json_to_str(resp)}"
        )


class WrappedResponse:
    def __init__(self, resp: httpx.Response):
        self.resp = resp

    @cached_property
    def status(self) -> int:
        return self.resp.status_code

    @cached_property
    def json(self) -> JSONValue:
        return self.resp.json()

    @cached_property
    def json_obj(self) -> JSONObject:
        data = self.json
        if isinstance(data, dict):
            return data
        raise ValueError(f"Expected a JSON object, got {type(data).__name__}")


def check_resp(
    resp: httpx.Response,
    *,
    status: int | None = None,
) -> WrappedResponse:
    """
    Check that an httpx response has the expected status code.

    A convenience wrapper around assert_http_status that provides a cleaner interface for test
    assertions.
    """
    assert_http_status(resp, status=status)

    return WrappedResponse(resp)
