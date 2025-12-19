"""FastAPI dependencies for phone detection and configuration."""

import re
from typing import Annotated

from fastapi import Depends, Header

from .config import Settings, get_settings


def is_79xx_phone(
    x_ciscoipphonemodelname: Annotated[str | None, Header()] = None,
) -> bool:
    """Detect if request is from a 7900 series phone.

    Checks the X-CiscoIPPhoneModelName header for pattern CP-79*.
    """
    if x_ciscoipphonemodelname:
        return bool(re.match(r"^CP-79", x_ciscoipphonemodelname))
    return False


def validate_device_name(device_name: str) -> bool:
    """Validate Cisco device name format (SEP + 12 hex chars)."""
    return bool(re.match(r"^SEP[0-9A-F]{12}$", device_name))


# Type aliases for dependency injection
Is79xx = Annotated[bool, Depends(is_79xx_phone)]
AppSettings = Annotated[Settings, Depends(get_settings)]
