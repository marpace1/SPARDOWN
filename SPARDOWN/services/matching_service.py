import asyncio
from typing import List, Optional, Tuple
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata
from SPARDOWN.downloaders.yt_dlp import YtDlpDownloader
from SPARDOWN.core.logging import logger

class MatchingService:
    def __init__(self, downloader: YtDlpDownloader):
        self.downloader = downloader

    async def match_track(self, track: SpotifyTrackMetadata) -> Tuple[Optional[str], float]:
        """
        Matches a Spotify track to a YouTube source.
        Returns (URL, ConfidenceScore).
        """
        query = f"ytsearch1:{track.artist} {track.title} official audio"
        try:
            # Use yt-dlp to search
            info = await self.downloader.extract_info(query)
            if not info or 'entries' not in info or not info['entries']:
                return None, 0.0
            
            best_match = info['entries'][0]
            confidence = await self._calculate_confidence(track, best_match)
            
            return best_match['webpage_url'], confidence
        except Exception as e:
            logger.error(f"Matching error for {track.title}: {e}")
            return None, 0.0

    async def _calculate_confidence(self, spotify: SpotifyTrackMetadata, yt_info: dict) -> float:
        score = 0.0
        
        # 1. Title match (Fuzzy)
        s_title = spotify.title.lower()
        y_title = yt_info.get('title', '').lower()
        if s_title in y_title or y_title in s_title:
            score += 0.5
            
        # 2. Artist match
        s_artist = spotify.artist.lower()
        if s_artist in y_title:
            score += 0.3
            
        # 3. Duration match (within 5 seconds)
        s_dur = spotify.duration_ms / 1000
        y_dur = yt_info.get('duration', 0)
        if abs(s_dur - y_dur) < 5:
            score += 0.2
            
        return min(score, 1.0)

    async def match_album(self, tracks: List[SpotifyTrackMetadata]) -> List[Tuple[Optional[str], float]]:
        return await asyncio.gather(*[self.match_track(t) for t in tracks])

    async def match_playlist(self, tracks: List[SpotifyTrackMetadata]) -> List[Tuple[Optional[str], float]]:
        # Process in chunks to avoid overloading
        results = []
        chunk_size = 10
        for i in range(0, len(tracks), chunk_size):
            chunk = tracks[i:i+chunk_size]
            res = await asyncio.gather(*[self.match_track(t) for t in chunk])
            results.extend(res)
            await asyncio.sleep(1) # Rate limiting
        return results
