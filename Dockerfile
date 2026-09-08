FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-core.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt \
    && pip install --no-cache-dir "torch>=2.2,<3" "torchvision>=0.17,<1" \
       --index-url https://download.pytorch.org/whl/cpu

COPY . .
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /data/uploads \
    && chown -R app:app /app /data

USER app

ENV DATABASE_URL=sqlite:////data/app.db \
    UPLOAD_DIR=/data/uploads \
    APP_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=3)"

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
