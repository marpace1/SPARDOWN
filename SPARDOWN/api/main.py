

from SPARDOWN.core.security import hash_api_key
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from SPARDOWN.database.session import db
from SPARDOWN.downloaders.yt_dlp import YtDlpDownloader
from SPARDOWN.workers.queue import QueueManager
from SPARDOWN.services.download_service import DownloadService
from SPARDOWN.services.matching_service import MatchingService
from SPARDOWN.services.cache_service import MetadataCacheService
from SPARDOWN.repositories.repos import ApiKeyRepository
from SPARDOWN.services.providers.provider_manager import ProviderManager
from fastapi.responses import FileResponse
from datetime import datetime
import asyncio
from SPARDOWN.config.settings import settings
from SPARDOWN.models.models import JobStatus
from SPARDOWN.services.cleanup_service import CleanupService
from SPARDOWN.repositories.repos import JobRepository
from SPARDOWN.core.logging import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    status,
    WebSocket,
    WebSocketDisconnect,
    Header
)
import secrets

app = FastAPI(title="SPARDOWN API", version="1.0.0")

MAX_ACTIVE_JOBS_PER_USER = 5


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Connection Manager for WebSockets ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, job_id: int, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, job_id: int, websocket: WebSocket):
        if job_id in self.active_connections:
            try:
                self.active_connections[job_id].remove(websocket)
            except ValueError:
                pass

    async def broadcast(self, job_id: int, message: dict):
        if job_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError):
                    disconnected.append(connection)
            
            for conn in disconnected:
                self.disconnect(job_id, conn)

manager = ConnectionManager()

async def get_db():
    async with await db.get_session() as session:
        yield session

async def get_service(session: AsyncSession = Depends(get_db)):
    return app.state.download_service

async def verify_admin(
    x_admin_key: str = Header(None)
):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )


async def cleanup_worker():
    from SPARDOWN.services.cleanup_service import CleanupService

    cleanup = CleanupService()

    while True:
        try:
            await cleanup.cleanup_old_files()
        except Exception as e:
            print(f"[Cleanup Worker] Error: {e}")

        await asyncio.sleep(3600)  # 1 hour
        
async def get_api_key(
    x_api_key: str = Header(None),
    session: AsyncSession = Depends(get_db)
):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    repo = ApiKeyRepository(session)

    try:
        hashed_key = hash_api_key(x_api_key)
        api_key = await repo.get_by_id(hashed_key)
    except Exception:
        api_key = None

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=403,
            detail="API key disabled"
        )

    if api_key.requests_today >= api_key.daily_limit:
        raise HTTPException(
            status_code=429,
            detail="Daily API limit reached"
        )

    api_key.requests_today += 1
    api_key.requests_total += 1
    api_key.last_used = datetime.utcnow()

    await session.commit()

    return api_key

# --- Pydantic Models ---
class JobCreate(BaseModel):
    url: str = Field(
        ...,
        example="The Weeknd Blinding Lights"
    )

    job_type: str = Field(
        "search",
        pattern="^(search|youtube)$"
    )

class JobResponse(BaseModel):
    id: int
    status: str
    progress: float
    current_track: Optional[int]
    total_tracks: Optional[int]
    download_speed: Optional[float]
    eta: Optional[float]
    error: Optional[str]

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "healthy",
        "queue": "healthy",
        "providers": {
            "spotify_api": "credentials_missing",
            "spotify_page": "available",
            "musicbrainz": "available"
        }
    }
@app.post("/apikeys/create")
async def create_api_key(
    owner: str,
    session: AsyncSession = Depends(get_db),
    admin=Depends(verify_admin)
):
    repo = ApiKeyRepository(session)

    
    
    raw_key = secrets.token_urlsafe(48)
    
    hashed_key = hash_api_key(raw_key)

    await repo.create(
        key=hashed_key,
        owner=owner,
        is_active=True,
        requests_today=0,
        requests_total=0,
        daily_limit=100
    )
    
    logger.info(
    f"API key created for owner={owner}")

    return {
        "api_key": raw_key,
        "owner": owner,
        "daily_limit": 100
    }
    


@app.get("/apikeys")
async def list_api_keys(
    session: AsyncSession = Depends(get_db)
):
    repo = ApiKeyRepository(session)

    keys = await repo.list_all()

    return [
        {
            "owner": k.owner,
            "active": k.is_active,
            "requests_today": k.requests_today,
            "requests_total": k.requests_total
        }
        for k in keys
    ]


@app.delete("/apikeys/{key}")
async def delete_api_key(
    key: str,
    session: AsyncSession = Depends(get_db)
):
    repo = ApiKeyRepository(session)

    hashed_key = hash_api_key(key)

    existing = await repo.get_by_id(hashed_key)

    if not existing:
        raise HTTPException(
            status_code=404,
            detail="API key not found"
        )

    await repo.delete(hashed_key)

    return {"detail": "API key deleted"}

@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    api_key=Depends(get_api_key),
    service: DownloadService = Depends(get_service)
):
    async with service.session_factory() as session:
        job_repo = JobRepository(session)

        jobs = await job_repo.list_all()

        active_jobs = [
            j for j in jobs
            if getattr(j, "owner_key", "") == api_key.key
            and j.status in [
                JobStatus.PENDING,
                JobStatus.EXTRACTING,
                JobStatus.MATCHING,
                JobStatus.DOWNLOADING,
                JobStatus.TAGGING
            ]
        ]

        if len(active_jobs) >= MAX_ACTIVE_JOBS_PER_USER:
            raise HTTPException(
                status_code=429,
                detail="Too many active jobs"
            )

    job_id = await service.create_download_job(
        payload.url,
        payload.job_type,
        api_key.key
    )
    logger.info(
    f"Job {job_id} created by owner={api_key.owner}"
)

    return await service.get_job_status(job_id)

@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    api_key=Depends(get_api_key),
    service: DownloadService = Depends(get_service)
):
    async with service.session_factory() as session:
        job_repo = JobRepository(session)

        job = await job_repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
            
        if job.owner_key != api_key.key:
            logger.warning(
                f"Unauthorized access attempt "
                f"job={job_id} owner={api_key.owner}"
            )

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    return await service.get_job_status(job_id)


@app.get("/jobs")
async def list_jobs(
    api_key=Depends(get_api_key),
    service: DownloadService = Depends(get_service)
):
    return await service.list_downloads()


@app.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: int,
    api_key=Depends(get_api_key),
    service: DownloadService = Depends(get_service)
):
    async with service.session_factory() as session:
        job_repo = JobRepository(session)

        job = await job_repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        if job.owner_key != api_key.key:
            logger.warning(
                f"Unauthorized access attempt "
                f"job={job_id} owner={api_key.owner}"
            )

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    await service.cancel_job(job_id)
    logger.info(
    f"Job {job_id} cancelled by owner={api_key.owner}"
)

    return {"detail": "Job cancelled"}

@app.get("/history")
async def get_history(
    api_key=Depends(get_api_key),
    session: AsyncSession = Depends(get_db)
):
    from SPARDOWN.repositories.repos import (
        TrackRepository,
        JobRepository
    )

    track_repo = TrackRepository(session)
    job_repo = JobRepository(session)

    tracks = await track_repo.list_all()

    user_tracks = []

    for track in tracks:
        job = await job_repo.get_by_id(track.job_id)

        if job and job.owner_key == api_key.key:
            user_tracks.append(
                {
                    "title": track.title,
                    "artist": track.artist,
                    "path": track.file_path
                }
            )

    return user_tracks

@app.get("/stats")
async def stats(
    api_key=Depends(get_api_key),
    service: DownloadService = Depends(get_service)
):
    jobs = await service.list_downloads()

    return {
        "total_jobs": len(jobs),
        "completed": len(
            [j for j in jobs if j["status"] == "completed"]
        ),
        "failed": len(
            [j for j in jobs if j["status"] == "failed"]
        ),
        "active": len(
            [
                j for j in jobs
                if j["status"] not in [
                    "completed",
                    "failed"
                ]
            ]
        )
    }
    
@app.get("/downloads/{job_id}")
async def download_file(
    job_id: int,
    api_key=Depends(get_api_key),
    session: AsyncSession = Depends(get_db)
):
    from SPARDOWN.repositories.repos import (
        TrackRepository,
        JobRepository
    )

    job_repo = JobRepository(session)

    job = await job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    if job.owner_key != api_key.key:
            logger.warning(
                f"Unauthorized access attempt "
                f"job={job_id} owner={api_key.owner}"
            )

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    repo = TrackRepository(session)

    tracks = await repo.list_all()

    for track in tracks:
        if (
            track.job_id == job_id
            and track.file_path
        ):
            downloads_root = Path("downloads").resolve()
            return FileResponse(
                path=track.file_path,
                filename=f"{track.title}.mp3"
            )

    raise HTTPException(
        status_code=404,
        detail="File not found"
    )

@app.websocket("/ws/jobs/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: int):
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)

@app.on_event("startup")

async def startup_event():
    cleanup = CleanupService()
    await cleanup.cleanup_old_files()
    app.state.cleanup_task = asyncio.create_task(
    cleanup_worker())
    await db.init_db()
    app.state.queue_manager = QueueManager(concurrency=3)
    downloader = YtDlpDownloader()
    
    # New Provider Manager replaces SpotifyService
    provider_manager = ProviderManager()
    matcher = MatchingService(downloader)
    
    app.state.download_service = DownloadService(
        session_factory=db.session_factory,
        downloader=downloader,
        queue_manager=app.state.queue_manager,
        provider_manager=provider_manager,
        matching_service=matcher,
        cache_service_factory=lambda s: MetadataCacheService(s),
        ws_manager=manager
    )
    
    await app.state.queue_manager.start(worker_func=app.state.download_service.process_job)

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "cleanup_task"):
        app.state.cleanup_task.cancel()
    await app.state.queue_manager.stop()
