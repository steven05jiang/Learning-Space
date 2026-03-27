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

# Install additional dependencies for worker service (Playwright)
RUN if [ "$SERVICE_TYPE" = "worker" ]; then \
        apt-get update && apt-get install -y \
        curl wget gnupg ca-certificates \
        fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
        libcairo2 libcups2 libdbus-1-3 libdrm2 libgdk-pixbuf2.0-0 \
        libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 \
        libxcomposite1 libxdamage1 libxrandr2 libxss1 xdg-utils \
        && apt-get clean && rm -rf /var/lib/apt/lists/* \
        && playwright install chromium && playwright install-deps chromium; \
    fi

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

# Set environment for Playwright if it's worker service
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

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