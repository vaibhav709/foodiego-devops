# CareSync - hardened multi-stage image
FROM python:3.12-slim AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM builder AS test
RUN pip install --no-cache-dir pytest==8.3.4
COPY . .
RUN cp -r /install/* /usr/local/ && python -m pytest -q tests/

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# Patch OS packages, drop pip/setuptools from the runtime image and create an unprivileged user
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
 && pip uninstall -y pip setuptools wheel || true \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin caresync
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=root:root caresync ./caresync
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/healthz')"
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--worker-tmp-dir", "/tmp", "caresync:create_app()"]
