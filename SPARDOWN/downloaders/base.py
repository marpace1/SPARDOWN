from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass

@dataclass
class TrackMetadata:
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[float] = None
    genre: Optional[str] = None
    release_date: Optional[str] = None
    artwork_url: Optional[str] = None
    source_url: str = ""

class BaseDownloader(ABC):
    @abstractmethod
    async def extract_info(self, url: str) -> Dict[str, Any]:
        """Extract metadata from the URL."""
        pass

    @abstractmethod
    async def download(
        self, 
        url: str, 
        output_path: str, 
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """Download the file to the specified path."""
        pass

    @abstractmethod
    async def embed_metadata(self, file_path: str, metadata: TrackMetadata) -> bool:
        """Embed metadata into the audio file."""
        pass
