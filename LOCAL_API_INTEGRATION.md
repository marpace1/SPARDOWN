# SPARDOWN Local API Integration Guide

## Overview

SPARDOWN is designed to run locally on a user's machine and expose a local REST API.

Applications, plugins, desktop software, browser extensions, and automation tools can communicate with SPARDOWN through localhost without requiring any public server.

---

# Architecture

```text
Application / Plugin
          ↓
http://localhost:8000
          ↓
SPARDOWN
          ↓
YouTube Search
          ↓
Download & Conversion
          ↓
MP3 Output
```

The third-party application sends requests to SPARDOWN and SPARDOWN handles all downloading, conversion, metadata tagging, and file management.

---

# Why Local API?

A local API provides:

* No hosting costs
* No server maintenance
* No bandwidth costs
* No public infrastructure
* Full user control
* Better privacy

Each user runs their own SPARDOWN instance.

---

# Installation

## Clone Repository

```bash
git clone https://github.com/marpace1/SPARDOWN.git
cd SPARDOWN
```

## Docker

```bash
docker compose up
```

or

## Python

```bash
pip install -r requirements.txt

python -m uvicorn main:app --reload
```

---

# Local Endpoint

Default address:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

# Authentication

Users configure their own API key inside:

```env
API_KEY=my_local_key
```

Example request:

```http
X-API-Key: my_local_key
```

The API key is local to the user's installation.

No external server is involved.

---

# Plugin Integration Example

## Step 1

Plugin retrieves song information:

```json
{
  "title": "Faded",
  "artist": "Alan Walker"
}
```

---

## Step 2

Plugin creates search query:

```text
Alan Walker Faded
```

---

## Step 3

Plugin sends request to SPARDOWN:

```http
POST http://localhost:8000/download
```

Request:

```json
{
  "query": "Alan Walker Faded"
}
```

---

## Step 4

SPARDOWN:

* Searches source
* Finds best match
* Downloads audio
* Converts to MP3
* Applies metadata
* Saves file

---

## Step 5

Plugin receives response:

```json
{
  "job_id": "123456",
  "status": "queued"
}
```

---

## Step 6

Plugin checks status:

```http
GET /jobs/123456
```

---

## Step 7

When completed:

```json
{
  "status": "completed"
}
```

Downloaded file becomes available in the configured downloads directory.

---

# Distribution Scenarios

## Scenario A: Developer Tool

User installs:

* SPARDOWN
* Plugin

User starts SPARDOWN manually.

Plugin communicates with:

```text
http://localhost:8000
```

---

## Scenario B: Desktop Application

SPARDOWN is bundled with a desktop application.

The application automatically launches SPARDOWN during startup.

Users do not need to manually start the backend.

Recommended for future Tauri-based implementations.

---

# Best Practices

* Never hardcode API keys.
* Allow users to configure API addresses.
* Use localhost by default.
* Check API availability before sending requests.
* Handle connection failures gracefully.

Example:

```text
Could not connect to SPARDOWN.
Please ensure SPARDOWN is running.
```

---

# Future Direction

A future SPARDOWN Desktop application may:

* Run in the system tray
* Start automatically with Windows
* Manage downloads through a GUI
* Expose the same localhost API

This would allow plugins and third-party applications to continue using the existing API without modification.

---

# Summary

SPARDOWN is intended to function as a local API service.

Third-party applications can communicate with SPARDOWN through localhost, allowing them to use downloading, conversion, metadata tagging, and file management features without implementing those systems themselves.
