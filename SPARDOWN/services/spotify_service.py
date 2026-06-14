import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from SPARDOWN.config.settings import settings
import os

@dataclass
class SpotifyTrackMetadata:
    spotify_id: str
    title: str
    artist: str
    album: str
    duration_ms: int
    artwork_url: str
    release_date: str
    url: str

class SpotifyService:
    def __init__(self):
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise RuntimeError(
                "Spotify credentials missing. Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables."
            )
            
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def _parse_url(self, url: str) -> Tuple[str, str]:
        parts = url.split('/')
        for i, part in enumerate(parts):
            if part in ['track', 'album', 'playlist', 'artist']:
                return part, parts[i+1].split('?')[0]
        raise ValueError("Invalid Spotify URL")

    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        type_, id_ = self._parse_url(url)
        if type_ != 'track': raise ValueError("URL is not a track")
        
        track = self.sp.track(id_)
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
        type_, id_ = self._parse_url(url)
        if type_ != 'album': raise ValueError("URL is not an album")
        
        album_info = self.sp.album(id_)
        album_name = album_info['name']
        release_date = album_info['release_date']
        artwork_url = album_info['images'][0]['url'] if album_info['images'] else ""
        
        tracks = []
        results = self.sp.album_tracks(id_)
        while results:
            for item in results['items']:
                t = item['track']
                tracks.append(SpotifyTrackMetadata(
                    spotify_id=t['id'],
                    title=t['name'],
                    artist=t['artists'][0]['name'],
                    album=album_name,
                    duration_ms=t['duration_ms'],
                    artwork_url=artwork_url,
                    release_date=release_date,
                    url=t['external_urls']['spotify']
                ))
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return tracks

    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        type_, id_ = self._parse_url(url)
        if type_ != 'playlist': raise ValueError("URL is not a playlist")
        
        tracks = []
        results = self.sp.playlist_items(id_)
        while results:
            for item in results['items']:
                t = item['track']
                if not t: continue
                tracks.append(SpotifyTrackMetadata(
                    spotify_id=t['id'],
                    title=t['name'],
                    artist=t['artists'][0]['name'],
                    album=t['album']['name'],
                    duration_ms=t['duration_ms'],
                    artwork_url=t['album']['images'][0]['url'] if t['album']['images'] else "",
                    release_date=t['album']['release_date'],
                    url=t['external_urls']['spotify']
                ))
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return tracks

    async def get_artist_discography(self, url: str) -> List[SpotifyTrackMetadata]:
        type_, id_ = self._parse_url(url)
        if type_ != 'artist': raise ValueError("URL is not an artist")
        
        artist_info = self.sp.artist(id_)
        artist_name = artist_info['name']
        
        # For discography, we'll take top tracks as the representative set
        # but we could iterate through all albums.
        results = self.sp.artist_top_tracks(id_)
        tracks = []
        for t in results['tracks']:
            tracks.append(SpotifyTrackMetadata(
                spotify_id=t['id'],
                title=t['name'],
                artist=artist_name,
                album=t['album']['name'],
                duration_ms=t['duration_ms'],
                artwork_url=t['album']['images'][0]['url'] if t['album']['images'] else "",
                release_date=t['album']['release_date'],
                url=t['external_urls']['spotify']
            ))
        return tracks
