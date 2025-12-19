"""Problem Report router for PRT file upload (7800/8800 series)."""

from datetime import datetime

from fastapi import APIRouter, Form, Response, UploadFile

from ..dependencies import AppSettings, validate_device_name

router = APIRouter(tags=["problem-report"])


@router.post("/problem-report")
async def problem_report(
    settings: AppSettings,
    devicename: str = Form(default=""),
    prt_file: UploadFile | None = None,
) -> Response:
    """Handle problem report file upload from phones.

    Phones POST multipart/form-data with devicename and prt_file (tar.gz).
    """
    # Newer firmware puts leading newline for form-data variables
    device_name = devicename.strip()

    if not validate_device_name(device_name):
        return Response(content="Invalid device", media_type="text/plain", status_code=403)

    if prt_file is None:
        return Response(content="Missing problem report", media_type="text/plain", status_code=500)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = settings.reports_dir / f"prt-{device_name}-{timestamp}.tar.gz"

    # Save uploaded file
    content = await prt_file.read()
    with open(output_file, "wb") as f:
        f.write(content)

    return Response(content="Log saved", media_type="text/plain")
