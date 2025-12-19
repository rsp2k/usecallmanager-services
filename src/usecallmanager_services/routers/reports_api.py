"""Reports API router for viewing quality and problem reports."""

import json
import tarfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from ..dependencies import AppSettings

router = APIRouter(prefix="/api/reports", tags=["reports-api"])


def parse_timestamp_from_filename(filename: str) -> datetime | None:
    """Extract timestamp from PRT filename like prt-SEP...-20241219123456.tar.gz."""
    try:
        # Format: prt-{device}-{YYYYMMDDHHmmss}.tar.gz
        parts = filename.replace(".tar.gz", "").split("-")
        if len(parts) >= 3:
            timestamp_str = parts[-1]
            return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    except (ValueError, IndexError):
        pass
    return None


def get_file_info(path: Path) -> dict:
    """Get file metadata."""
    stat = path.stat()
    return {
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
    }


# ============== Quality Reports API ==============


@router.get("/quality")
async def list_quality_reports(settings: AppSettings) -> JSONResponse:
    """List all devices with quality reports."""
    reports_dir = settings.reports_dir
    devices = []

    for qrt_file in sorted(reports_dir.glob("qrt-*.json")):
        device_name = qrt_file.stem.replace("qrt-", "")

        # Count entries and get latest timestamp
        entry_count = 0
        latest_timestamp = None

        try:
            with open(qrt_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry_count += 1
                        try:
                            entry = json.loads(line)
                            latest_timestamp = entry.get("timestamp", latest_timestamp)
                        except json.JSONDecodeError:
                            pass
        except Exception:
            pass

        devices.append({
            "device": device_name,
            "file": qrt_file.name,
            "entry_count": entry_count,
            "latest_report": latest_timestamp,
            **get_file_info(qrt_file),
        })

    return JSONResponse({
        "count": len(devices),
        "devices": devices,
    })


@router.get("/quality/{device}")
async def get_quality_reports(
    device: str,
    settings: AppSettings,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """Get quality report entries for a specific device."""
    # Sanitize device name
    device = device.strip()
    if not device.startswith("SEP") or len(device) != 15:
        raise HTTPException(status_code=400, detail="Invalid device name format")

    qrt_file = settings.reports_dir / f"qrt-{device}.json"

    if not qrt_file.exists():
        raise HTTPException(status_code=404, detail=f"No quality reports for device {device}")

    entries = []
    try:
        with open(qrt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading reports: {e}")

    # Reverse to show newest first
    entries.reverse()

    total = len(entries)
    paginated = entries[offset:offset + limit]

    return JSONResponse({
        "device": device,
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": paginated,
    })


# ============== Problem Reports API ==============


@router.get("/problem")
async def list_problem_reports(
    settings: AppSettings,
    device: str | None = Query(default=None, description="Filter by device name"),
) -> JSONResponse:
    """List all problem reports (PRT files)."""
    reports_dir = settings.reports_dir
    reports = []

    pattern = f"prt-{device}-*.tar.gz" if device else "prt-*.tar.gz"

    for prt_file in sorted(reports_dir.glob(pattern), reverse=True):
        # Parse filename: prt-{device}-{timestamp}.tar.gz
        parts = prt_file.stem.split("-")
        if len(parts) >= 3:
            device_name = parts[1]
            timestamp = parse_timestamp_from_filename(prt_file.name)

            reports.append({
                "device": device_name,
                "file": prt_file.name,
                "timestamp": timestamp.isoformat() if timestamp else None,
                **get_file_info(prt_file),
            })

    return JSONResponse({
        "count": len(reports),
        "reports": reports,
    })


@router.get("/problem/{filename}")
async def get_problem_report_info(
    filename: str,
    settings: AppSettings,
) -> JSONResponse:
    """Get information about a specific problem report file."""
    # Validate filename format
    if not filename.startswith("prt-") or not filename.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    prt_file = settings.reports_dir / filename

    if not prt_file.exists():
        raise HTTPException(status_code=404, detail="Problem report not found")

    # Parse device and timestamp from filename
    parts = filename.replace(".tar.gz", "").split("-")
    device_name = parts[1] if len(parts) >= 2 else "unknown"
    timestamp = parse_timestamp_from_filename(filename)

    # Try to list contents of the tar.gz
    contents = []
    try:
        with tarfile.open(prt_file, "r:gz") as tar:
            for member in tar.getmembers():
                contents.append({
                    "name": member.name,
                    "size": member.size,
                    "type": "file" if member.isfile() else "dir" if member.isdir() else "other",
                })
    except Exception:
        contents = None  # Unable to read archive

    return JSONResponse({
        "device": device_name,
        "file": filename,
        "timestamp": timestamp.isoformat() if timestamp else None,
        "contents": contents,
        **get_file_info(prt_file),
    })


@router.get("/problem/{filename}/download")
async def download_problem_report(
    filename: str,
    settings: AppSettings,
) -> FileResponse:
    """Download a problem report file."""
    # Validate filename format
    if not filename.startswith("prt-") or not filename.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Invalid filename format")

    prt_file = settings.reports_dir / filename

    if not prt_file.exists():
        raise HTTPException(status_code=404, detail="Problem report not found")

    return FileResponse(
        path=prt_file,
        filename=filename,
        media_type="application/gzip",
    )


# ============== Summary/Stats API ==============


@router.get("/summary")
async def reports_summary(settings: AppSettings) -> JSONResponse:
    """Get summary statistics for all reports."""
    reports_dir = settings.reports_dir

    # Count quality reports
    qrt_files = list(reports_dir.glob("qrt-*.json"))
    qrt_device_count = len(qrt_files)
    qrt_entry_count = 0

    for qrt_file in qrt_files:
        try:
            with open(qrt_file, "r", encoding="utf-8") as f:
                qrt_entry_count += sum(1 for line in f if line.strip())
        except Exception:
            pass

    # Count problem reports
    prt_files = list(reports_dir.glob("prt-*.tar.gz"))
    prt_count = len(prt_files)
    prt_total_size = sum(f.stat().st_size for f in prt_files)

    # Get unique devices from PRT files
    prt_devices = set()
    for prt_file in prt_files:
        parts = prt_file.stem.split("-")
        if len(parts) >= 2:
            prt_devices.add(parts[1])

    return JSONResponse({
        "quality_reports": {
            "device_count": qrt_device_count,
            "total_entries": qrt_entry_count,
        },
        "problem_reports": {
            "file_count": prt_count,
            "device_count": len(prt_devices),
            "total_size_bytes": prt_total_size,
        },
        "reports_directory": str(reports_dir),
    })
