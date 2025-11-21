"""
Standalone test script for YouTube scraper.

Run this to test the YouTube scraper without needing all environment variables:
    python test_youtube_scraper.py

Only requires: YOUTUBE_API_KEY in .env
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.schemas.youtube import YouTubeVideo, YouTubeTranscript

# Load environment variables
load_dotenv()

# Check if API key is set
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    print("Error: YOUTUBE_API_KEY not found in environment variables")
    print("Please set it in your .env file")
    exit(1)


def test_youtube_scraper():
    """Test the YouTube scraper with minimal setup."""

    print("=" * 60)
    print("Testing YouTube Scraper (Standalone)")
    print("=" * 60)

    # Initialize YouTube API client
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    transcript_api = YouTubeTranscriptApi()

    # Test channel
    channel_url = "https://www.youtube.com/@OpenAI"
    print(f"\nScraping channel: {channel_url}")
    print("-" * 60)

    try:
        # Extract channel handle
        handle = "OpenAI"

        # Search for channel
        print(f"\n[1/3] Searching for channel: {handle}")
        search_request = youtube.search().list(
            part="snippet",
            q=handle,
            type="channel",
            maxResults=1
        )
        search_response = search_request.execute()

        if not search_response["items"]:
            print("✗ Channel not found")
            return

        channel_id = search_response["items"][0]["snippet"]["channelId"]
        print(f"✓ Found channel ID: {channel_id}")

        # Get recent videos
        print(f"\n[2/3] Fetching recent videos...")
        videos_request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=3
        )
        videos_response = videos_request.execute()

        videos = videos_response.get("items", [])
        print(f"✓ Found {len(videos)} videos")

        # Process each video using Pydantic models
        print(f"\n[3/3] Processing videos and fetching transcripts...")
        video_models = []

        for i, video in enumerate(videos, 1):
            try:
                video_id = video["id"]["videoId"]
                title = video["snippet"]["title"]
                url = f"https://www.youtube.com/watch?v={video_id}"
                published_at_str = video["snippet"]["publishedAt"]
                description = video["snippet"].get("description", "")
                channel_id = video["snippet"]["channelId"]
                channel_title = video["snippet"].get("channelTitle", "")

                # Parse published date
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))

                # Try to get transcript and create Pydantic model
                transcript_model = None
                try:
                    fetched_transcript = transcript_api.fetch(video_id, languages=["en"])
                    transcript_text = " ".join([entry.text for entry in fetched_transcript])
                    # Create validated Pydantic transcript model
                    transcript_model = YouTubeTranscript(
                        text=transcript_text,
                        language="en"
                    )
                except (TranscriptsDisabled, NoTranscriptFound):
                    pass
                except Exception as e:
                    print(f"   Warning: Could not fetch transcript for video {video_id}: {e}")

                # Create validated Pydantic video model
                video_model = YouTubeVideo(
                    video_id=video_id,
                    title=title,
                    url=url,
                    description=description,
                    published_at=published_at,
                    channel_id=channel_id,
                    channel_title=channel_title,
                    transcript=transcript_model
                )

                video_models.append(video_model)

                # Display results with Pydantic model properties
                print(f"\n{'='*60}")
                print(f"[Video {i}] - Using Pydantic Models")
                print(f"{'='*60}")
                print(f"Title: {video_model.title}")
                print(f"URL: {video_model.url}")
                print(f"Video ID: {video_model.video_id} (validated: 11 chars)")
                print(f"Channel: {video_model.channel_title} ({video_model.channel_id})")
                print(f"Published: {video_model.published_at}")
                print(f"Has transcript: {'Yes ✓' if video_model.has_transcript else 'No ✗'}")
                if video_model.has_transcript:
                    print(f"Transcript length: {video_model.transcript_length} characters")
                    print(f"Transcript language: {video_model.transcript.language}")
                    print(f"Transcript preview: {video_model.transcript.text[:200]}...")
                print(f"\nDescription preview:")
                print(f"{video_model.description[:300]}..." if len(video_model.description or "") > 300 else video_model.description)

            except Exception as e:
                print(f"\n✗ Error creating video model: {e}")
                continue

        # Show validation summary
        print("\n" + "=" * 60)
        print(f"✓ Successfully validated {len(video_models)} videos using Pydantic models")
        print("=" * 60)

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_youtube_scraper()
