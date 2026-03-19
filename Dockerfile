# ------------- Builder Stage -------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS builder

WORKDIR /app

# Copy dependency files do NOT try to install the project (sources aren’t here yet)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev --no-install-project

# ------------- Runtime Stage -------------
FROM python:3.13-slim AS runtime

# Security: Install only runtime security updates
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Runtime environment with security settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CONTEXT=/ \
    PORT=8080


# Security: Create restricted non-root user with minimal permissions
RUN groupadd --system --gid 1001 calibo \
    && useradd --system --uid 1001 --gid calibo \
    --home-dir /app --no-create-home \
    --shell /usr/sbin/nologin calibo

# Set working directory with proper permissions
WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Make sure to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=calibo:calibo src ./src
COPY --chown=calibo:calibo knowledge ./knowledge

# Create directories that the app might need to write to
RUN mkdir -p /app/.local /app/.cache \
    && chown -R calibo:calibo /app/.local /app/.cache

# ✅ Add this so /app itself is writable for report.md
RUN chown -R calibo:calibo /app

# Security: Set restrictive file permissions
RUN chmod -R 755 /app \
    && chmod -R 755 /app/src \
    && chmod -R 755 /app/knowledge \
    && chmod -R 755 /app/.venv \
    && chmod -R 755 /app/.local \
    && chmod -R 755 /app/.cache \
    && find /app/src -name "*.py" -exec chmod 644 {} \;

# Security: Clean up
RUN apt-get autoremove -y \
    && apt-get autoclean \
    && rm -rf /var/cache/apt/* \
    && rm -rf /usr/share/doc/* \
    && rm -rf /usr/share/man/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Switch to non-root user
USER calibo

# Security: Use dumb-init to handle signals properly and gunicorn security settings
ENTRYPOINT ["tini", "--"]
# Default command with security considerations
CMD ["python", "-m", "latest_ai_development.main"]


