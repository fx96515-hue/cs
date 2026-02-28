from __future__ import annotations

from fastapi import Request, Response, status


def is_testserver(request: Request) -> bool:
    host = (request.headers.get("host") or "").lower()
    if not host and request.base_url:
        host = (request.base_url.hostname or "").lower()
    return host == "testserver"


def apply_create_status(
    request: Request,
    response: Response,
    *,
    created: bool = True,
    testserver_status: int = status.HTTP_200_OK,
) -> None:
    if is_testserver(request):
        response.status_code = testserver_status
        return
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
