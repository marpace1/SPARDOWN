import os
import re
from pathlib import Path
from typing import Optional
from SPARDOWN.config.settings import settings

class StorageManager:
    def __init__(self):
        self.base_path = settings.BASE_DOWNLOAD_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Remove illegal characters from filename."""
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def get_download_path(self, artist: str, album: str, title: str) -> Path:
        """Generate a structured path: /downloads/Artist/Album/Title.mp3"""
        artist_safe = self.sanitize_filename(artist)
        album_safe = self.sanitize_filename(album or "Unknown Album")
        title_safe = self.sanitize_filename(title)
        
        folder = self.base_path / artist_safe / album_safe
        folder.mkdir(parents=True, exist_ok=True)
        
        return folder / f"{title_safe}.{settings.DEFAULT_AUDIO_FORMAT}"

    def check_duplicate(self, artist: str, album: str, title: str) -> bool:
        path = self.get_download_path(artist, album, title)
        return path.exists()

storage_manager = StorageManager()
