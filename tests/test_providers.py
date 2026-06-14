import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from SPARDOWN.services.providers.provider_manager import ProviderManager
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.services.providers.spotify_api_provider import SpotifyAPIProvider
from SPARDOWN.services.providers.spotify_page_provider import SpotifyPageProvider
from SPARDOWN.services.providers.musicbrainz_provider import MusicBrainzProvider

class TestProviderStabilization(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.manager = ProviderManager()
        self.url = "https://open.spotify.com/track/test_id"
        self.mock_meta = SpotifyTrackMetadata(
            spotify_id="test", title="Test", artist="Artist", 
            album="Album", duration_ms=100, artwork_url="url", 
            release_date="2023", url=self.url
        )

    @patch('SPARDOWN.services.providers.spotify_api_provider.SpotifyAPIProvider.is_available', return_value=True)
    async def test_spotify_api_success(self, mock_avail):
        with patch.object(SpotifyAPIProvider, 'get_track', return_value=self.mock_meta) as mock_get:
            res = await self.manager.get_track(self.url)
            self.assertEqual(res.title, "Test")
            mock_get.assert_called_once()

    @patch('SPARDOWN.services.providers.spotify_api_provider.SpotifyAPIProvider.is_available', return_value=True)
    async def test_spotify_api_403_failover(self, mock_avail):
        with patch.object(SpotifyAPIProvider, 'get_track', side_effect=Exception("403 Forbidden")), \
             patch.object(SpotifyPageProvider, 'get_track', return_value=self.mock_meta) as mock_page:
            res = await self.manager.get_track(self.url)
            self.assertEqual(res.title, "Test")
            mock_page.assert_called_once()

    @patch('SPARDOWN.services.providers.spotify_api_provider.SpotifyAPIProvider.is_available', return_value=False)
    async def test_spotify_page_success(self, mock_avail):
        with patch.object(SpotifyPageProvider, 'get_track', return_value=self.mock_meta) as mock_page:
            res = await self.manager.get_track(self.url)
            self.assertEqual(res.title, "Test")
            mock_page.assert_called_once()

    async def test_musicbrainz_success(self):
        with patch.object(SpotifyAPIProvider, 'is_available', return_value=False), \
             patch.object(SpotifyPageProvider, 'get_track', side_effect=Exception("Page Fail")), \
             patch.object(MusicBrainzProvider, 'get_track', return_value=self.mock_meta) as mock_mb:
            res = await self.manager.get_track(self.url)
            self.assertEqual(res.title, "Test")
            mock_mb.assert_called_once()

    async def test_all_providers_fail(self):
        with patch.object(SpotifyAPIProvider, 'is_available', return_value=False), \
             patch.object(SpotifyPageProvider, 'get_track', side_effect=ValueError("Fail")), \
             patch.object(MusicBrainzProvider, 'get_track', side_effect=ValueError("Fail")):
            with self.assertRaises(ValueError) as cm:
                await self.manager.get_track(self.url)
            self.assertIn("Fail", str(cm.exception))

    async def test_playlist_unsupported_musicbrainz(self):
        with patch.object(SpotifyAPIProvider, 'is_available', return_value=False), \
             patch.object(SpotifyPageProvider, 'get_playlist', side_effect=Exception("Page Fail")):
            with self.assertRaises(ValueError) as cm:
                await self.manager.get_playlist(self.url)
            self.assertIn("MusicBrainz cannot resolve Spotify playlists", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
