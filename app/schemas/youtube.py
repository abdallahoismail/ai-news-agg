"""Pydantic schemas for YouTube data validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl


class YouTubeChannel(BaseModel):
    """YouTube channel data model."""

    id: str = Field(..., description="YouTube channel ID", min_length=1)
    title: Optional[str] = Field(None, description="Channel title")
    url: str = Field(..., description="Channel URL")
    custom_url: Optional[str] = Field(None, description="Channel custom URL or handle")

    @field_validator("id")
    @classmethod
    def validate_channel_id(cls, v: str) -> str:
        """Validate channel ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Channel ID cannot be empty")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL is a YouTube URL."""
        if not v.startswith("https://www.youtube.com/"):
            raise ValueError("URL must be a valid YouTube URL")
        return v


class YouTubeTranscript(BaseModel):
    """YouTube video transcript data model."""

    text: str = Field(..., description="Full transcript text")
    language: str = Field(default="en", description="Transcript language code")
    char_count: Optional[int] = Field(None, description="Character count of transcript")

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate transcript text is not empty."""
        if not v or not v.strip():
            raise ValueError("Transcript text cannot be empty")
        return v

    def model_post_init(self, __context) -> None:
        """Calculate character count after initialization."""
        if self.char_count is None:
            self.char_count = len(self.text)


class YouTubeVideo(BaseModel):
    """YouTube video data model."""

    video_id: str = Field(..., description="YouTube video ID (11 characters)", min_length=11, max_length=11)
    title: str = Field(..., description="Video title", min_length=1)
    url: str = Field(..., description="Full video URL")
    description: Optional[str] = Field(None, description="Video description")
    published_at: datetime = Field(..., description="Video publication date and time")
    channel_id: str = Field(..., description="Channel ID this video belongs to")
    channel_title: Optional[str] = Field(None, description="Channel title")
    transcript: Optional[YouTubeTranscript] = Field(None, description="Video transcript if available")

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, v: str) -> str:
        """Validate video ID format (11 characters, alphanumeric and - _)."""
        if not v or len(v) != 11:
            raise ValueError("Video ID must be exactly 11 characters")
        # YouTube video IDs are alphanumeric with - and _
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
        if not all(c in allowed_chars for c in v):
            raise ValueError("Video ID contains invalid characters")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL is a YouTube video URL."""
        if not v.startswith("https://www.youtube.com/watch?v="):
            raise ValueError("URL must be a valid YouTube video URL")
        return v

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, v: str) -> str:
        """Validate channel ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Channel ID cannot be empty")
        return v.strip()

    @property
    def has_transcript(self) -> bool:
        """Check if video has a transcript."""
        return self.transcript is not None

    @property
    def transcript_length(self) -> int:
        """Get transcript character count, returns 0 if no transcript."""
        return self.transcript.char_count if self.transcript else 0
