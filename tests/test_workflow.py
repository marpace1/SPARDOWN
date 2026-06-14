import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from SPARDOWN.services.download_service import DownloadService
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.models.models import JobStatus

class TestSpardownEndToEnd(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_session_factory = MagicMock()
        self.mock_session = AsyncMock()
        self.mock_session_factory.return_value.__aenter__.return_value = self.mock_session
        
        self.mock_downloader = AsyncMock()
        self.mock_queue = AsyncMock()
        self.mock_spotify = AsyncMock()
        self.mock_matcher = AsyncMock()
        self.mock_cache = AsyncMock()
        
        self.service = DownloadService(
            session_factory=self.mock_session_factory,
            downloader=self.mock_downloader,
            queue_manager=self.mock_queue,
            spotify_service=self.mock_spotify,
            matching_service=self.mock_matcher,
            cache_service_factory=lambda s: self.mock_cache,
            ws_manager=AsyncMock()
        )

    async def test_single_track_workflow(self):
        # Setup
        url = "https://open.spotify.com/track/123"
        track_meta = SpotifyTrackMetadata(
            spotify_id="123", title="Test Song", artist="Test Artist",
            album="Test Album", duration_ms=200000, artwork_url="url",
            release_date="2023", url=url
        )
        
        self.mock_spotify.get_track.return_value = track_meta
        self.mock_matcher.match_track.return_value = ("https://yt.com/abc", 0.9)
        self.mock_downloader.download.return_value = True
        
        # Execute
        job_id = await self.service.create_download_job(url, "track")
        await self.service.process_job(job_id)
        
        # Verify
        self.mock_spotify.get_track.assert_called_once()
        self.mock_downloader.download.assert_called_once()
        self.mock_downloader.embed_metadata.assert_called_once()

    async def test_playlist_workflow(self):
        # Setup
        url = "https://open.spotify.com/playlist/456"
        tracks = [
            SpotifyTrackMetadata("1", "S1", "A1", "Alb", 100, "u", "d", "url1"),
            SpotifyTrackMetadata("2", "S2", "A1", "Alb", 100, "u", "d", "url2"),
        ]
        
        self.mock_spotify.get_playlist.return_value = tracks
        self.mock_matcher.match_track.return_value = ("https://yt.com/abc", 0.9)
        self.mock_downloader.download.return_value = True
        
        # Execute
        job_id = await self.service.create_download_job(url, "playlist")
        await self.service.process_job(job_id)
        
        # Verify
        self.assertEqual(self.mock_downloader.download.call_count, 2)

if __name__ == "__main__":
    unittest.main()
