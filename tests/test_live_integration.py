import asyncio
import unittest
from unittest.mock import patch
from SPARDOWN.services.providers.provider_manager import ProviderManager
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata

class TestLiveIntegration(unittest.IsolatedAsyncioTestCase):
    """
    Optional integration tests that hit real Spotify URLs.
    These verify that our PageProvider and MusicBrainzProvider actually work.
    """
    async def asyncSetUp(self):
        self.manager = ProviderManager()

    async def test_live_track_extraction(self):
        # Use a known public track
        url = "https://open.spotify.com/track/4cOd7P6uSsqS7zN8S38Sio"
        try:
            meta = await self.manager.get_track(url)
            self.assertIsInstance(meta, SpotifyTrackMetadata)
            self.assertTrue(len(meta.title) > 0)
            self.assertTrue(len(meta.artist) > 0)
            print(f"Live Track Test Success: {meta.title} by {meta.artist}")
        except Exception as e:
            self.fail(f"Live track extraction failed: {e}")

    async def test_live_album_extraction(self):
        # Use a known public album
        url = "https://open.spotify.com/album/4S6mF8H9J7u7yYp7Lp9X6G"
        try:
            meta_list = await self.manager.get_album(url)
            self.assertIsInstance(meta_list, list)
            self.assertTrue(len(meta_list) > 0)
            self.assertTrue(len(meta_list[0].title) > 0)
            print(f"Live Album Test Success: found {len(meta_list)} tracks")
        except Exception as e:
            self.fail(f"Live album extraction failed: {e}")

    async def test_live_artist_extraction(self):
        # Use a known public artist
        url = "https://open.spotify.com/artist/0TdBpS7Z7mCBeZpS6rR0Z7"
        try:
            meta_list = await self.manager.get_artist(url)
            self.assertIsInstance(meta_list, list)
            self.assertTrue(len(meta_list) > 0)
            print(f"Live Artist Test Success: found {len(meta_list)} representative tracks")
        except Exception as e:
            self.fail(f"Live artist extraction failed: {e}")

if __name__ == "__main__":
    unittest.main()
