# ADR-0026: Containerize Crow Health deployment

## Context

Crow Health now has a read-only FastAPI interface and authenticated Apple Health manifest intake, but the repository has not yet defined a repeatable server deployment. The Debian host prepared for Crow Health separates application files under `/opt/crow/health` from persistent data under `/srv/crow-data/health`.

A deployment contract is needed before the service is started as a long-lived server process. The contract must not move persistence into the container filesystem or introduce unrelated infrastructure.

## Decision

Crow Health will be deployed as a single Docker Compose service built from the repository `Dockerfile`.

The container runs the existing `crow_health.api:app` using Uvicorn on port 8000. Uvicorn is an explicit runtime dependency.

Persistent Crow Health paths are bind-mounted from `/srv/crow-data/health`. The observation store, observation index and Apple Health manifest archive therefore survive image rebuilds and container replacement.

The Compose service runs as a configurable numeric UID/GID, defaulting to `1000:1000`, so host file ownership remains explicit. The API binds to loopback by default and requires an explicit configuration change before it is reachable from another host.

The deployment includes a health check against the existing `/health` endpoint and uses `restart: unless-stopped`.

Secrets are not committed. The Apple Health manifest bearer token is supplied only through the local deployment environment.

## Consequences

Crow Health can be reproduced on the prepared Debian Docker host without installing Python packages directly into the host operating system.

Application deployment and persistent health data remain separated. Rebuilding or replacing the container does not delete the bind-mounted evidence and observation data.

The container deployment does not provide TLS termination, reverse proxying, general API authentication, automatic backups, PostgreSQL, automatic Garmin retrieval or Apple Health background collection. These remain separate decisions and must not be inferred from this deployment pass.

The container deployment is not considered operationally verified merely because Python CI passes. A real Docker image build, Compose start and `/health` check on the target Debian host are required as deployment evidence.
