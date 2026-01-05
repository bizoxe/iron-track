ARG BUILDER_IMAGE=python:3.12-slim-bookworm
ARG UV_INSTALL_ARGS="--all-extras --dev"

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

# Install essential build tools and uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    tini \
    curl \
    && apt-get autoremove -y && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# --- Stage 2: Builder (Install dependencies) ---
FROM python-base AS builder

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv venv && uv sync ${UV_INSTALL_ARGS} --frozen --no-install-project

# --- Stage 3: Development (Final Development Image) ---
FROM builder AS development

# Copy project files
COPY README.md .pre-commit-config.yaml LICENSE Makefile ./
COPY src ./src/

RUN uv sync ${UV_INSTALL_ARGS} --frozen

STOPSIGNAL SIGINT
EXPOSE 8000

ENTRYPOINT ["tini", "--"]

CMD ["app", "server", "dev", "--host", "0.0.0.0", "--port", "8000"]