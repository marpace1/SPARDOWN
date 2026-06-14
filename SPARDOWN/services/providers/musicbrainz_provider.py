import httpx
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
from SPARDOWN.services.providers.base_provider import MetadataProvider
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.core.logging import logger

class MusicBrainzProvider(MetadataProvider):
    def __init__(self):
        self.base_url = "https://musicbrainz.org/ws2"
        self.headers = {"User-Agent": "SPARDOWN/1.0 (contact@spardown.ai)"}
        self.INVALID_VALUES = {
            "Spotify – Web Player", 
            "Spotify - Web Player", 
            "Unknown Artist", 
            "Unknown Track", 
            "Spotify",
            ""
        }

    @property
    def name(self) -> str:
        return "MusicBrainzProvider"

    def supports_url(self, url: str) -> bool:
        return True

    def _validate_input(self, title: str, artist: str):
        if not title or not artist:
            raise ValueError("No valid metadata available for MusicBrainz lookup (empty fields)")
        if title in self.INVALID_VALUES or artist in self.INVALID_VALUES:
            raise ValueError(f"No valid metadata available for MusicBrainz lookup (placeholder detected: {title}/{artist})")

    async def _get_search_terms(self, url: str) -> Tuple[str, str]:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else ""
            if " - " in title:
                parts = title.split(" - ")
                return parts[0].strip(), parts[1].strip()
            return title.strip(), "Unknown Artist"

    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        title, artist = await self._get_search_terms(url)
        self._validate_input(title, artist)
        
        query = f"recording:\"{title}\" AND artist:\"{artist}\""
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/recording", params={"query": query, "fmt": "json"})
            response.raise_for_status()
            data = response.json()
            
            if not data.get('recordings'):
                raise ValueError(f"No matching recording found on MusicBrainz for {title}")
            
            rec = data['recordings'][0]
            album_name = "Unknown Album"
            release_date = ""
            if rec.get('release-list'):
                rel_id = rec['release-list'][0]['id']
                rel_resp = await client.get(f"{self.base_url}/release/{rel_id}?fmt=json")
                if rel_resp.status_code == 200:
                    rel_data = rel_resp.json()
                    album_name = rel_data.get('title', 'Unknown Album')
                    release_date = rel_data.get('date', '')
            
            return SpotifyTrackMetadata(
                spotify_id="mb_" + rec['id'],
                title=rec.get('title', title),
                artist=rec.get('artist-credit', [{}])[0].get('name', artist),
                album=album_name,
                duration_ms=rec.get('length', 0),
                artwork_url="",
                release_date=release_date,
                url=url
            )

    async def get_album(self, url: str) -> List[SpotifyTrackMetadata]:
        title, _ = await self._get_search_terms(url)
        if not title or title in self.INVALID_VALUES:
            raise ValueError("No valid metadata available for MusicBrainz lookup")
            
        query = f"release:\"{title}\""
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/release", params={"query": query, "fmt": "json"})
            response.raise_for_status()
            data = response.json()
            
            if not data.get('releases'):
                raise ValueError(f"No matching album found on MusicBrainz for {title}")
            
            rel = data['releases'][0]
            rel_id = rel['id']
            rel_resp = await client.get(f"{self.base_url}/release/{rel_id}?inc=recordings&fmt=json")
            rel_resp.raise_for_status()
            rel_data = rel_resp.json()
            
            tracks = []
            for rec in rel_data.get('recording-list', []):
                tracks.append(SpotifyTrackMetadata(
                    spotify_id="mb_" + rec['id'],
                    title=rec.get('title', 'Unknown'),
                    artist=rel.get('artist-credit', [{}])[0].get('name', 'Unknown'),
                    album=rel.get('title', 'Unknown'),
                    duration_ms=rec.get('length', 0),
                    artwork_url="",
                    release_date=rel.get('date', ''),
                    url=url
                ))
            if not tracks:
                raise ValueError("Album found but no tracks could be retrieved")
            return tracks

    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        raise ValueError("MusicBrainz cannot resolve Spotify playlists")

    async def get_artist(self, url: str) -> List[SpotifyTrackMetadata]:
        _, artist = await self._get_search_terms(url)
        if not artist or artist in self.INVALID_VALUES:
            raise ValueError("No valid metadata available for MusicBrainz lookup")
            
        query = f"artist:\"{artist}\""
        async with httpx.AsyncClient(headers=self.headers, timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/artist", params={"query": query, "fmt": "json"})
            response.raise_for_status()
            data = response.json()
            
            if not data.get('artists'):
                raise ValueError(f"No matching artist found on MusicBrainz for {artist}")
            
            art = data['artists'][0]
            art_id = art['id']
            rel_resp = await client.get(f"{self.base_url}/artist/{art_id}/releases?fmt=json")
            rel_resp.raise_for_status()
            rel_data = rel_resp.json()
            
            tracks = []
            for rel in rel_data.get('releases', []):
                tracks.append(SpotifyTrackMetadata(
                    spotify_id="mb_" + rel['id'],
                    title=rel.get('title', 'Unknown'),
                    artist=art.get('name', artist),
                    album=rel.get('title', 'Unknown'),
                    duration_ms=0,
                    artwork_url="",
                    release_date=rel.get('date', ''),
                    url=url
                ))
            if not tracks:
                raise ValueError("Artist found but no representative releases available")
            return tracks
