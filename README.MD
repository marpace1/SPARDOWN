#  SPARDOWN

SPARDOWN is a FastAPI-powered music search and download service that allows users to search tracks, fetch YouTube sources, download audio, convert to MP3, and manage download history through a REST API.

---

##  Features

-  Music Search
-  YouTube Audio Downloads
-  Automatic MP3 Conversion
-  Metadata Tagging
-  Download History
-  Usage Statistics
-  Background Job Queue
-  API Key Authentication
-  Rate Limiting
-  Download Management

---

## 🏗 Architecture

```
Client
   │
   ▼
FastAPI API
   │
   ▼
Job Queue
   │
   ▼
YouTube Search
   │
   ▼
yt-dlp
   │
   ▼
FFmpeg Conversion
   │
   ▼
MP3 Output
```

---

## 📦 Requirements

- Python 3.11+
- FFmpeg
- Git

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/marpace1/SPARDOWN.git
cd SPARDOWN
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate Environment

Windows:

```bash
.venv\Scripts\activate
```

Linux/Mac:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file:

```env
API_KEY=your_api_key
DATABASE_URL=sqlite:///spardown.db
DOWNLOAD_PATH=downloads
```

### Install FFmpeg

Ensure FFmpeg is available in PATH.

Verify:

```bash
ffmpeg -version
```

---

## ▶ Running SPARDOWN

```bash
uvicorn main:app --reload
```

Server:

```
http://127.0.0.1:8000
```

Swagger Documentation:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

---

# API Documentation

## Authentication

Include API key:

```http
X-API-Key: your_api_key
```

---

## Search Track

### Request

```http
GET /api/search?q=alan walker faded
```

### Example Response

```json
{
  "success": true,
  "results": [
    {
      "title": "Alan Walker - Faded",
      "artist": "Alan Walker",
      "duration": 212
    }
  ]
}
```

---

## Download Track

### Request

```http
POST /api/download
```

### Body

```json
{
  "query": "Alan Walker Faded"
}
```

### Example Response

```json
{
  "job_id": "123456",
  "status": "queued"
}
```

---

## Job Status

### Request

```http
GET /api/jobs/{job_id}
```

### Example Response

```json
{
  "job_id": "123456",
  "status": "completed",
  "progress": 100
}
```

---

## Download File

### Request

```http
GET /api/downloads/{file_id}
```

### Example Response

Returns MP3 file.

---

## History

### Request

```http
GET /api/history
```

### Example Response

```json
{
  "downloads": [
    {
      "title": "Alan Walker - Faded",
      "downloaded_at": "2026-06-14T18:30:00"
    }
  ]
}
```

---

## Statistics

### Request

```http
GET /api/stats
```

### Example Response

```json
{
  "total_downloads": 25,
  "successful_downloads": 24,
  "failed_downloads": 1
}
```

---

# Project Structure

```text
SPARDOWN/
├── main.py
├── requirements.txt
├── README.md
├── downloads/
├── tests/
├── .env
├── spardown.db
└── SPARDOWN/
```

---

# Known Limitations

- Depends on YouTube availability.
- Search quality depends on source metadata.
- Very large playlists may take longer to process.
- Regional restrictions may affect some content.
- Download speed depends on network conditions.

---

# Roadmap

## Version 1.1

- Playlist Downloads
- Album Downloads
- Bulk Downloads
- Better Metadata Matching

## Version 1.2

- WebSocket Progress Updates
- User Accounts
- Download Scheduling

## Version 2.0

- Desktop App (Tauri)
- Modern GUI
- Multi-platform Packaging

---

# Contributing

Contributions are welcome.

1. Fork repository
2. Create feature branch
3. Commit changes
4. Open pull request

---

# License

MIT License

---

# Disclaimer

This project is intended for educational and personal use. Users are responsible for complying with applicable copyright laws and platform terms of service.
