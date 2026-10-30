# The API and the dashboard in one image: the API serves the compiled dashboard.
# The build context is the project root.

FROM node:24-alpine AS dashboard
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Type-checks the app and its tests, then builds it into /build/dist.
RUN npm run build


FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:$PATH"

# The code looks for the dashboard in ../frontend/dist and the demo emails in ../demo, so the
# three folders keep the same layout as in the repository.
WORKDIR /app/backend
# The dependencies come first, so changing the code does not install them again.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/alembic.ini ./
COPY backend/migrations ./migrations
COPY backend/app ./app
COPY demo /app/demo
COPY --from=dashboard /build/dist /app/frontend/dist

RUN useradd --system --no-create-home app
USER app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/config', timeout=2)"

# One worker: the scheduler and the on-demand run lock live in the memory of the process.
CMD ["sh", "-c", "alembic upgrade head && exec fastapi run --host 0.0.0.0 --port 8000"]
