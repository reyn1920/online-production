import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


class YouTubeIntegration:
    """YouTube API integration with secure credential management"""

    def __init__(
        self,
        secrets_db_path: str = "secrets.sqlite",
        config_path: str = "config / youtube.oauth.json",
# BRACKET_SURGEON: disabled
#     ):
        self.secrets_db_path = secrets_db_path
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.youtube_service = None
        self.credentials = None

    def _get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from the encrypted database"""
        try:
            conn = sqlite3.connect(self.secrets_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM secrets WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()

            if result:
                # In a real implementation, you'd decrypt the value here
                # For now, assuming the value is stored encrypted
                return result[0]
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving secret {key}: {e}")
            return None

    def _load_oauth_config(self) -> Dict[str, Any]:
        """Load OAuth configuration and merge with secrets from database"""
        try:
            # Load base config
            with open(self.config_path, "r") as f:
                config = json.load(f)

            # Get credentials from secrets database
            client_id = self._get_secret("YOUTUBE_CLIENT_ID")
            client_secret = self._get_secret("YOUTUBE_CLIENT_SECRET")

            if client_id and client_secret:
                # Update config with real credentials
                config["global"]["client_id"] = client_id
                config["global"]["client_secret"] = client_secret
                self.logger.info("Successfully loaded YouTube credentials from secrets database")
            else:
                self.logger.warning("YouTube credentials not found in secrets database")

            return config
        except Exception as e:
            self.logger.error(f"Error loading OAuth config: {e}")
            return {}

    def _save_oauth_config(self, config: Dict[str, Any]):
        """Save OAuth configuration back to file"""
        try:
            # Don't save the actual credentials to the config file
            config_to_save = config.copy()
            config_to_save["global"]["client_id"] = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
            config_to_save["global"]["client_secret"] = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"

            with open(self.config_path, "w") as f:
                json.dump(config_to_save, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving OAuth config: {e}")

    def get_oauth_url(self, channel_id: str) -> Optional[str]:
        """Generate OAuth URL for a specific channel"""
        try:
            config = self._load_oauth_config()
            if not config or "global" not in config:
                return None

            # Validate channel exists
            if channel_id not in config.get("channels", {}):
                self.logger.error(f"Channel {channel_id} not found in configuration")
                return None

            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": config["global"]["client_id"],
                        "client_secret": config["global"]["client_secret"],
                        "auth_uri": "https://accounts.google.com / o/oauth2 / auth",
                        "token_uri": "https://oauth2.googleapis.com / token",
                        "redirect_uris": [config["global"]["redirect_uri"]],
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 },
                scopes=config["global"]["scopes"],
# BRACKET_SURGEON: disabled
#             )

            flow.redirect_uri = config["global"]["redirect_uri"]

            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type="offline", prompt="consent", state=channel_id
# BRACKET_SURGEON: disabled
#             )

            return authorization_url

        except Exception as e:
            self.logger.error(f"Error generating OAuth URL: {e}")
            return None

    def handle_oauth_callback(self, code: str, state: str) -> bool:
        """Handle OAuth callback and store refresh token"""
        try:
            config = self._load_oauth_config()
            if not config:
                return False

            channel_id = state
            if channel_id not in config.get("channels", {}):
                self.logger.error(f"Invalid channel_id in state: {channel_id}")
                return False

            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": config["global"]["client_id"],
                        "client_secret": config["global"]["client_secret"],
                        "auth_uri": "https://accounts.google.com / o/oauth2 / auth",
                        "token_uri": "https://oauth2.googleapis.com / token",
                        "redirect_uris": [config["global"]["redirect_uri"]],
# BRACKET_SURGEON: disabled
#                     }
# BRACKET_SURGEON: disabled
#                 },
                scopes=config["global"]["scopes"],
# BRACKET_SURGEON: disabled
#             )

            flow.redirect_uri = config["global"]["redirect_uri"]

            # Exchange code for tokens
            flow.fetch_token(code=code)

            # Store refresh token
            if flow.credentials.refresh_token:
                config["channels"][channel_id]["refresh_token"] = flow.credentials.refresh_token
                config["channels"][channel_id]["authorized_at"] = datetime.now().isoformat()

                # Save updated config
                self._save_oauth_config(config)

                self.logger.info(f"Successfully authorized channel {channel_id}")
                return True
            else:
                self.logger.error("No refresh token received")
                return False

        except Exception as e:
            self.logger.error(f"Error handling OAuth callback: {e}")
            return False

    def initialize_service(self, channel_id: str) -> bool:
        """Initialize YouTube service for a specific channel"""
        try:
            config = self._load_oauth_config()
            if not config:
                return False

            if channel_id not in config.get("channels", {}):
                self.logger.error(f"Channel {channel_id} not found")
                return False

            refresh_token = config["channels"][channel_id].get("refresh_token")
            if not refresh_token:
                self.logger.error(f"No refresh token for channel {channel_id}")
                return False

            # Create credentials
            self.credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com / token",
                client_id=config["global"]["client_id"],
                client_secret=config["global"]["client_secret"],
                scopes=config["global"]["scopes"],
# BRACKET_SURGEON: disabled
#             )

            # Refresh the token
            self.credentials.refresh(Request())

            # Build YouTube service
            self.youtube_service = build("youtube", "v3", credentials=self.credentials)

            self.logger.info(f"Successfully initialized YouTube service for channel {channel_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing YouTube service: {e}")
            return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        privacy_status: str = "private",
    ) -> Optional[str]:
        """Upload video to YouTube"""
        if not self.youtube_service:
            self.logger.error("YouTube service not initialized")
            return None

        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": "22",  # People & Blogs
# BRACKET_SURGEON: disabled
#                 },
                "status": {"privacyStatus": privacy_status},
# BRACKET_SURGEON: disabled
#             }

            # Call the API's videos.insert method to create and upload the video
            insert_request = self.youtube_service.videos().insert(
                part=",".join(body.keys()), body=body, media_body=video_path
# BRACKET_SURGEON: disabled
#             )

            response = insert_request.execute()
            video_id = response["id"]

            self.logger.info(f"Successfully uploaded video: {video_id}")
            return video_id

        except Exception as e:
            self.logger.error(f"Error uploading video: {e}")
            return None

    def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the authenticated channel"""
        if not self.youtube_service:
            self.logger.error("YouTube service not initialized")
            return None

        try:
            response = (
                self.youtube_service.channels().list(part="snippet,statistics", mine=True).execute()
# BRACKET_SURGEON: disabled
#             )

            if response["items"]:
                return response["items"][0]
            return None

        except Exception as e:
            self.logger.error(f"Error getting channel info: {e}")
            return None

    def is_channel_authorized(self, channel_id: str) -> bool:
        """Check if a channel is authorized"""
        try:
            config = self._load_oauth_config()
            if not config or channel_id not in config.get("channels", {}):
                return False

            return bool(config["channels"][channel_id].get("refresh_token"))
        except Exception as e:
            self.logger.error(f"Error checking authorization status: {e}")
            return False

    def get_authorized_channels(self) -> Dict[str, Dict[str, Any]]:
        """Get list of authorized channels"""
        try:
            config = self._load_oauth_config()
            if not config:
                return {}

            authorized = {}
            for channel_id, channel_data in config.get("channels", {}).items():
                if channel_data.get("refresh_token"):
                    authorized[channel_id] = {
                        "note": channel_data.get("note", "Unknown"),
                        "authorized_at": channel_data.get("authorized_at"),
                        "authorized": True,
# BRACKET_SURGEON: disabled
#                     }
                else:
                    authorized[channel_id] = {
                        "note": channel_data.get("note", "Unknown"),
                        "authorized": False,
# BRACKET_SURGEON: disabled
#                     }

            return authorized
        except Exception as e:
            self.logger.error(f"Error getting authorized channels: {e}")
            return {}