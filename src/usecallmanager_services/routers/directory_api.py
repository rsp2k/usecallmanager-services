"""Directory API router for web interface."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from ..asterisk_manager import get_manager_client
from ..dependencies import AppSettings

router = APIRouter(prefix="/directory", tags=["directory-api"])


@router.get("/list")
async def list_directory(
    settings: AppSettings,
    search: str = Query(default="", description="Search term for name or extension"),
    sort: str = Query(default="name", description="Sort by: name, extension"),
    order: str = Query(default="asc", description="Sort order: asc, desc"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    """Get directory entries with search and pagination."""
    try:
        async with get_manager_client(settings) as manager:
            all_entries = await manager.get_voicemail_users()
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to connect to Asterisk: {e}", "entries": [], "total": 0},
            status_code=503,
        )

    # Convert to list of dicts
    entries = [{"extension": mailbox, "name": name} for mailbox, name in all_entries]

    # Filter by search term
    if search:
        search_lower = search.lower()
        entries = [
            e
            for e in entries
            if search_lower in e["name"].lower() or search_lower in e["extension"].lower()
        ]

    # Sort entries
    reverse = order.lower() == "desc"
    if sort == "extension":
        entries.sort(key=lambda e: e["extension"], reverse=reverse)
    else:
        entries.sort(key=lambda e: e["name"].lower(), reverse=reverse)

    total = len(entries)
    paginated = entries[offset : offset + limit]

    return JSONResponse({
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": paginated,
    })


@router.get("/stats")
async def directory_stats(settings: AppSettings) -> JSONResponse:
    """Get directory statistics."""
    try:
        async with get_manager_client(settings) as manager:
            entries = await manager.get_voicemail_users()
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to connect to Asterisk: {e}"},
            status_code=503,
        )

    # Count entries with names
    named_count = sum(1 for _, name in entries if name)

    # Get first letter distribution
    letter_dist = {}
    for _, name in entries:
        if name:
            first = name[0].upper()
            letter_dist[first] = letter_dist.get(first, 0) + 1

    return JSONResponse({
        "total_entries": len(entries),
        "named_entries": named_count,
        "letter_distribution": dict(sorted(letter_dist.items())),
    })


@router.get("/export")
async def export_directory(
    settings: AppSettings,
    format: str = Query(default="csv", description="Export format: csv, vcard"),
) -> JSONResponse:
    """Export directory in various formats."""
    try:
        async with get_manager_client(settings) as manager:
            entries = await manager.get_voicemail_users()
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to connect to Asterisk: {e}"},
            status_code=503,
        )

    if format == "vcard":
        # Generate vCard 3.0 format
        vcards = []
        for mailbox, name in entries:
            if name:
                vcard = (
                    "BEGIN:VCARD\n"
                    "VERSION:3.0\n"
                    f"FN:{name}\n"
                    f"TEL;TYPE=WORK:{mailbox}\n"
                    "END:VCARD"
                )
                vcards.append(vcard)
        content = "\n".join(vcards)
        return JSONResponse({
            "format": "vcard",
            "content_type": "text/vcard",
            "filename": "directory.vcf",
            "content": content,
        })
    else:
        # CSV format
        lines = ["Extension,Name"]
        for mailbox, name in sorted(entries, key=lambda e: e[1]):
            # Escape quotes in name
            safe_name = name.replace('"', '""')
            lines.append(f'{mailbox},"{safe_name}"')
        content = "\n".join(lines)
        return JSONResponse({
            "format": "csv",
            "content_type": "text/csv",
            "filename": "directory.csv",
            "content": content,
        })
