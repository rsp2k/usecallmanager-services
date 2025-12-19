"""Information router for 7900 series Info button help."""

import re
from pathlib import Path

from fastapi import APIRouter, Query, Response
from lxml import etree

from ..xml_responses import CiscoIPPhoneText

router = APIRouter(tags=["information"])

# Path to phone help XML file
PHONE_HELP_FILE = Path("phone_help.xml")


@router.get("/information")
async def help_information(
    id: str = Query(default="", pattern=r"^[0-9]+$"),
) -> Response:
    """Display help information for 7900 series Info button.

    Looks up help text by ID from phone_help.xml.
    """
    if not id or not re.match(r"^[0-9]+$", id):
        return Response(content="Invalid id", media_type="text/plain", status_code=500)

    title = "Information"
    help_text = "Sorry, no help on that topic."

    if PHONE_HELP_FILE.exists():
        try:
            document = etree.parse(str(PHONE_HELP_FILE))
            element = document.find(f'HelpItem[ID="{id}"]')

            if element is not None:
                title_elem = element.find("Title")
                text_elem = element.find("Text")

                if title_elem is not None and title_elem.text:
                    title = title_elem.text
                if text_elem is not None and text_elem.text:
                    help_text = text_elem.text
        except etree.Error:
            pass

    # Information endpoint is for 7900 series only (hardcoded positions)
    text = CiscoIPPhoneText(title, help_text, is_79xx=True)
    text.add_softkey("Exit", "Key:Info", "3")

    return Response(content=text.build(), media_type="text/xml")
