"""Quality Report router for QRT logging (7800/8800 series)."""

import json
from datetime import datetime
from urllib.parse import quote_plus

from fastapi import APIRouter, Query, Request, Response

from ..asterisk_manager import get_manager_client
from ..dependencies import AppSettings, Is79xx, validate_device_name
from ..xml_responses import CiscoIPPhoneMenu, CiscoIPPhoneText

router = APIRouter(prefix="/quality-report", tags=["quality-report"])

# Report reason codes and descriptions
REPORT_REASONS = {
    "0": "Audio had echo",
    "1": "Audio had crackling",
    "2": "I could not hear them",
    "3": "They could not hear me",
    "4": "Other issue (unspecified)",
}


@router.get("")
async def quality_report(
    request: Request,
    is_79xx: Is79xx,
    name: str = Query(default=""),
) -> Response:
    """Display quality report reason selection menu."""
    if not validate_device_name(name):
        return Response(content="Invalid device", media_type="text/plain", status_code=403)

    base_url = str(request.base_url).rstrip("/")

    menu = CiscoIPPhoneMenu("Quality Report", is_79xx)
    for reason_code, reason_text in REPORT_REASONS.items():
        # Use QueryStringParam to pass reason with submit
        menu.add_item(reason_text, f"QueryStringParam:reason={quote_plus(reason_code)}")

    submit_url = f"{base_url}/quality-report/send?name={quote_plus(name)}"
    menu.add_softkey("Submit", submit_url, menu.softkey_position("select"))
    menu.add_softkey("Exit", "Init:Services", menu.softkey_position("exit"))

    return Response(content=menu.build(), media_type="text/xml")


@router.get("/send")
async def quality_report_send(
    is_79xx: Is79xx,
    settings: AppSettings,
    name: str = Query(default=""),
    reason: str = Query(default=""),
) -> Response:
    """Submit quality report and log to file."""
    if not validate_device_name(name):
        return Response(content="Invalid device", media_type="text/plain", status_code=403)

    # Get SIP peer information from Asterisk
    ip_address = None
    status = None
    rtp_rx_stat = None
    rtp_tx_stat = None

    try:
        async with get_manager_client(settings) as manager:
            peer_info = await manager.get_sip_peer_by_device(name)
            if peer_info:
                ip_address = peer_info.get("ip_address")
                status = peer_info.get("status")
                rtp_rx_stat = peer_info.get("rtp_rx_stat")
                rtp_tx_stat = peer_info.get("rtp_tx_stat")
    except Exception:
        # Continue even if Asterisk query fails
        pass

    reason_text = REPORT_REASONS.get(reason, "")

    # Append report to JSON log file
    log_file = settings.reports_dir / f"qrt-{name}.json"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ip_address": ip_address,
                    "status": status,
                    "reason": reason_text,
                    "rtp_rx_stat": rtp_rx_stat,
                    "rtp_tx_stat": rtp_tx_stat,
                }
            )
            + "\n"
        )

    text = CiscoIPPhoneText(
        "Quality Report",
        f"{reason_text} has been reported.",
        is_79xx,
    )
    text.add_softkey("Exit", "Init:Services", text.softkey_position("exit"))

    return Response(content=text.build(), media_type="text/xml")
