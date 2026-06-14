import asyncio
import sys
from SPARDOWN.config.settings import settings
from SPARDOWN.core.logging import setup_logging, logger
from SPARDOWN.database.session import db
from SPARDOWN.downloaders.yt_dlp import YtDlpDownloader
from SPARDOWN.workers.queue import QueueManager
from SPARDOWN.services.download_service import DownloadService

async def main():
    # 1. Setup
    setup_logging(settings.LOG_LEVEL)
    logger.info("Initializing SPARDOWN Backend...")
    
    # 2. Database Init
    await db.init_db()
    
    # 3. Component Initialization
    downloader = YtDlpDownloader()
    queue_manager = QueueManager(concurrency=settings.MAX_CONCURRENT_DOWNLOADS)
    
    # We need a session for the service. In a real API, this would be per-request.
    session = await db.get_session()
    service = DownloadService(session, downloader, queue_manager)
    
    # 4. Start Worker Loop
    # The worker uses the service.process_job method
    await queue_manager.start(worker_func=service.process_job)
    
    try:
        # --- Example Usage (Simulating API calls) ---
        
        # Example 1: Request a track download
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 
        job_id = await service.create_download_job(test_url, "track")
        logger.info(f"Started test job: {job_id}")
        
        # Example 2: Check status periodically
        for _ in range(5):
            await asyncio.sleep(2)
            status = await service.get_job_status(job_id)
            logger.info(f"Job {job_id} status: {status['status']} - Progress: {status['progress']}%")
            if status['status'] == 'completed':
                break
        
        # Example 3: List downloads
        downloads = await service.list_downloads()
        logger.info(f"Total downloads in history: {len(downloads)}")
        
        logger.info("Demo complete. Keeping workers alive for a few seconds...")
        await asyncio.sleep(5)
        
    except KeyboardInterrupt:
        pass
    finally:
        await queue_manager.stop()
        await session.close()
        logger.info("SPARDOWN shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
