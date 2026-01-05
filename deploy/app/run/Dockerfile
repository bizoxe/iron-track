ARG BUILDER_IMAGE=python:3.12-slim-bookworm

# --- Stage 1: Base (Environment & System) ---
FROM ${BUILDER_IMAGE} AS python-base

ENV PATH="/workspace/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /workspace/app

# System updates and essential runtime packages
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends tini \
    && apt-get autoremove -y && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* /root/.cache \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# --- Stage 2: Builder (Compilation & Assembly) ---
FROM python-base AS builder

# Build-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
    && apt-get autoremove -y && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false

COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv venv && uv sync --frozen --no-install-project --no-default-groups --no-editable

# Build the application wheel
COPY src ./src/
COPY README.md LICENSE Makefile ./
RUN uv build --wheel

# --- Stage 3: Runner (Final Production Image) ---
FROM python-base AS runner

WORKDIR /workspace/app

# Security: Create non-root user and required directories
RUN addgroup --system --gid 1000 appgroup \
    && adduser --no-create-home --system --uid 1000 --ingroup appgroup appuser \
    && mkdir -p /run/app /workspace/app \
    && chown -R 1000:1000 /run/app /workspace

# Copy virtualenv and built wheel from builder
COPY --from=builder --chown=1000:1000 /workspace/app/.venv /workspace/app/.venv
COPY --from=builder --chown=1000:1000 /workspace/app/dist /tmp/dist

# Install the wheel and cleanup
RUN uv pip install --no-deps /tmp/dist/*.whl && rm -rf /tmp/dist

USER appuser

# Granian configuration
ENV GRANIAN_INTERFACE=asgi \
    GRANIAN_LOOP=auto \
    GRANIAN_TASK_IMPL=asyncio

STOPSIGNAL SIGINT
ENTRYPOINT ["tini", "--"]

CMD ["granian", "--uds", "/run/app/granian.sock", "--uds-permissions", "438", "app.main:app"]