"""CLI entry point for usecallmanager-services."""

import uvicorn


def main() -> None:
    """Run the application with uvicorn."""
    try:
        from importlib.metadata import version

        package_version = version("usecallmanager-services")
    except Exception:
        package_version = "2024.12.19"

    print(f"Cisco IP Phone XML Services v{package_version}")

    from .config import get_settings

    settings = get_settings()

    uvicorn.run(
        "usecallmanager_services.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
