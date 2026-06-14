from typing import List, Dict, Any, Optional, Callable
from SPARDOWN.repositories.repos import JobRepository, TrackRepository
from SPARDOWN.downloaders.base import BaseDownloader, TrackMetadata
from SPARDOWN.storage.manager import storage_manager
from SPARDOWN.models.models import JobStatus, DownloadJob, Track
from SPARDOWN.workers.queue import QueueManager
from SPARDOWN.core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.services.matching_service import MatchingService
from SPARDOWN.services.cache_service import MetadataCacheService
from SPARDOWN.services.providers.provider_manager import ProviderManager
from dataclasses import asdict
from datetime import datetime
from dataclasses import dataclass

class PlaylistProcessor:
    def __init__(self, service: 'DownloadService'):
        self.service = service

    async def process(self, session: AsyncSession, job_id: int, spotify_tracks: List[SpotifyTrackMetadata]):
        total = len(spotify_tracks)
        chunk_size = 20
        for i in range(0, total, chunk_size):
            job_repo = JobRepository(session)
            job = await job_repo.get_by_id(job_id)
            if not job or job.status == JobStatus.CANCELLED:
                return
            chunk = spotify_tracks[i:i+chunk_size]
            for idx, s_track in enumerate(chunk, i + 1):
                await self.service.process_single_spotify_track(session, job_id, s_track, idx, total)
@dataclass
class SearchTrack:
    title: str
    artist: str = "Unknown"
    album: str = "Unknown"
    duration_ms: int = 0
class DownloadService:
    
    def __init__(
        self, 
        session_factory: async_sessionmaker, 
        downloader: BaseDownloader, 
        queue_manager: QueueManager,
        provider_manager: ProviderManager,
        matching_service: MatchingService,
        cache_service_factory: Callable[[AsyncSession], MetadataCacheService],
        ws_manager: Any = None
    ):
        self.session_factory = session_factory
        self.downloader = downloader
        self.queue_manager = queue_manager
        self.provider_manager = provider_manager
        self.matcher = matching_service
        self.cache_factory = cache_service_factory
        self.ws_manager = ws_manager

    async def _update_job_progress(self, session: AsyncSession, job_id: int, **kwargs):
        job_repo = JobRepository(session)
        await job_repo.update(job_id, **kwargs)
        if self.ws_manager:
            job = await job_repo.get_by_id(job_id)
            if job:
                await self.ws_manager.broadcast(job_id, {
                    "id": job.id, "status": job.status.value, "progress": job.progress,
                    "current_track": job.current_track, "total_tracks": job.total_tracks,
                    "error": job.error_message
                })

    async def create_download_job(
        self,
        url: str,
        job_type: str = "track",
        owner_key: str = ""
    ) -> int:

        async with self.session_factory() as session:
            job_repo = JobRepository(session)

            job = await job_repo.create(
                url=url,
                job_type=job_type,
                status=JobStatus.PENDING,
                owner_key=owner_key
            )

            await self.queue_manager.add_job(job.id)

            return job.id


    async def get_job_status(self, job_id: int) -> Dict[str, Any]:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            job = await job_repo.get_by_id(job_id)
            if not job: raise ValueError("Job not found")
            return {
                "id": job.id, "status": job.status.value, "progress": job.progress,
                "current_track": job.current_track, "total_tracks": job.total_tracks,
                "download_speed": job.download_speed, "eta": job.eta, "error": job.error_message
            }

    async def cancel_job(self, job_id: int) -> bool:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            return await job_repo.update(job_id, status=JobStatus.CANCELLED) != None

    async def list_downloads(self) -> List[Dict[str, Any]]:
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.list_all()
            return [{"id": j.id, "status": j.status.value, "url": j.url, "progress": j.progress} for j in jobs]

    async def process_job(self, job_id: int):
        async with self.session_factory() as session:
            job_repo = JobRepository(session)
            job = await job_repo.get_by_id(job_id)

            if not job or job.status == JobStatus.CANCELLED:
                return

            try:
                await self._update_job_progress(
                    session,
                    job_id,
                    status=JobStatus.EXTRACTING
                )

                if job.job_type in ["search", "youtube"]:
                    spotify_tracks = [
                        SearchTrack(
                            title=job.url
                        )
                    ]
                else:
                    raise ValueError(
                        "Unsupported job type. Use 'search' or 'youtube'."
                    )

                await self._update_job_progress(
                    session,
                    job_id,
                    total_tracks=len(spotify_tracks)
                )

                processor = PlaylistProcessor(self)

                await processor.process(
                    session,
                    job_id,
                    spotify_tracks
                )

                await self._update_job_progress(
                    session,
                    job_id,
                    status=JobStatus.COMPLETED,
                    progress=100.0
                )

            except Exception as e:
                logger.error(
                    f"Error processing job {job_id}: {e}"
                )

                await self._update_job_progress(
                    session,
                    job_id,
                    status=JobStatus.FAILED,
                    error_message=str(e)
                )



    async def process_single_spotify_track(
        self,
        session: AsyncSession,
        job_id: int,
        s_track,
        index: int,
        total: int
    ):
        track_repo = TrackRepository(session)

        await self._update_job_progress(
            session,
            job_id,
            status=JobStatus.MATCHING,
            current_track=index
        )

        if str(s_track.title).startswith("http"):
            download_url = s_track.title
        else:
            download_url = f"ytsearch1:{s_track.title}"

        confidence = 1.0

        await self._update_job_progress(
            session,
            job_id,
            status=JobStatus.DOWNLOADING
        )

        safe_title = str(s_track.title).replace("/", "-")

        path = str(
            storage_manager.get_download_path(
                "Search",
                "Downloads",
                safe_title
            )
        )

        if path.endswith(".mp3"):
            path = path[:-4]


        import asyncio

        loop = asyncio.get_running_loop()

        def update_progress(p):
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(
                    self._update_realtime_progress(
                        job_id,
                        p,
                        index,
                        total
                    )
                )
            )

        success = await self.downloader.download(
            download_url,
            str(path),
            progress_callback=update_progress
        )

        if success:
            await self._update_job_progress(
                session,
                job_id,
                status=JobStatus.TAGGING
            )

            final_path = str(path) + ".mp3"

            await self.downloader.embed_metadata(
                final_path,
                TrackMetadata(
                    title=s_track.title,
                    artist=s_track.artist,
                    album=s_track.album,
                    duration=s_track.duration_ms / 1000,
                    source_url=download_url
                )
            )

            await track_repo.create(
                job_id=job_id,
                title=s_track.title,
                artist=s_track.artist,
                album=s_track.album,
                duration=s_track.duration_ms / 1000,
                source_url=download_url,
                source_platform="youtube",
                match_confidence=confidence,
                file_path=final_path,
                downloaded_at=datetime.utcnow()
            )


            await self._update_job_progress(
                session,
                job_id,
                progress=(index / total) * 100
            )

    async def _update_realtime_progress(
        self,
        job_id: int,
        p: float,
        index: int,
        total: int
    ):
        async with self.session_factory() as session:
            overall_prog = ((index - 1) / total) * 100 + (p / total)

            await self._update_job_progress(
                session,
                job_id,
                progress=overall_prog
            )

