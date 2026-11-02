# FoodieGo - multi-stage image: builder -> test -> slim runtime
FROM python:3.12-slim AS builder
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM builder AS test
RUN pip install --no-cache-dir pytest==8.3.4
COPY . .
RUN cp -r /install/* /usr/local/ && python -m pytest -q tests/

FROM python:3.12-slim AS runtime
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin foodie
COPY --from=builder /install /usr/local
WORKDIR /app
COPY foodiego ./foodiego
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-tmp-dir", "/dev/shm", "foodiego:create_app()"]
