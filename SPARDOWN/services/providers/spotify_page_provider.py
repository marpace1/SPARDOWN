import httpx
import json
from typing import List, Optional, Tuple, Any
from bs4 import BeautifulSoup
from SPARDOWN.services.providers.base_provider import MetadataProvider
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.core.logging import logger

class SpotifyPageProvider(MetadataProvider):
    """
    Metadata extraction from public Spotify pages.
    Implements strict anti-bot detection to avoid generating fake/placeholder metadata.
    """
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.BOT_INDICATORS = {
            "Spotify – Web Player", 
            "Spotify - Web Player", 
            "Spotify", 
            "Log in to Spotify"
        }

    @property
    def name(self) -> str:
        return "SpotifyPageProvider"

    def supports_url(self, url: str) -> bool:
        return "open.spotify.com" in url

    async def _fetch_page(self, url: str) -> Tuple[BeautifulSoup, Optional[dict]]:
        logger.info(f"[SpotifyPageProvider] Fetching page: {url}")
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Anti-Bot Detection: Check Page Title
            page_title = soup.title.string if soup.title else ""
            if any(indicator in page_title for indicator in self.BOT_INDICATORS):
                logger.warning(f"[SpotifyPageProvider] Anti-bot detected via title: {page_title}")
                raise ValueError("Spotify anti-bot protection prevented metadata extraction")
            
            # 2. Anti-Bot Detection: Check for __NEXT_DATA__
            json_data = None
            script_tag = soup.find('script', id='__NEXT_DATA__')
            if script_tag:
                try:
                    json_data = json.loads(script_tag.string)
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # If no JSON and no OG tags, it's a bot-blocked page
            if not json_data and not soup.find("meta", property="og:title"):
                logger.warning("[SpotifyPageProvider] Anti-bot detected: No JSON and no OG tags")
                raise ValueError("Spotify anti-bot protection prevented metadata extraction")
            
            return soup, json_data

    def _find_recursive(self, data: Any, target_key: str) -> Any:
        if isinstance(data, dict):
            if target_key in data: return data[target_key]
            for value in data.values():
                res = self._find_recursive(value, target_key)
                if res is not None: return res
        elif isinstance(data, list):
            for item in data:
                res = self._find_recursive(item, target_key)
                if res is not None: return res
        return None

    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        soup, json_data = await self._fetch_page(url)
        
        # Try JSON first
        if json_data:
            track_data = self._find_recursive(json_data, 'track')
            if track_data and isinstance(track_data, dict) and 'name' in track_data:
                return SpotifyTrackMetadata(
                    spotify_id=track_data.get('id', ''),
                    title=track_data.get('name', 'Unknown'),
                    artist=track_data.get('artists', [{}])[0].get('name', 'Unknown'),
                    album=track_data.get('album', {}).get('name', 'Unknown'),
                    duration_ms=track_data.get('duration_ms', 0),
                    artwork_url=track_data.get('album', {}).get('images', [{}])[0].get('url', ''),
                    release_date=track_data.get('album', {}).get('release_date', ''),
                    url=url
                )
        
        # Fallback to Meta Tags
        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            desc = soup.find("meta", property="og:description")
            img = soup.find("meta", property="og:image")
            return SpotifyTrackMetadata(
                spotify_id=url.split("/")[-1].split("?")[0],
                title=title_tag["content"],
                artist=desc["content"] if desc else "Unknown",
                album="Unknown",
                duration_ms=0,
                artwork_url=img["content"] if img else "",
                release_date="",
                url=url
            )
            
        raise ValueError("Could not extract track metadata from Spotify page")

    async def get_album(self, url: str) -> List[SpotifyTrackMetadata]:
        soup, json_data = await self._fetch_page(url)
        if json_data:
            album_data = self._find_recursive(json_data, 'album')
            if album_data and isinstance(album_data, dict) and 'name' in album_data:
                track_items = self._find_recursive(album_data, 'items') or []
                if track_items:
                    album_name = album_data.get('name', 'Unknown')
                    release_date = album_data.get('release_date', '')
                    artwork_url = album_data.get('images', [{}])[0].get('url', '')
                    tracks = []
                    for item in track_items:
                        t = item.get('track', item) if isinstance(item, dict) else {}
                        if not t or not isinstance(t, dict): continue
                        tracks.append(SpotifyTrackMetadata(
                            spotify_id=t.get('id', ''), title=t.get('name', 'Unknown'),
                            artist=t.get('artists', [{}])[0].get('name', 'Unknown'),
                            album=album_name, duration_ms=t.get('duration_ms', 0),
                            artwork_url=artwork_url, release_date=release_date,
                            url=t.get('external_urls', {}).get('spotify', '')
                        ))
                    return tracks

        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            desc = soup.find("meta", property="og:description")
            img = soup.find("meta", property="og:image")
            return [SpotifyTrackMetadata(
                spotify_id=url.split("/")[-1].split("?")[0],
                title="Album Representative",
                artist=desc["content"] if desc else "Unknown",
                album=title_tag["content"],
                duration_ms=0, artwork_url=img["content"] if img else "",
                release_date="", url=url
            )]
        raise ValueError("Could not extract album metadata from Spotify page")

    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        soup, json_data = await self._fetch_page(url)
        if json_data:
            playlist_data = self._find_recursive(json_data, 'playlist')
            if playlist_data:
                track_items = self._find_recursive(playlist_data, 'items') or []
                if track_items:
                    tracks = []
                    for item in track_items:
                        t = item.get('track', item) if isinstance(item, dict) else {}
                        if not t or not isinstance(t, dict): continue
                        tracks.append(SpotifyTrackMetadata(
                            spotify_id=t.get('id', ''), title=t.get('name', 'Unknown'),
                            artist=t.get('artists', [{}])[0].get('name', 'Unknown'),
                            album=t.get('album', {}).get('name', 'Unknown'),
                            duration_ms=t.get('duration_ms', 0),
                            artwork_url=t.get('album', {}).get('images', [{}])[0].get('url', ''),
                            release_date=t.get('album', {}).get('release_date', ''),
                            url=t.get('external_urls', {}).get('spotify', '')
                        ))
                    return tracks
        raise ValueError("Playlist metadata unavailable from public Spotify pages")

    async def get_artist(self, url: str) -> List[SpotifyTrackMetadata]:
        soup, json_data = await self._fetch_page(url)
        if json_data:
            artist_data = self._find_recursive(json_data, 'artist')
            if artist_data and isinstance(artist_data, dict) and 'name' in artist_data:
                artist_name = artist_data.get('name', 'Unknown')
                top_tracks = self._find_recursive(artist_data, 'items') or []
                tracks = []
                for t in top_tracks:
                    if not isinstance(t, dict): continue
                    tracks.append(SpotifyTrackMetadata(
                        spotify_id=t.get('id', ''), title=t.get('name', 'Unknown'),
                        artist=artist_name, album=t.get('album', {}).get('name', 'Unknown'),
                        duration_ms=t.get('duration_ms', 0),
                        artwork_url=t.get('album', {}).get('images', [{}])[0].get('url', ''),
                        release_date=t.get('album', {}).get('release_date', ''),
                        url=t.get('external_urls', {}).get('spotify', '')
                    ))
                return tracks
        
        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            desc = soup.find("meta", property="og:description")
            img = soup.find("meta", property="og:image")
            return [SpotifyTrackMetadata(
                spotify_id=url.split("/")[-1].split("?")[0],
                title="Artist Representative",
                artist=title_tag["content"],
                album="Artist Discography",
                duration_ms=0, artwork_url=img["content"] if img else "",
                release_date="", url=url
            )]
        raise ValueError("Could not extract artist metadata from Spotify page")
