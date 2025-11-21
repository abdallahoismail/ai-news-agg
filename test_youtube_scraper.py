"""
Standalone test script for YouTube scraper.

Run this to test the YouTube scraper without needing all environment variables:
    python test_youtube_scraper.py

Only requires: YOUTUBE_API_KEY in .env
"""

# just to avoid import errors

import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from datetime import datetime

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

        # Process each video
        print(f"\n[3/3] Processing videos and fetching transcripts...")
        for i, video in enumerate(videos, 1):
            video_id = video["id"]["videoId"]
            title = video["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            published_at = video["snippet"]["publishedAt"]
            description = video["snippet"].get("description", "")

            # Try to get transcript
            transcript = None
            try:
                fetched_transcript = transcript_api.fetch(video_id, languages=["en"])
                transcript = " ".join([entry.text for entry in fetched_transcript])
            except (TranscriptsDisabled, NoTranscriptFound):
                pass
            except Exception as e:
                print(f"   Warning: Could not fetch transcript for video {video_id}: {e}")

            # Display results
            print(f"\n{'='*60}")
            print(f"[Video {i}]")
            print(f"{'='*60}")
            print(f"Title: {title}")
            print(f"URL: {url}")
            print(f"Published: {published_at}")
            print(f"Has transcript: {'Yes ✓' if transcript else 'No ✗'}")
            if transcript:
                print(f"Transcript length: {len(transcript)} characters")
                print(f"Transcript preview: {transcript[:200]}...")
            print(f"\nDescription preview:")
            print(f"{description[:300]}..." if len(description) > 300 else description)

        print("\n" + "=" * 60)
        print("✓ Test completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_youtube_scraper()
