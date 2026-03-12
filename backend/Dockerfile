FROM python:3.12-slim-bookworm

# Install system dependencies (WeasyPrint + Cairo + curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango1.0-dev \
    libcairo2-dev \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install ODA File Converter (pre-built DWG→DXF converter, replaces LibreDWG source build)
RUN curl -fsSL -o /tmp/oda.deb \
    "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb" \
    && (dpkg -i /tmp/oda.deb || true) \
    && apt-get update && apt-get install -f -y --no-install-recommends \
    && rm /tmp/oda.deb \
    && rm -rf /var/lib/apt/lists/*

# Headless mode for ODA's Qt6 GUI
ENV QT_QPA_PLATFORM=offscreen

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash app

WORKDIR /app

# Install dependencies (generate lockfile if not present)
COPY pyproject.toml ./
RUN uv lock && uv sync --no-dev

# Copy application code
COPY app/ ./app/

# Create upload/output directories with correct ownership.
# Named Docker volumes inherit permissions from the first container that uses them.
RUN mkdir -p /app/uploads /app/outputs \
    && chown -R app:app /app

# Switch to non-root user
USER app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
