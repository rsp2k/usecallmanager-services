"""Authentication router for CGI/Execute requests."""

from fastapi import APIRouter, Query, Response

from ..dependencies import AppSettings

router = APIRouter(tags=["authentication"])


@router.get("/authentication")
async def cgi_authentication(
    settings: AppSettings,
    UserID: str = Query(default=""),
    Password: str = Query(default=""),
) -> Response:
    """Authenticate CGI/Execute requests from phones.

    Returns AUTHORIZED or UNAUTHORIZED based on credentials.
    """
    if UserID != settings.cgi_username or Password != settings.cgi_password:
        return Response(content="UNAUTHORIZED", media_type="text/plain")
    return Response(content="AUTHORIZED", media_type="text/plain")
