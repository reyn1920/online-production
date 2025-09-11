#!/usr / bin / env python3
"""
TRAE.AI YouTube Integration Module

Provides secure YouTube API integration with authentication, video upload,
analytics, and comprehensive error handling for automated content management.

Features:
- OAuth 2.0 authentication with secure credential management
- Video upload with metadata and thumbnail support
- Channel analytics and performance tracking
- Playlist management and video organization
- Comprehensive logging and error handling

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore


class VideoPrivacy(Enum):
    """Video privacy settings."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    SCHEDULED = "scheduled"


class VideoCategory(Enum):
    """YouTube video categories."""

    FILM_ANIMATION = "1"
    AUTOS_VEHICLES = "2"
    MUSIC = "10"
    PETS_ANIMALS = "15"
    SPORTS = "17"
    TRAVEL_EVENTS = "19"
    GAMING = "20"
    PEOPLE_BLOGS = "22"
    COMEDY = "23"
    ENTERTAINMENT = "24"
    NEWS_POLITICS = "25"
    HOWTO_STYLE = "26"
    EDUCATION = "27"
    SCIENCE_TECHNOLOGY = "28"

@dataclass


class VideoMetadata:
    """Metadata for YouTube video uploads."""

    title: str
    description: str
    tags: List[str]
    category_id: str = VideoCategory.EDUCATION.value
    privacy_status: str = VideoPrivacy.PUBLIC.value
    thumbnail_path: Optional[str] = None
    scheduled_publish_time: Optional[datetime] = None
    default_language: str = "en"
    default_audio_language: str = "en"

@dataclass


class UploadResult:
    """Result from video upload operation."""

    status: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    upload_time: Optional[str] = None
    privacy_status: Optional[str] = None
    error: Optional[str] = None
    processing_status: Optional[str] = None

@dataclass


class ChannelAnalytics:
    """YouTube channel analytics data."""

    subscriber_count: int
    view_count: int
    video_count: int
    estimated_minutes_watched: int
    average_view_duration: float
    subscriber_gained: int
    subscriber_lost: int
    likes: int
    dislikes: int
    shares: int
    comments: int


class YouTubeIntegration:
    """
    Comprehensive YouTube API integration with secure authentication,
        video upload, and analytics capabilities.
    """


    def __init__(self, secrets_db_path: str = "data / secrets.sqlite"):
        self.logger = setup_logger("youtube_integration")
        self.secret_store = SecretStore(secrets_db_path)
        self.credentials = self._load_credentials()

        # API configuration
        self.base_url = "https://www.googleapis.com / youtube / v3"
        self.upload_url = "https://www.googleapis.com / upload / youtube / v3"
        self.oauth_url = "https://oauth2.googleapis.com / token"

        # Service initialization
        self.youtube_service = None
        self._initialize_service()

        # Configure HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total = 3, backoff_factor = 2, status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries = retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.logger.info("YouTube integration initialized successfully")


    def _load_credentials(self) -> Dict[str, str]:
        """Load YouTube API credentials from secure storage."""
        try:
            with self.secret_store as store:
                credentials = {
                    "api_key": store.get_secret("YOUTUBE_API_KEY"),
                        "client_id": store.get_secret("YOUTUBE_CLIENT_ID"),
                        "client_secret": store.get_secret("YOUTUBE_CLIENT_SECRET"),
                        "refresh_token": store.get_secret("YOUTUBE_REFRESH_TOKEN"),
                        "access_token": store.get_secret("YOUTUBE_ACCESS_TOKEN"),
                        }

                missing_creds = [k for k, v in credentials.items() if not v]
                if missing_creds:
                    self.logger.warning(f"Missing YouTube credentials: {missing_creds}")

                return credentials

        except Exception as e:
            self.logger.error(f"Failed to load YouTube credentials: {e}")
            return {}


    def _initialize_service(self) -> bool:
        """Initialize YouTube service with OAuth authentication."""
        try:
            if not self.credentials.get("access_token"):
                self.logger.warning(
                    "No access token available, service not initialized"
                )
                return False

            # Verify token validity
            if not self._verify_access_token():
                if not self._refresh_access_token():
                    self.logger.error("Failed to refresh access token")
                    return False

            # Initialize the YouTube API service
            # Create credentials object
            creds = Credentials(
                token = self.credentials["access_token"],
                    refresh_token = self.credentials.get("refresh_token"),
                    token_uri="https://oauth2.googleapis.com / token",
                    client_id = self.credentials.get("client_id"),
                    client_secret = self.credentials.get("client_secret"),
                    )

            # Build the YouTube service
            self.youtube_service = build("youtube", "v3", credentials = creds)
            self.logger.info("YouTube service initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize YouTube service: {e}")
            return False


    def _verify_access_token(self) -> bool:
        """Verify if the current access token is valid."""
        try:
            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Accept": "application / json",
                    }

            response = self.session.get(
                f"{self.base_url}/channels",
                    headers = headers,
                    params={"part": "id", "mine": "true"},
                    timeout = 10,
                    )

            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            return False


    def _refresh_access_token(self) -> bool:
        """Refresh the access token using the refresh token."""
        try:
            if not self.credentials.get("refresh_token"):
                self.logger.error("No refresh token available")
                return False

            data = {
                "client_id": self.credentials["client_id"],
                    "client_secret": self.credentials["client_secret"],
                    "refresh_token": self.credentials["refresh_token"],
                    "grant_type": "refresh_token",
                    }

            response = self.session.post(self.oauth_url, data = data, timeout = 10)

            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data["access_token"]

                # Store new access token
                with self.secret_store as store:
                    store.store_secret("YOUTUBE_ACCESS_TOKEN", new_access_token)

                self.credentials["access_token"] = new_access_token
                self.logger.info("Access token refreshed successfully")
                return True
            else:
                self.logger.error(f"Token refresh failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to refresh access token: {e}")
            return False


    def upload_video(self, video_path: str, metadata: VideoMetadata) -> Dict[str, Any]:
        """Upload video to YouTube with real API integration using MediaFileUpload."""
        try:
            if not self.youtube_service:
                return {"status": "failed", "error": "YouTube service not initialized"}

            if not os.path.exists(video_path):
                return UploadResult(
                    status="failed", error = f"Video file not found: {video_path}"
                )

            # Prepare video metadata
            body = {
                "snippet": {
                    "title": metadata.title,
                        "description": metadata.description,
                        "tags": metadata.tags,
                        "categoryId": metadata.category_id,
                        "defaultLanguage": metadata.default_language,
                        "defaultAudioLanguage": metadata.default_audio_language,
                        },
                    "status": {
                    "privacyStatus": metadata.privacy_status,
                        "selfDeclaredMadeForKids": False,
                        },
                    }

            # Add scheduled publish time if provided
            if (
                metadata.scheduled_publish_time
                and metadata.privacy_status == VideoPrivacy.SCHEDULED.value
            ):
                body["status"]["publishAt"] = (
                    metadata.scheduled_publish_time.isoformat() + "Z"
                )

            # Create MediaFileUpload object
            media = MediaFileUpload(
                video_path, chunksize=-1, resumable = True  # Upload in a single request
            )

            if not os.path.exists(video_path):
                return {
                    "status": "failed",
                        "error": f"Video file not found at {video_path}",
                        }
            media = MediaFileUpload(video_path, chunksize=-1, resumable = True)

            request = self.youtube_service.videos().insert(
                part=",".join(body.keys()), body = body, media_body = media
            )

            response = request.execute()

            # Upload custom thumbnail if provided
            if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
                self._upload_thumbnail(response["id"], metadata.thumbnail_path)

            return {
                "status": "uploaded",
                    "video_id": response.get("id"),
                    "title": response["snippet"]["title"],
                    "upload_time": datetime.now().isoformat(),
                    "privacy_status": response["status"]["privacyStatus"],
                    }
        except Exception as e:
            return {"status": "upload_failed", "error": str(e)}


    def _resumable_upload(
        self, video_path: str, metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform resumable upload for large video files."""
        try:
            # Step 1: Initiate resumable upload
            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Content - Type": "application / json",
                    "X - Upload - Content - Type": "video/*",
                    "X - Upload - Content - Length": str(os.path.getsize(video_path)),
                    }

            params = {"uploadType": "resumable", "part": "snippet,status"}

            response = self.session.post(
                f"{self.upload_url}/videos",
                    headers = headers,
                    params = params,
                    json = metadata,
                    timeout = 30,
                    )

            if response.status_code != 200:
                raise Exception(f"Upload initiation failed: {response.status_code}")

            upload_url = response.headers.get("Location")
            if not upload_url:
                raise Exception("No upload URL received")

            # Step 2: Upload video file
            with open(video_path, "rb") as video_file:
                file_size = os.path.getsize(video_path)
                chunk_size = 8 * 1024 * 1024  # 8MB chunks

                uploaded = 0
                while uploaded < file_size:
                    chunk_end = min(uploaded + chunk_size - 1, file_size - 1)
                    chunk_data = video_file.read(chunk_size)

                    headers = {
                        "Content - Range": f"bytes {uploaded}-{chunk_end}/{file_size}",
                            "Content - Type": "video/*",
                            }

                    response = self.session.put(
                        upload_url,
                            headers = headers,
                            data = chunk_data,
                            timeout = 300,  # 5 minutes for chunk upload
                    )

                    if response.status_code == 200:
                        # Upload complete
                        result = response.json()
                        return {
                            "status": "uploaded",
                                "video_id": result["id"],
                                "processing_status": result.get("status", {}).get(
                                "uploadStatus"
                            ),
                                }
                    elif response.status_code == 308:
                        # Continue upload
                        uploaded = chunk_end + 1
                        self.logger.info(
                            f"Upload progress: {uploaded}/{file_size} bytes"
                        )
                    else:
                        raise Exception(f"Upload chunk failed: {response.status_code}")

            raise Exception("Upload completed but no success response received")

        except Exception as e:
            self.logger.error(f"Resumable upload failed: {e}")
            return {"status": "failed", "error": str(e)}


    def _upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Upload custom thumbnail for a video using Google API client."""
        try:
            if not os.path.exists(thumbnail_path):
                self.logger.error(f"Thumbnail file not found: {thumbnail_path}")
                return False

            # Create MediaFileUpload for thumbnail
            media = MediaFileUpload(
                thumbnail_path, mimetype="image / jpeg", resumable = False
            )

            # Upload thumbnail using YouTube API
            request = self.youtube_service.thumbnails().set(
                videoId = video_id, media_body = media
            )

            response = request.execute()

            self.logger.info(f"Thumbnail uploaded successfully for video {video_id}")
            return True

        except HttpError as e:
            self.logger.error(f"YouTube API error during thumbnail upload: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Thumbnail upload failed: {e}")
            return False


    def get_channel_analytics(
        self, start_date: datetime, end_date: datetime
    ) -> Optional[ChannelAnalytics]:
        """Fetch channel analytics for a date range."""
        try:
            if not self.youtube_service:
                self.logger.error("YouTube service not initialized")
                return None

            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Accept": "application / json",
                    }

            # Get channel statistics
            response = self.session.get(
                f"{self.base_url}/channels",
                    headers = headers,
                    params={"part": "statistics", "mine": "true"},
                    timeout = 10,
                    )

            if response.status_code != 200:
                raise Exception(f"Analytics request failed: {response.status_code}")

            data = response.json()
            if not data.get("items"):
                raise Exception("No channel data found")

            stats = data["items"][0]["statistics"]

            # Get additional analytics data from YouTube Analytics API
            analytics_data = self._fetch_analytics_data(start_date, end_date)

            return ChannelAnalytics(
                subscriber_count = int(stats.get("subscriberCount", 0)),
                    view_count = int(stats.get("viewCount", 0)),
                    video_count = int(stats.get("videoCount", 0)),
                    estimated_minutes_watched = analytics_data.get(
                    "estimatedMinutesWatched", 0
                ),
                    average_view_duration = analytics_data.get("averageViewDuration", 0.0),
                    subscriber_gained = analytics_data.get("subscribersGained", 0),
                    subscriber_lost = analytics_data.get("subscribersLost", 0),
                    likes = analytics_data.get("likes", 0),
                    dislikes = analytics_data.get("dislikes", 0),
                    shares = analytics_data.get("shares", 0),
                    comments = analytics_data.get("comments", 0),
                    )

        except Exception as e:
            self.logger.error(f"Failed to fetch channel analytics: {e}")
            return None


    def _fetch_analytics_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch detailed analytics data from YouTube Analytics API."""
        try:
            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Accept": "application / json",
                    }

            # Format dates for API
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Get analytics data
            response = self.session.get(
                "https://youtubeanalytics.googleapis.com / v2 / reports",
                    headers = headers,
                    params={
                    "ids": "channel == MINE",
                        "startDate": start_str,
                        "endDate": end_str,
                        "metrics": "estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,dislikes,shares,comments",
                        "dimensions": "day",
                        },
                    timeout = 10,
                    )

            if response.status_code == 200:
                data = response.json()
                rows = data.get("rows", [])

                if rows:
                    # Aggregate data across the date range
                    totals = {
                        "estimatedMinutesWatched": sum(
                            row[1] for row in rows if len(row) > 1
                        ),
                            "averageViewDuration": sum(
                            row[2] for row in rows if len(row) > 2
                        )
                        / len(rows),
                            "subscribersGained": sum(
                            row[3] for row in rows if len(row) > 3
                        ),
                            "subscribersLost": sum(row[4] for row in rows if len(row) > 4),
                            "likes": sum(row[5] for row in rows if len(row) > 5),
                            "dislikes": sum(row[6] for row in rows if len(row) > 6),
                            "shares": sum(row[7] for row in rows if len(row) > 7),
                            "comments": sum(row[8] for row in rows if len(row) > 8),
                            }
                    return totals

            # Return empty data if API call fails or no data available
            return {
                "estimatedMinutesWatched": 0,
                    "averageViewDuration": 0.0,
                    "subscribersGained": 0,
                    "subscribersLost": 0,
                    "likes": 0,
                    "dislikes": 0,
                    "shares": 0,
                    "comments": 0,
                    }

        except Exception as e:
            self.logger.error(f"Failed to fetch analytics data: {e}")
            return {
                "estimatedMinutesWatched": 0,
                    "averageViewDuration": 0.0,
                    "subscribersGained": 0,
                    "subscribersLost": 0,
                    "likes": 0,
                    "dislikes": 0,
                    "shares": 0,
                    "comments": 0,
                    }


    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific video."""
        try:
            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Accept": "application / json",
                    }

            response = self.session.get(
                f"{self.base_url}/videos",
                    headers = headers,
                    params={
                    "part": "snippet,statistics,status,contentDetails",
                        "id": video_id,
                        },
                    timeout = 10,
                    )

            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    return data["items"][0]

            return None

        except Exception as e:
            self.logger.error(f"Failed to get video details: {e}")
            return None


    def update_video_metadata(self, video_id: str, metadata: VideoMetadata) -> bool:
        """Update metadata for an existing video."""
        try:
            if not self.youtube_service:
                self.logger.error("YouTube service not initialized")
                return False

            headers = {
                "Authorization": f'Bearer {self.credentials["access_token"]}',
                    "Content - Type": "application / json",
                    }

            update_data = {
                "id": video_id,
                    "snippet": {
                    "title": metadata.title,
                        "description": metadata.description,
                        "tags": metadata.tags,
                        "categoryId": metadata.category_id,
                        },
                    "status": {"privacyStatus": metadata.privacy_status},
                    }

            response = self.session.put(
                f"{self.base_url}/videos",
                    headers = headers,
                    params={"part": "snippet,status"},
                    json = update_data,
                    timeout = 30,
                    )

            if response.status_code == 200:
                self.logger.info(f"Video metadata updated successfully: {video_id}")
                return True
            else:
                self.logger.error(f"Video update failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to update video metadata: {e}")
            return False


    def delete_video(self, video_id: str) -> bool:
        """Delete a video from YouTube."""
        try:
            if not self.youtube_service:
                self.logger.error("YouTube service not initialized")
                return False

            headers = {"Authorization": f'Bearer {self.credentials["access_token"]}'}

            response = self.session.delete(
                f"{self.base_url}/videos",
                    headers = headers,
                    params={"id": video_id},
                    timeout = 30,
                    )

            if response.status_code == 204:
                self.logger.info(f"Video deleted successfully: {video_id}")
                return True
            else:
                self.logger.error(f"Video deletion failed: {response.status_code}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to delete video: {e}")
            return False


    def search_videos(self, query: str, max_results: int = 25) -> List[Dict[str, Any]]:
        """Search for videos on YouTube."""
        try:
            params = {
                "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": max_results,
                    "key": self.credentials.get("api_key"),
                    }

            response = self.session.get(
                f"{self.base_url}/search", params = params, timeout = 10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            else:
                self.logger.error(f"Video search failed: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Failed to search videos: {e}")
            return []


    def get_video_comments(
        self, video_id: str, max_results: int = 100, order: str = "time"
    ) -> List[Dict[str, Any]]:
        """Fetch comments for a specific video.

        Args:
            video_id: YouTube video ID
            max_results: Maximum number of comments to fetch (default: 100)
            order: Sort order - 'time', 'relevance' (default: 'time')

        Returns:
            List of comment data dictionaries
        """
        comments = []

        try:
            if not self.youtube_service:
                self.logger.error("YouTube service not initialized")
                return comments

            # Fetch comment threads
            request = self.youtube_service.commentThreads().list(
                part="snippet,replies",
                    videoId = video_id,
                    maxResults = min(max_results, 100),  # API limit is 100
                order = order,
                    textFormat="plainText",
                    )

            response = request.execute()

            for item in response.get("items", []):
                comment_data = {
                    "id": item["id"],
                        "snippet": item["snippet"],
                        "replies": item.get("replies", {}).get("comments", []),
                        }
                comments.append(comment_data)

            # Handle pagination if more results needed
            while "nextPageToken" in response and len(comments) < max_results:
                request = self.youtube_service.commentThreads().list(
                    part="snippet,replies",
                        videoId = video_id,
                        maxResults = min(max_results - len(comments), 100),
                        order = order,
                        textFormat="plainText",
                        pageToken = response["nextPageToken"],
                        )

                response = request.execute()

                for item in response.get("items", []):
                    comment_data = {
                        "id": item["id"],
                            "snippet": item["snippet"],
                            "replies": item.get("replies", {}).get("comments", []),
                            }
                    comments.append(comment_data)

            self.logger.info(f"Fetched {len(comments)} comments for video {video_id}")
            return comments

        except HttpError as e:
            self.logger.error(f"HTTP error fetching comments: {e}")
            return comments
        except Exception as e:
            self.logger.error(f"Failed to fetch comments for video {video_id}: {e}")
            return comments


    def post_comment_reply(
        self, parent_comment_id: str, reply_text: str
    ) -> Dict[str, Any]:
        """Post a reply to a comment.

        Args:
            parent_comment_id: ID of the parent comment to reply to
            reply_text: Text content of the reply

        Returns:
            Dictionary with status and comment details
        """
        try:
            if not self.youtube_service:
                return {"status": "failed", "error": "YouTube service not initialized"}

            if not reply_text.strip():
                return {"status": "failed", "error": "Reply text cannot be empty"}

            # Prepare comment body
            comment_body = {
                "snippet": {"parentId": parent_comment_id, "textOriginal": reply_text}
            }

            # Post the reply
            request = self.youtube_service.comments().insert(
                part="snippet", body = comment_body
            )

            response = request.execute()

            self.logger.info(
                f"Successfully posted reply to comment {parent_comment_id}"
            )

            return {
                "status": "success",
                    "comment_id": response["id"],
                    "text": response["snippet"]["textOriginal"],
                    "published_at": response["snippet"]["publishedAt"],
                    "parent_id": parent_comment_id,
                    }

        except HttpError as e:
            error_details = (
                e.content.decode("utf - 8") if hasattr(e, "content") else str(e)
            )
            self.logger.error(f"HTTP error posting comment reply: {error_details}")
            return {"status": "failed", "error": f"HTTP error: {error_details}"}
        except Exception as e:
            self.logger.error(f"Failed to post comment reply: {e}")
            return {"status": "failed", "error": str(e)}


    def post_video_comment(self, video_id: str, comment_text: str) -> Dict[str, Any]:
        """Post a top - level comment on a video.

        Args:
            video_id: YouTube video ID
            comment_text: Text content of the comment

        Returns:
            Dictionary with status and comment details
        """
        try:
            if not self.youtube_service:
                return {"status": "failed", "error": "YouTube service not initialized"}

            if not comment_text.strip():
                return {"status": "failed", "error": "Comment text cannot be empty"}

            # Prepare comment thread body
            comment_thread_body = {
                "snippet": {
                    "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": comment_text}},
                        }
            }

            # Post the comment
            request = self.youtube_service.commentThreads().insert(
                part="snippet", body = comment_thread_body
            )

            response = request.execute()

            self.logger.info(f"Successfully posted comment on video {video_id}")

            top_level_comment = response["snippet"]["topLevelComment"]

            return {
                "status": "success",
                    "comment_id": top_level_comment["id"],
                    "thread_id": response["id"],
                    "text": top_level_comment["snippet"]["textOriginal"],
                    "published_at": top_level_comment["snippet"]["publishedAt"],
                    "video_id": video_id,
                    }

        except HttpError as e:
            error_details = (
                e.content.decode("utf - 8") if hasattr(e, "content") else str(e)
            )
            self.logger.error(f"HTTP error posting video comment: {error_details}")
            return {"status": "failed", "error": f"HTTP error: {error_details}"}
        except Exception as e:
            self.logger.error(f"Failed to post video comment: {e}")
            return {"status": "failed", "error": str(e)}


    def like_comment(self, comment_id: str) -> Dict[str, Any]:
        """Like a comment.

        Args:
            comment_id: ID of the comment to like

        Returns:
            Dictionary with status
        """
        try:
            if not self.youtube_service:
                return {"status": "failed", "error": "YouTube service not initialized"}

            # Set rating to 'like'
            request = self.youtube_service.comments().setRating(
                id = comment_id, rating="like"
            )

            request.execute()

            self.logger.info(f"Successfully liked comment {comment_id}")

            return {"status": "success", "comment_id": comment_id, "action": "liked"}

        except HttpError as e:
            error_details = (
                e.content.decode("utf - 8") if hasattr(e, "content") else str(e)
            )
            self.logger.error(f"HTTP error liking comment: {error_details}")
            return {"status": "failed", "error": f"HTTP error: {error_details}"}
        except Exception as e:
            self.logger.error(f"Failed to like comment: {e}")
            return {"status": "failed", "error": str(e)}


    def get_channel_comments(self, max_results: int = 100) -> List[Dict[str, Any]]:
        """Get recent comments across all channel videos.

        Args:
            max_results: Maximum number of comments to fetch

        Returns:
            List of comment data dictionaries
        """
        comments = []

        try:
            if not self.youtube_service:
                self.logger.error("YouTube service not initialized")
                return comments

            # First, get channel's recent videos
            channel_request = self.youtube_service.channels().list(
                part="contentDetails", mine = True
            )

            channel_response = channel_request.execute()

            if not channel_response.get("items"):
                self.logger.warning("No channel found")
                return comments

            uploads_playlist_id = channel_response["items"][0]["contentDetails"][
                "relatedPlaylists"
            ]["uploads"]

            # Get recent videos from uploads playlist
            playlist_request = self.youtube_service.playlistItems().list(
                part="contentDetails",
                    playlistId = uploads_playlist_id,
                    maxResults = 10,  # Check last 10 videos
            )

            playlist_response = playlist_request.execute()

            # Collect comments from recent videos
            for item in playlist_response.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_comments = self.get_video_comments(video_id, max_results = 20)
                comments.extend(video_comments)

                # Stop if we have enough comments
                if len(comments) >= max_results:
                    break

            # Sort by most recent
            comments.sort(
                key = lambda x: x["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                    reverse = True,
                    )

            return comments[:max_results]

        except Exception as e:
            self.logger.error(f"Failed to get channel comments: {e}")
            return comments


    def get_trending_videos(
        self, region_code: str = "US", category_id: str = "0"
    ) -> List[Dict[str, Any]]:
        """Get trending videos for a specific region and category."""
        try:
            params = {
                "part": "snippet,statistics",
                    "chart": "mostPopular",
                    "regionCode": region_code,
                    "videoCategoryId": category_id,
                    "maxResults": 50,
                    "key": self.credentials.get("api_key"),
                    }

            response = self.session.get(
                f"{self.base_url}/videos", params = params, timeout = 10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("items", [])
            else:
                self.logger.error(
                    f"Trending videos request failed: {response.status_code}"
                )
                return []

        except Exception as e:
            self.logger.error(f"Failed to get trending videos: {e}")
            return []
