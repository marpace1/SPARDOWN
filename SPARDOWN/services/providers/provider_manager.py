import logging
import time
from typing import List, Optional, Any
from SPARDOWN.services.providers.base_provider import MetadataProvider
from SPARDOWN.services.providers.spotify_api_provider import SpotifyAPIProvider
from SPARDOWN.services.providers.spotify_page_provider import SpotifyPageProvider
from SPARDOWN.services.providers.musicbrainz_provider import MusicBrainzProvider
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.core.logging import logger

class ProviderManager:
    def __init__(self):
        self.providers: List[MetadataProvider] = [
            SpotifyAPIProvider(),
            SpotifyPageProvider(),
            MusicBrainzProvider()
        ]

    async def _execute_with_timing(self, method_name: str, url: str, job_type: str) -> Any:
        last_exception = None
        for provider in self.providers:
            if not provider.supports_url(url): continue
            if hasattr(provider, 'is_available') and not provider.is_available(): continue

            start_time = time.perf_counter()
            try:
                logger.info(f"[ProviderManager] Selected provider: {provider.name} for {job_type}")
                method = getattr(provider, method_name)
                result = await method(url)
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.info(f"[ProviderManager] {provider.name} succeeded in {duration_ms:.2f} ms")
                return result
            except ValueError as ve:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.warning(f"[ProviderManager] {provider.name} rejected request in {duration_ms:.2f} ms: {ve}")
                last_exception = ve
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.warning(f"[ProviderManager] {provider.name} failed in {duration_ms:.2f} ms. Error: {e}")
                last_exception = e
                logger.info(f"[ProviderManager] Fallback activated...")
        
        if last_exception:
            raise last_exception
        raise RuntimeError(f"All metadata providers failed to resolve the {job_type}.")

    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        return await self._execute_with_timing('get_track', url, 'track')

    async def get_album(self, url: str) -> List[SpotifyTrackMetadata]:
        return await self._execute_with_timing('get_album', url, 'album')

    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        return await self._execute_with_timing('get_playlist', url, 'playlist')

    async def get_artist(self, url: str) -> List[SpotifyTrackMetadata]:
        return await self._execute_with_timing('get_artist', url, 'artist')
