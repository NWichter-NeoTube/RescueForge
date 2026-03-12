# Stage 1: Build LibreDWG from source
FROM python:3.12-slim-bookworm AS libredwg-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential autoconf automake libtool texinfo \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --recurse-submodules https://github.com/LibreDWG/libredwg.git /tmp/libredwg \
    && cd /tmp/libredwg \
    && git submodule update --init --recursive \
    && autoreconf -fi \
    && ./configure --prefix=/usr/local --disable-bindings --disable-write \
    && make -j2 \
    && make install

# Stage 2: Final image
FROM python:3.12-slim-bookworm

# Copy LibreDWG binaries
COPY --from=libredwg-builder /usr/local/bin/dwg2dxf /usr/local/bin/dwg2dxf
COPY --from=libredwg-builder /usr/local/bin/dwgread /usr/local/bin/dwgread
COPY --from=libredwg-builder /usr/local/lib/libredwg* /usr/local/lib/
RUN ldconfig

# Install system dependencies (WeasyPrint + Cairo + curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango1.0-dev \
    libcairo2-dev \
    libgdk-pixbuf-2.0-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

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
