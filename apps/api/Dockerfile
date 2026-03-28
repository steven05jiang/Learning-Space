FROM python:3.12-slim

# Build argument to determine service type (api or worker)
ARG SERVICE_TYPE=api

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps, system Python)
RUN uv sync --frozen --no-dev --no-install-project

# Copy app source
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# Set Playwright browser path before install so browsers land in the right place
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install Playwright + deps for worker service (let install-deps resolve packages for the OS)
RUN if [ "$SERVICE_TYPE" = "worker" ]; then \
        /app/.venv/bin/playwright install-deps chromium \
        && /app/.venv/bin/playwright install chromium; \
    fi

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user (security best practice for both services)
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app \
    && chown -R app:app /ms-playwright 2>/dev/null || true

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 8000 for API service
EXPOSE 8000

# Use entrypoint script to handle service type logic
ENTRYPOINT ["/entrypoint.sh"]