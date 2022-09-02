FROM python:3.9-slim
## PIPFILES
WORKDIR /pipfiles

# INSTALL RUNTIME DEPS.
RUN apt-get update && \
    apt-get install -y --no-install-recommends git p7zip tar unrar-free xz-utils && \
    rm -rf /var/lib/apt/lists/*

# INSTALL REQUIREMENTS
COPY Pipfile* ./
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev libc-dev && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -U setuptools wheel pipenv && \
    pipenv install --dev --system && \
    apt-get remove -y gcc libpq-dev libc-dev && \
    apt-get autoremove -y

## FINAL
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
WORKDIR /app

# TINI INSTALLATION
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# ENTRYPOINT
COPY ./docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/tini", "--", "/entrypoint.sh"]

# COPY APP SOURCE CODE
COPY ./docker/* ./
COPY ./fastapi-permissions/fastapi_permissions ./fastapi_permissions
COPY ./db_adapters ./media_adapters ./api ./

ENV PROMETHEUS_MULTIPROC_DIR=/prometheus
RUN mkdir /prometheus

ENV PORT 3000
ENV GUNICORN_WORKERS 4
EXPOSE 3000
CMD ["serve"]
