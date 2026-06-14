from pathlib import Path
from datetime import datetime, timedelta
from SPARDOWN.core.logging import logger


class CleanupService:

    def __init__(self, downloads_dir="downloads"):
        self.downloads_dir = Path(downloads_dir)

    async def cleanup_old_files(self):

        if not self.downloads_dir.exists():
            return

        logger.info(
            f"[Cleanup] Starting cleanup of {self.downloads_dir}"
        )

        cutoff = datetime.utcnow() - timedelta(hours=24)

        deleted = 0

        for file in self.downloads_dir.rglob("*"):

            if not file.is_file():
                continue

            modified = datetime.utcfromtimestamp(
                file.stat().st_mtime
            )

            if modified < cutoff:
                try:
                    file.unlink()

                    deleted += 1

                    logger.info(
                        f"[Cleanup] Deleted expired file: {file.name}"
                    )

                except Exception as e:
                    logger.error(
                        f"Cleanup error while deleting {file}: {e}"
                    )

        logger.info(
            f"[Cleanup] Deleted {deleted} expired files"
        )