"""YouTube channel scraper for video content."""

from datetime import datetime
from typing import List, Optional
import re

from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from pydantic import ValidationError

from app.scrapers.base import BaseScraper, ScrapedArticle
from app.schemas.youtube import YouTubeVideo, YouTubeTranscript


class YouTubeScraper(BaseScraper):
    """Scraper for YouTube channels to get recent videos and transcripts."""

    def __init__(self):
        """Initialize YouTube scraper with API client."""
        super().__init__()
        self.youtube = build(
            "youtube", "v3", developerKey=self.settings.youtube_api_key
        )
        self.transcript_api = YouTubeTranscriptApi()

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.

        Args:
            url: YouTube video or channel URL

        Returns:
            Video ID if found, None otherwise
        """
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com\/embed\/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _extract_channel_id(self, url: str) -> Optional[str]:
        """
        Extract channel ID from YouTube channel URL.

        Args:
            url: YouTube channel URL

        Returns:
            Channel ID if found, None otherwise
        """
        patterns = [
            r"youtube\.com\/channel\/([a-zA-Z0-9_-]+)",
            r"youtube\.com\/c\/([a-zA-Z0-9_-]+)",
            r"youtube\.com\/@([a-zA-Z0-9_-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                channel_identifier = match.group(1)
                # If it's a custom URL or handle, resolve to channel ID
                if "youtube.com/c/" in url or "youtube.com/@" in url:
                    return self._resolve_channel_id(channel_identifier)
                return channel_identifier
        return None

    def _resolve_channel_id(self, username: str) -> Optional[str]:
        """
        Resolve username or handle to channel ID using YouTube API.

        Args:
            username: YouTube username or handle

        Returns:
            Channel ID if found, None otherwise
        """
        try:
            request = self.youtube.search().list(
                part="snippet", q=username, type="channel", maxResults=1
            )
            response = request.execute()

            if response["items"]:
                return response["items"][0]["snippet"]["channelId"]
        except Exception as e:
            print(f"Error resolving channel ID for {username}: {e}")

        return None

    def _get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[dict]:
        """
        Get recent videos from a YouTube channel.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to retrieve

        Returns:
            List of video information dictionaries
        """
        try:
            request = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                order="date",
                type="video",
                maxResults=max_results,
            )
            response = request.execute()

            return response.get("items", [])
        except Exception as e:
            print(f"Error fetching videos for channel {channel_id}: {e}")
            return []

    def _get_video_transcript(self, video_id: str) -> Optional[YouTubeTranscript]:
        """
        Get transcript for a YouTube video.

        Args:
            video_id: YouTube video ID

        Returns:
            YouTubeTranscript model if available, None otherwise
        """
        try:
            fetched_transcript = self.transcript_api.fetch(video_id, languages=["en"])
            transcript_text = " ".join([entry.text for entry in fetched_transcript])

            # Return Pydantic model
            return YouTubeTranscript(
                text=transcript_text,
                language="en"
            )
        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception as e:
            print(f"Error fetching transcript for video {video_id}: {e}")
            return None

    def _parse_video_to_model(self, video_data: dict) -> Optional[YouTubeVideo]:
        """
        Parse YouTube API video data into a Pydantic model.

        Args:
            video_data: Raw video data from YouTube API

        Returns:
            YouTubeVideo model if parsing successful, None otherwise
        """
        try:
            video_id = video_data["id"]["videoId"]
            title = video_data["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            description = video_data["snippet"].get("description", "")
            channel_id = video_data["snippet"]["channelId"]
            channel_title = video_data["snippet"].get("channelTitle")

            # Parse published date
            published_at = datetime.fromisoformat(
                video_data["snippet"]["publishedAt"].replace("Z", "+00:00")
            )

            # Get transcript
            transcript = self._get_video_transcript(video_id)

            # Create and validate Pydantic model
            video_model = YouTubeVideo(
                video_id=video_id,
                title=title,
                url=url,
                description=description,
                published_at=published_at,
                channel_id=channel_id,
                channel_title=channel_title,
                transcript=transcript
            )

            return video_model

        except (ValidationError, KeyError) as e:
            print(f"Error parsing video data: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error parsing video: {e}")
            return None

    def scrape(
        self, source_url: str, config: Optional[dict] = None
    ) -> List[ScrapedArticle]:
        """
        Scrape recent videos from a YouTube channel.

        Args:
            source_url: YouTube channel URL
            config: Optional configuration (e.g., max_videos)

        Returns:
            List of scraped videos with titles, URLs, and transcripts
        """
        max_videos = (
            config.get("max_videos", self.settings.max_articles_per_source)
            if config
            else self.settings.max_articles_per_source
        )

        # Extract channel ID
        channel_id = self._extract_channel_id(source_url)
        if not channel_id:
            print(f"Could not extract channel ID from URL: {source_url}")
            return []

        # Get recent videos from YouTube API
        videos = self._get_channel_videos(channel_id, max_videos)

        articles = []
        for video in videos:
            try:
                # Parse video data into Pydantic model (includes validation)
                video_model = self._parse_video_to_model(video)

                if video_model is None:
                    continue

                # Convert YouTubeVideo model to ScrapedArticle for compatibility
                article = ScrapedArticle(
                    title=video_model.title,
                    url=video_model.url,
                    content=video_model.description,
                    transcript=video_model.transcript.text if video_model.transcript else None,
                    published_date=video_model.published_at,
                )

                articles.append(article)

            except Exception as e:
                print(f"Error processing video from {source_url}: {e}")
                continue

        return articles


if __name__ == "__main__":
    """
    Example usage of YouTubeScraper.

    Run this file directly to test the scraper:
        python -m app.scrapers.youtube_scraper

    Make sure you have set YOUTUBE_API_KEY in your .env file.
    """
    import os
    import sys
    from pathlib import Path
    from dotenv import load_dotenv

    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Load environment variables
    load_dotenv()

    # Check if API key is set
    if not os.getenv("YOUTUBE_API_KEY"):
        print("Error: YOUTUBE_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        exit(1)

    # Initialize scraper
    scraper = YouTubeScraper()

    # Example: Scrape OpenAI's YouTube channel
    print("=" * 60)
    print("Testing YouTube Scraper")
    print("=" * 60)

    channel_url = "https://www.youtube.com/@OpenAI"
    print(f"\nScraping channel: {channel_url}")
    print("-" * 60)

    try:
        # Scrape with custom config
        config = {"max_videos": 3}
        articles = scraper.scrape(channel_url, config)

        print(f"\n✓ Found {len(articles)} videos\n")

        # Display results
        for i, article in enumerate(articles, 1):
            print(f"\n[Video {i}]")
            print(f"Title: {article.title}")
            print(f"URL: {article.url}")
            print(f"Published: {article.published_date}")
            print(f"Has transcript: {'Yes' if article.transcript else 'No'}")
            if article.transcript:
                print(f"Transcript length: {len(article.transcript)} characters")
            print(
                f"Description: {article.content[:200]}..."
                if len(article.content) > 200
                else article.content
            )
            print("-" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        scraper.close()
        print("\n✓ Scraper closed")
