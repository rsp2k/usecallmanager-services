"""Directory router for local directory from Asterisk voicemail.conf."""

from math import ceil
from urllib.parse import quote_plus

from fastapi import APIRouter, Query, Request, Response

from ..asterisk_manager import get_manager_client
from ..dependencies import AppSettings, Is79xx
from ..xml_responses import CiscoIPPhoneDirectory, CiscoIPPhoneMenu, CiscoIPPhoneText

router = APIRouter(prefix="/directory", tags=["directory"])

# Index mappings for phone keypad
DIAL_INDICES = ("1", "2ABC", "3DEF", "4GHI", "5JKL", "6MNO", "7PQRS", "8TUV", "9WXYZ", "0")


@router.get("")
async def directory_index(request: Request, is_79xx: Is79xx) -> Response:
    """Display directory index (letter selection)."""
    base_url = str(request.base_url).rstrip("/")

    menu = CiscoIPPhoneMenu("Local Directory", is_79xx)
    for index in DIAL_INDICES:
        menu.add_item(index, f"{base_url}/directory/entries?index={quote_plus(index)}")

    menu.add_softkey("Exit", "Init:Directories", menu.softkey_position("exit"))
    select_name = "Select" if is_79xx else "View"
    menu.add_softkey(select_name, "SoftKey:Select", menu.softkey_position("select"))
    menu.add_softkey("Help", f"{base_url}/directory/help", menu.softkey_position("update"))

    return Response(content=menu.build(), media_type="text/xml")


@router.get("/entries")
async def directory_entries(
    request: Request,
    is_79xx: Is79xx,
    settings: AppSettings,
    index: str = Query(default=""),
    page: int = Query(default=1, ge=1),
) -> Response:
    """Display directory entries for a given index."""
    base_url = str(request.base_url).rstrip("/")

    if not index:
        # Redirect to index if no filter provided
        return await directory_index(request, is_79xx)

    async with get_manager_client(settings) as manager:
        all_entries = await manager.get_voicemail_users()

    # Filter entries by first letter matching the index
    entries = [
        (mailbox, name) for mailbox, name in all_entries if name and name[0].upper() in index
    ]
    entries.sort(key=lambda e: e[1])

    # Pagination: 10 entries per page
    per_page = 10
    total_pages = max(1, ceil(len(entries) / per_page))
    page = min(page, total_pages)

    start = (page - 1) * per_page
    page_entries = entries[start : start + per_page]

    # Build title with page indicator if needed
    title = index + (f" {page}/{total_pages}" if total_pages > 1 else "")

    directory = CiscoIPPhoneDirectory(title, is_79xx)
    for mailbox, name in page_entries:
        directory.add_entry(name, mailbox)

    dial_name = "Dial" if is_79xx else "Call"
    directory.add_softkey("Exit", f"{base_url}/directory", directory.softkey_position("exit"))
    directory.add_softkey(dial_name, "SoftKey:Select", directory.softkey_position("select"))

    if page < total_pages:
        next_url = f"{base_url}/directory/entries?index={quote_plus(index)}&page={page + 1}"
        directory.add_softkey("Next", next_url, directory.softkey_position("next"))

    if page > 1:
        prev_url = f"{base_url}/directory/entries?index={quote_plus(index)}&page={page - 1}"
        directory.add_softkey("Previous", prev_url, directory.softkey_position("previous"))

    return Response(content=directory.build(), media_type="text/xml")


@router.get("/help")
async def directory_help(is_79xx: Is79xx) -> Response:
    """Display directory help text."""
    text = CiscoIPPhoneText(
        "How To Use",
        "Use the keypad or navigation key to select the first letter of the person's name.",
        is_79xx,
    )
    text.add_softkey("Back", "SoftKey:Exit", text.softkey_position("exit"))

    return Response(content=text.build(), media_type="text/xml")


@router.get("/79xx")
async def directory_menuitem(request: Request) -> Response:
    """7900 series need a menu item before the index.

    This provides a wrapper menu item for 79xx directory URLs.
    """
    base_url = str(request.base_url).rstrip("/")

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<CiscoIPPhoneMenu>\n"
        "  <MenuItem>\n"
        "    <Name>Local Directory</Name>\n"
        f"    <URL>{base_url}/directory</URL>\n"
        "  </MenuItem>\n"
        "</CiscoIPPhoneMenu>\n"
    )

    return Response(content=xml, media_type="text/xml")
