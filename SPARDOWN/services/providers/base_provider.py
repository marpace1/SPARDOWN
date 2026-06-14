from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from SPARDOWN.services.spotify_service import SpotifyTrackMetadata

class MetadataProvider(ABC):
    """
    Abstract Base Class for all metadata providers.
    All providers must return the same normalized SpotifyTrackMetadata model.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        pass

    @abstractmethod
    async def get_track(self, url: str) -> SpotifyTrackMetadata:
        pass

    @abstractmethod
    async def get_album(self, url: str) -> List[SpotifyTrackMetadata]:
        pass

    @abstractmethod
    async def get_playlist(self, url: str) -> List[SpotifyTrackMetadata]:
        pass

    @abstractmethod
    async def get_artist(self, url: str) -> List[SpotifyTrackMetadata]:
        pass
