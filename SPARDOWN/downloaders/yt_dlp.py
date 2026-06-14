import asyncio
import yt_dlp
from typing import Dict, Any, Callable, Optional
from SPARDOWN.downloaders.base import BaseDownloader, TrackMetadata
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC, APIC
from mutagen.mp3 import MP3

class YtDlpDownloader(BaseDownloader):
    def __init__(self):
        self.ydl_opts_base = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': False,
        }

    async def extract_info(self, url: str) -> Dict[str, Any]:
        return await asyncio.to_thread(self._extract_info_sync, url)

    def _extract_info_sync(self, url: str) -> Dict[str, Any]:
        with yt_dlp.YoutubeDL(self.ydl_opts_base) as ydl:
            return ydl.extract_info(url, download=False)

    async def download(
        self,
        url: str,
        output_path: str,
        progress_callback=None
    ) -> bool:

        opts = {
            **self.ydl_opts_base,
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [
                lambda d: self._progress_hook(d, progress_callback)
            ] if progress_callback else [],
        }

        try:
            await asyncio.to_thread(
                self._download_sync,
                opts,
                url
            )
            return True

        except Exception as e:
            print(f"[YTDLP ERROR] {e}")
            return False


    def _download_sync(self, opts, url):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _progress_hook(self, d, callback):
        if d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%')
            try:
                # Clean characters like ' ', '%', ')' from the string
                clean_p = "".join(c for c in p_str if c.isdigit() or c == '.')
                callback(float(clean_p))
            except (ValueError, TypeError):
                pass

    async def embed_metadata(self, file_path: str, metadata: TrackMetadata) -> bool:
        return await asyncio.to_thread(self._embed_metadata_sync, file_path, metadata)

    def _embed_metadata_sync(self, file_path: str, metadata: TrackMetadata) -> bool:
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            
            tags = audio.tags
            tags.add(TIT2(encoding=3, text=metadata.title))
            tags.add(TPE1(encoding=3, text=metadata.artist))
            if metadata.album:
                tags.add(TALB(encoding=3, text=metadata.album))
            if metadata.genre:
                tags.add(TCON(encoding=3, text=metadata.genre))
            if metadata.release_date:
                tags.add(TDRC(encoding=3, text=metadata.release_date))
            
            audio.save()
            return True
        except Exception as e:
            print(f"[YTDLP ERROR] {e}")
            raise
