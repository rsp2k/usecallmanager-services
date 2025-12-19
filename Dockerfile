# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.5-python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies first (better layer caching)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy source and install package
COPY src/ src/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-editable --no-dev


FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy static files
COPY --chown=appuser:appuser phone_help.xml config.yml ./

# Create reports directory
RUN mkdir -p /var/log/cisco && chown appuser:appuser /var/log/cisco

# Set environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:6972/')" || exit 1

EXPOSE 6972

CMD ["usecallmanager-services"]
