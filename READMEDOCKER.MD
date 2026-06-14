# 🐳 Docker Support

SPARDOWN can be run using Docker, eliminating the need to manually install Python dependencies, FFmpeg, or configure the runtime environment.

## Prerequisites

Install:

* Docker
* Docker Compose

Verify installation:

```bash
docker --version
docker compose version
```

---

## Configure Environment

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit the values as needed.

---

## Build the Docker Image

```bash
docker compose build
```

This will:

* Install Python dependencies
* Install FFmpeg
* Copy the SPARDOWN source code
* Create the application image

---

## Start SPARDOWN

```bash
docker compose up
```

Or run in the background:

```bash
docker compose up -d
```

---

## Access the API

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

## View Logs

```bash
docker compose logs -f
```

---

## Stop SPARDOWN

```bash
docker compose down
```

---

## Rebuild After Code Changes

```bash
docker compose down
docker compose build
docker compose up -d
```

---

## Persistent Downloads

Downloaded files are stored in the local `downloads` directory and remain available even after the container is restarted.

---

## Troubleshooting

### Container Fails to Start

Check logs:

```bash
docker compose logs
```

### Port Already In Use

Change the port mapping inside:

```yaml
docker-compose.yml
```

Example:

```yaml
ports:
  - "8080:8000"
```

Then access:

```text
http://localhost:8080/docs
```

### Verify Running Containers

```bash
docker ps
```

You should see the SPARDOWN container listed and running.
