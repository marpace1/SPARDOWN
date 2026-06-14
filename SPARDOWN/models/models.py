import enum
from datetime import datetime
from typing import List, Optional


from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Float,
    ForeignKey,
    Enum as SQLEnum,
    Text,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


class Base(DeclarativeBase):
    pass


class JobStatus(enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    EXTRACTING = "extracting"
    MATCHING = "matching"
    DOWNLOADING = "downloading"
    TAGGING = "tagging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    owner_key: Mapped[str] = mapped_column(
        String(128),
        default=""
    )

    url: Mapped[str] = mapped_column(String(1024))

    job_type: Mapped[str] = mapped_column(
        String(50)
    )  # track, album, playlist, artist

    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus),
        default=JobStatus.PENDING
    )

    progress: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    current_track: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0
    )

    total_tracks: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0
    )

    download_speed: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    eta: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    tracks: Mapped[List["Track"]] = relationship(
        back_populates="job"
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)

    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("download_jobs.id"),
        nullable=True
    )

    title: Mapped[str] = mapped_column(
        String(512)
    )

    artist: Mapped[str] = mapped_column(
        String(512)
    )

    album: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True
    )

    duration: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    genre: Mapped[Optional[str]] = mapped_column(
        String(256),
        nullable=True
    )

    release_date: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    artwork_url: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )

    source_url: Mapped[str] = mapped_column(
        String(1024)
    )

    source_platform: Mapped[str] = mapped_column(
        String(50),
        default="unknown"
    )

    match_confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(1024),
        nullable=True
    )

    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    job: Mapped[Optional["DownloadJob"]] = relationship(
        back_populates="tracks"
    )





class ApiKey(Base):
    __tablename__ = "api_keys"

    key: Mapped[str] = mapped_column(
        String(128),
        primary_key=True
    )

    owner: Mapped[str] = mapped_column(
        String(256)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        default=True
    )

    requests_today: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    requests_total: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    daily_limit: Mapped[int] = mapped_column(
        Integer,
        default=100
    )



class CacheEntry(Base):
    __tablename__ = "cache_entries"

    key: Mapped[str] = mapped_column(
        String(512),
        primary_key=True
    )

    value: Mapped[str] = mapped_column(
        Text
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


