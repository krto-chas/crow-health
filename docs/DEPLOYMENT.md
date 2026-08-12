# Crow Health container deployment

This deployment keeps application code under `/opt/crow/health` and persistent health data under `/srv/crow-data/health`.

## Host prerequisites

- Debian server with Docker Engine and the Docker Compose plugin.
- `/srv/crow-data/health/observations`
- `/srv/crow-data/health/evidence`
- `/srv/crow-data/health/exports`
- `/srv/crow-data/health/backups`
- The host account running Docker must be able to write the Crow Health data directories.

## First deployment

Clone the repository into the deployment root:

```bash
cd /opt/crow/health
git clone https://github.com/krto-chas/crow-health.git crow-health
cd crow-health
```

Create the local environment file:

```bash
cp .env.example .env
```

Determine the host UID and GID used for persistent writes:

```bash
id -u
id -g
```

Set `CROW_HEALTH_UID` and `CROW_HEALTH_GID` in `.env` to those values. The defaults are `1000:1000`.

The API binds to `127.0.0.1` by default. If a trusted LAN client must connect directly, set `CROW_HEALTH_BIND_ADDRESS` to the Debian server LAN address. Do not expose the service directly to the public Internet. TLS and general API authentication are outside this pass.

If Apple Health manifest intake is intentionally enabled, set a strong `CROW_HEALTH_APPLE_MANIFEST_TOKEN` in `.env`. Do not commit `.env`.

Build and start:

```bash
docker compose build
docker compose up -d
```

Verify:

```bash
docker compose ps
docker compose logs --tail=100 crow-health
curl http://127.0.0.1:8000/health
```

When a LAN bind address is configured, replace `127.0.0.1` with that address for the external verification request.

## Persistent paths

The container uses these host-backed paths:

```text
/srv/crow-data/health/observations/observations.jsonl
/srv/crow-data/health/observations/observations.index.jsonl
/srv/crow-data/health/evidence/apple-health-manifests/
```

Removing or rebuilding the container does not remove those files.

## Updating

After a reviewed change has been merged:

```bash
cd /opt/crow/health/crow-health
git pull --ff-only
docker compose build --pull
docker compose up -d
```

Then repeat the health and log checks before considering the deployment updated.

## Stopping

```bash
docker compose down
```

`docker compose down` removes the container and network but not the bind-mounted Crow Health data under `/srv/crow-data/health`.

## Evidence boundary

This deployment does not add a database, reverse proxy, TLS termination, general API authentication, automatic backup, automatic Garmin retrieval or background Apple Health collection. Those remain separate, reviewable concerns.
