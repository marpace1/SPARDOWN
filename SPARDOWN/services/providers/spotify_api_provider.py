import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Optional, Tuple
from dataclasses import dataclass
from SPARDOWN.services.providers.base_provider import MetadataProvider
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.core.logging import logger
import os

class SpotifyAPIProvider(MetadataProvider):
    def __init__(self):
        self._sp = None
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        
        if client_id and client_secret:
            try:
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                self._sp = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("[SpotifyAPIProvider] Initialized successfully")
            except Exception as e:
                logger.warning(f"[SpotifyAPIProvider] Failed to initialize: {e}")
        else:
            logger.warning("[SpotifyAPIProvider] Credentials missing. Provider will be unavailable.")

    @property
    def name(self) -> str:
        return "SpotifyAPIProvider"

    def supports_url(self, url: str) -> bool:
        return "open.spotify.com" in url

    def is_available(self) -> bool:
        return self._sp is not None

    def _parse_url(self, url: str) -> Tuple[str, str]:
        parts = url.split('/')
        for i, part in enumerate(parts):
            if part in ['track', 'album', 'playlist', 'artist']:
                return part, parts[i+1].split('?')[0]
        raise ValueError("Invalid Spotify URL")

    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        if not self.is_available(): raise RuntimeError("Provider unavailable")
        type_, id_ = self._parse_url(url)
        track = self._sp.track(id_)
        return SpotifyTrackMetadata(
            spotify_id=id_,
            title=track['name'],
            artist=track['artists'][0]['name'],
            album=track['album']['name'],
            duration_ms=track['duration_ms'],
            artwork_url=track['album']['images'][0]['url'] if track['album']['images'] else "",
            release_date=track['album']['release_date'],
            url=url
        )

    async def get_album(self, url: str) -> List[SpotifyTrackMetadata]:
        if not self.is_available(): raise RuntimeError("Provider unavailable")
        type_, id_ = self._parse_url(url)
        album_info = self._sp.album(id_)
        album_name = album_info['name']
        release_date = album_info['release_date']
        artwork_url = album_info['images'][0]['url'] if album_info['images'] else ""
        
        tracks = []
        results = self.sp_album_tracks(id_)
        while results:
            for item in results['items']:
                t = item['track']
                tracks.append(SpotifyTrackMetadata(
                    spotify_id=t['id'], title=t['name'], artist=t['artists'][0]['name'],
                    album=album_name, duration_ms=t['duration_ms'], artwork_url=artwork_url,
                    release_date=release_date, url=t['external_urls']['spotify']
                ))
            results = results['next'] if results.get('next') else None
        return tracks

    def sp_album_tracks(self, id_):
        return self._sp.album_tracks(id_)

    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        if not self.is_available(): raise RuntimeError("Provider unavailable")
        type_, id_ = self._parse_url(url)
        tracks = []
        results = self._sp.playlist_items(id_)
        while results:
            for item in results['items']:
                t = item['track']
                if not t: continue
                tracks.append(SpotifyTrackMetadata(
                    spotify_id=t['id'], title=t['name'], artist=t['artists'][0]['name'],
                    album=t['album']['name'], duration_ms=t['duration_ms'],
                    artwork_url=t['album']['images'][0]['url'] if t['album']['images'] else "",
                    release_date=t['album']['release_date'], url=t['external_urls']['spotify']
                ))
            results = self._sp.next(results) if results.get('next') else None
        return tracks

    async def get_artist(self, url: str) -> List[SpotifyTrackMetadata]:
        if not self.is_available(): raise RuntimeError("Provider unavailable")
        type_, id_ = self._parse_url(url)
        artist_info = self._sp.artist(id_)
        artist_name = artist_info['name']
        results = self._sp.artist_top_tracks(id_)
        tracks = []
        for t in results['tracks']:
            tracks.append(SpotifyTrackMetadata(
                spotify_id=t['id'], title=t['name'], artist=artist_name,
                album=t['album']['name'], duration_ms=t['duration_ms'],
                artwork_url=t['album']['images'][0]['url'] if t['album']['images'] else "",
                release_date=t['album']['release_date'], url=t['external_urls']['spotify']
            ))
        return tracks
