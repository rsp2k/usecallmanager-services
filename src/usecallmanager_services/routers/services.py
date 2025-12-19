"""Services router for menu and parked calls."""

from fastapi import APIRouter, Request, Response

from ..asterisk_manager import get_manager_client
from ..dependencies import AppSettings, Is79xx
from ..xml_responses import CiscoIPPhoneDirectory, CiscoIPPhoneMenu

router = APIRouter(prefix="/services", tags=["services"])


@router.get("")
async def services_menu(request: Request, is_79xx: Is79xx) -> Response:
    """Display services menu."""
    base_url = str(request.base_url).rstrip("/")

    menu = CiscoIPPhoneMenu("Services", is_79xx)
    menu.add_item("Parked Calls", f"{base_url}/services/parked-calls")
    menu.add_softkey("Exit", "Init:Services", menu.softkey_position("exit"))
    menu.add_softkey("Select", "SoftKey:Select", menu.softkey_position("select"))

    return Response(content=menu.build(), media_type="text/xml")


@router.get("/parked-calls")
async def parked_calls(
    request: Request,
    is_79xx: Is79xx,
    settings: AppSettings,
) -> Response:
    """Display currently parked calls."""
    base_url = str(request.base_url).rstrip("/")

    async with get_manager_client(settings) as manager:
        calls = await manager.get_parked_calls()

    directory = CiscoIPPhoneDirectory("Parked Calls", is_79xx, prompt="Select call")
    for extension, name in calls:
        directory.add_entry(name, extension)

    dial_name = "Dial" if is_79xx else "Call"
    directory.add_softkey("Exit", f"{base_url}/services", directory.softkey_position("exit"))
    directory.add_softkey(dial_name, "SoftKey:Select", directory.softkey_position("select"))
    directory.add_softkey("Update", "SoftKey:Update", directory.softkey_position("update"))

    return Response(content=directory.build(), media_type="text/xml")
