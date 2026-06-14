# SPARDOWN - Production-Grade Music Downloader Backend

SPARDOWN is a modular, service-oriented Python application designed to handle music downloads at scale. It is built from the ground up to be exposed as a REST API.

## 🏗 Architecture

The project follows a layered architecture to ensure maintainability and scalability:

- **API Layer (Future):** Intended to be a FastAPI wrapper around the Service layer.
- **Service Layer (`services/`):** Contains the business logic. All operations (creating jobs, checking status) are encapsulated here.
- **Repository Layer (`repositories/`):** Abstracts database access. Uses the Repository pattern to allow easy migration from SQLite to PostgreSQL.
- **Downloader Layer (`downloaders/`):** An abstraction layer for download engines. Currently implements `yt-dlp`.
- **Worker Layer (`workers/`):** A queue-based background processing system to handle concurrent downloads without blocking the main thread.
- **Storage Layer (`storage/`):** Manages file system organization, sanitization, and duplicate detection.

## 🚀 Key Features

- **Asynchronous Core:** Built with `asyncio` and `sqlalchemy[asyncio]` for high performance.
- **Job Management:** Full lifecycle tracking of downloads (Pending $\rightarrow$ Queued $\rightarrow$ Downloading $\rightarrow$ Completed/Failed).
- **Metadata Embedding:** Automatic ID3 tagging and cover art embedding using `mutagen`.
- **Modular Design:** Dependency injection used throughout to allow easy swapping of components.
- **Cross-Platform:** Works on Windows, Linux, and macOS.

## 🛠 Setup & Installation

1. **Install Dependencies:**
   ```bash
   pip install -r SPARDOWN/requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file or set the following variables:
   - `DATABASE_URL`: SQLite or PostgreSQL connection string.
   - `BASE_DOWNLOAD_PATH`: Path where music should be saved.
   - `MAX_CONCURRENT_DOWNLOADS`: Number of parallel worker threads.

3. **Run the Application:**
   ```bash
   python SPARDOWN/main.py
   ```

## 📁 Project Structure

```text
SPARDOWN/
├── api/            # API Route definitions (FastAPI)
├── core/           # Logging, Exceptions, Global Constants
├── database/       # DB Session and Engine management
├── models/         # SQLAlchemy DB Models
├── repositories/   # Data Access Layer (Repository Pattern)
├── services/       # Business Logic (Service Layer)
├── workers/        # Queue and Background Worker logic
├── downloaders/    # Download Engine implementations
├── storage/        # File System & Cache management
├── utils/          # Helper utilities
└── main.py         # Entry point / Integration test
```

## 🛣 Future API Roadmap

The `DownloadService` is designed to be mapped directly to FastAPI endpoints:

- `POST /jobs` $\rightarrow$ `DownloadService.create_download_job(url)`
- `GET /jobs/{id}` $\rightarrow$ `DownloadService.get_job_status(id)`
- `DELETE /jobs/{id}` $\rightarrow$ `DownloadService.cancel_job(id)`
- `GET /history` $\rightarrow$ `DownloadService.list_downloads()`
