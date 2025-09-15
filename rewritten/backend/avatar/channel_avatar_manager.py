import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .background_remover import BackgroundRemover, validate_and_process_avatar
from .golden_ratio_generator import GoldenRatioAvatarGenerator


class ChannelAvatarManager:
    """Manages channel avatars with automatic generation and background removal."""

    def __init__(self, db_path: str = None):
        self.db_path = (
            db_path or "/Users/thomasbrianreynolds/online production/right_perspective.db"
# BRACKET_SURGEON: disabled
#         )
        self.logger = logging.getLogger(__name__)
        self.avatar_generator = GoldenRatioAvatarGenerator()
        self.background_remover = BackgroundRemover()

        # Ensure avatar directory exists
        self.avatar_dir = Path("/Users/thomasbrianreynolds/online production/static/avatars")
        self.avatar_dir.mkdir(parents=True, exist_ok=True)

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_channel_avatar(self, channel_id: int) -> Optional[Dict]:
        """Get avatar for a specific channel, generating one if missing."""

        Args:
            channel_id: ID of the channel

        Returns:
            Dictionary with avatar information or None if channel doesn't exist'
        """"""
        try:
            with self._get_db_connection() as conn:
                # Check if channel exists
                channel = conn.execute(
                    "SELECT * FROM channels WHERE id = ?", (channel_id,)
                ).fetchone()

                if not channel:
                    self.logger.warning(f"Channel {channel_id} not found")
                    return None

                # Check for existing avatar
                avatar = conn.execute(
                    "SELECT * FROM avatars WHERE channel_id = ? AND is_default = 1",
                    (channel_id,),
                ).fetchone()

                if avatar:
                    return dict(avatar)

                # No avatar found, generate one automatically
                self.logger.info(
                    f"No avatar found for channel {channel_id}, generating golden ratio avatar"
# BRACKET_SURGEON: disabled
#                 )
                return self._generate_default_avatar(channel_id, channel["channel_name"])

        except Exception as e:
            self.logger.error(f"Error getting channel avatar: {e}")
            return None

    def _generate_default_avatar(self, channel_id: int, channel_name: str) -> Dict:
        """Generate a default avatar using golden ratio principles."""

        Args:
            channel_id: ID of the channel
            channel_name: Name of the channel for personalization

        Returns:
            Dictionary with generated avatar information
        """"""
        try:
            # Generate avatar configuration based on channel name
            avatar_config = self._create_avatar_config_from_name(channel_name)

            # Generate the avatar
            avatar_data = self.avatar_generator.generate_avatar(
                style=avatar_config["style"],
                color_scheme=avatar_config["color_scheme"],
                size=avatar_config["size"],
                customizations=avatar_config["customizations"],
# BRACKET_SURGEON: disabled
#             )

            # Save avatar to database
            avatar_id = self._save_avatar_to_db(
                channel_id=channel_id,
                avatar_data=avatar_data,
                is_default=True,
                generation_method="golden_ratio_auto",
# BRACKET_SURGEON: disabled
#             )

            # Save avatar file
            avatar_filename = f"channel_{channel_id}_default.png"
            avatar_path = self.avatar_dir / avatar_filename

            with open(avatar_path, "wb") as f:
                f.write(avatar_data["image_bytes"])

            return {
                "id": avatar_id,
                "channel_id": channel_id,
                "avatar_path": str(avatar_path),
                "avatar_url": f"/static/avatars/{avatar_filename}",
                "is_default": True,
                "generation_method": "golden_ratio_auto",
                "config": avatar_config,
                "created_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            self.logger.error(f"Error generating default avatar: {e}")
            raise

    def _create_avatar_config_from_name(self, channel_name: str) -> Dict:
        """Create avatar configuration based on channel name characteristics."""

        Args:
            channel_name: Name of the channel

        Returns:
            Avatar configuration dictionary
        """"""
        # Create a hash from the channel name for consistent generation
        name_hash = hashlib.md5(channel_name.encode()).hexdigest()

        # Use hash to determine style characteristics
        hash_int = int(name_hash[:8], 16)

        # Available styles and color schemes
        styles = ["geometric", "organic", "professional", "artistic", "minimal"]
        color_schemes = [
            "monochrome",
            "complementary",
            "triadic",
            "warm",
            "cool",
            "vibrant",
# BRACKET_SURGEON: disabled
#         ]

        # Deterministic selection based on hash
        style = styles[hash_int % len(styles)]
        color_scheme = color_schemes[(hash_int >> 4) % len(color_schemes)]

        # Size based on channel name length
        size = min(max(400, len(channel_name) * 20), 800)

        # Customizations based on name characteristics
        customizations = {
            "complexity": 0.6 + (hash_int % 100) / 250,  # 0.6 to 1.0
            "symmetry": 0.7 + (hash_int % 50) / 166,  # 0.7 to 1.0
            "golden_ratio_emphasis": 0.8,
            "transparency": True,
            "border_style": "none" if len(channel_name) < 10 else "subtle",
            "texture": "smooth" if "tech" in channel_name.lower() else "organic",
# BRACKET_SURGEON: disabled
#         }

        return {
            "style": style,
            "color_scheme": color_scheme,
            "size": size,
            "customizations": customizations,
            "generation_seed": name_hash[:16],
# BRACKET_SURGEON: disabled
#         }

    def _save_avatar_to_db(
        self,
        channel_id: int,
        avatar_data: Dict,
        is_default: bool = False,
        generation_method: str = "manual",
# BRACKET_SURGEON: disabled
#     ) -> int:
        """Save avatar information to database."""

        Args:
            channel_id: ID of the channel
            avatar_data: Avatar data from generator
                is_default: Whether this is the default avatar
            generation_method: How the avatar was generated

        Returns:
            ID of the created avatar record
        """"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    """"""
                    INSERT INTO avatars (
                        channel_id, is_default, base_face_image,
                            generation_method, config_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ""","""
                    (
                        channel_id,
                        is_default,
                        avatar_data.get("base64_image", ""),
                        generation_method,
                        json.dumps(avatar_data.get("config", {})),
                        datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )
                return cursor.lastrowid

        except Exception as e:
            self.logger.error(f"Error saving avatar to database: {e}")
            raise

    def upload_custom_avatar(
        self, channel_id: int, image_data: str, make_default: bool = True
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """Upload and process a custom avatar image."""

        Args:
            channel_id: ID of the channel
            image_data: Base64 encoded image data
            make_default: Whether to make this the default avatar

        Returns:
            Dictionary with upload results
        """"""
        try:
            # Validate and process the image (remove background)
            processing_result = validate_and_process_avatar(image_data)

            if not processing_result["success"]:
                return {"success": False, "error": processing_result["error"]}

            # If making this the default, update existing default
            if make_default:
                with self._get_db_connection() as conn:
                    conn.execute(
                        "UPDATE avatars SET is_default = 0 WHERE channel_id = ?",
                        (channel_id,),
# BRACKET_SURGEON: disabled
#                     )

            # Save processed avatar
            avatar_data = {
                "base64_image": processing_result["processed_image"],
                "config": {
                    "upload_method": "custom_upload",
                    "background_removed": True,
                    "original_info": processing_result["original_info"],
                    "processed_info": processing_result["processed_info"],
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

            avatar_id = self._save_avatar_to_db(
                channel_id=channel_id,
                avatar_data=avatar_data,
                is_default=make_default,
                generation_method="custom_upload",
# BRACKET_SURGEON: disabled
#             )

            # Save avatar file
            avatar_filename = f"channel_{channel_id}_custom_{avatar_id}.png"
            avatar_path = self.avatar_dir / avatar_filename

            # Convert base64 to bytes and save

            import base64

            image_bytes = base64.b64decode(processing_result["processed_image"].split(",")[1])

            with open(avatar_path, "wb") as f:
                f.write(image_bytes)

            return {
                "success": True,
                "avatar_id": avatar_id,
                "avatar_url": f"/static/avatars/{avatar_filename}",
                "processing_info": processing_result,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            self.logger.error(f"Error uploading custom avatar: {e}")
            return {"success": False, "error": str(e)}

    def get_all_channel_avatars(self, channel_id: int) -> List[Dict]:
        """Get all avatars for a specific channel."""

        Args:
            channel_id: ID of the channel

        Returns:
            List of avatar dictionaries
        """"""
        try:
            with self._get_db_connection() as conn:
                avatars = conn.execute(
                    """"""
                    SELECT * FROM avatars
                    WHERE channel_id = ?
                    ORDER BY is_default DESC, created_at DESC
                    ""","""
                    (channel_id,),
                ).fetchall()

                return [dict(avatar) for avatar in avatars]

        except Exception as e:
            self.logger.error(f"Error getting channel avatars: {e}")
            return []

    def set_default_avatar(self, channel_id: int, avatar_id: int) -> bool:
        """Set a specific avatar as the default for a channel."""

        Args:
            channel_id: ID of the channel
            avatar_id: ID of the avatar to make default

        Returns:
            True if successful, False otherwise
        """"""
        try:
            with self._get_db_connection() as conn:
                # First, remove default status from all avatars for this channel
                conn.execute(
                    "UPDATE avatars SET is_default = 0 WHERE channel_id = ?",
                    (channel_id,),
# BRACKET_SURGEON: disabled
#                 )

                # Set the specified avatar as default
                cursor = conn.execute(
                    "UPDATE avatars SET is_default = 1 WHERE id = ? AND channel_id = ?",
                    (avatar_id, channel_id),
# BRACKET_SURGEON: disabled
#                 )

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Error setting default avatar: {e}")
            return False

    def delete_avatar(self, channel_id: int, avatar_id: int) -> bool:
        """Delete an avatar (cannot delete if it's the only one)."""

        Args:
            channel_id: ID of the channel
            avatar_id: ID of the avatar to delete

        Returns:
            True if successful, False otherwise
        """"""
        try:
            with self._get_db_connection() as conn:
                # Check if this is the only avatar
                avatar_count = conn.execute(
                    "SELECT COUNT(*) as count FROM avatars WHERE channel_id = ?",
                    (channel_id,),
                ).fetchone()["count"]

                if avatar_count <= 1:
                    self.logger.warning(f"Cannot delete the only avatar for channel {channel_id}")
                    return False

                # Get avatar info before deletion
                avatar = conn.execute(
                    "SELECT * FROM avatars WHERE id = ? AND channel_id = ?",
                    (avatar_id, channel_id),
                ).fetchone()

                if not avatar:
                    return False

                # Delete from database
                cursor = conn.execute(
                    "DELETE FROM avatars WHERE id = ? AND channel_id = ?",
                    (avatar_id, channel_id),
# BRACKET_SURGEON: disabled
#                 )

                # If this was the default avatar, make another one default
                if avatar["is_default"]:
                    remaining_avatar = conn.execute(
                        "SELECT id FROM avatars WHERE channel_id = ? LIMIT 1",
                        (channel_id,),
                    ).fetchone()

                    if remaining_avatar:
                        conn.execute(
                            "UPDATE avatars SET is_default = 1 WHERE id = ?",
                            (remaining_avatar["id"],),
# BRACKET_SURGEON: disabled
#                         )

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Error deleting avatar: {e}")
            return False

    def regenerate_avatar(
        self, channel_id: int, style: str = None, color_scheme: str = None
# BRACKET_SURGEON: disabled
#     ) -> Dict:
        """Regenerate the default avatar for a channel."""

        Args:
            channel_id: ID of the channel
            style: Optional style override
            color_scheme: Optional color scheme override

        Returns:
            Dictionary with regeneration results
        """"""
        try:
            # Get channel info
            with self._get_db_connection() as conn:
                channel = conn.execute(
                    "SELECT * FROM channels WHERE id = ?", (channel_id,)
                ).fetchone()

                if not channel:
                    return {"success": False, "error": "Channel not found"}

            # Create new avatar config
            avatar_config = self._create_avatar_config_from_name(channel["channel_name"])

            # Apply overrides if provided
            if style:
                avatar_config["style"] = style
            if color_scheme:
                avatar_config["color_scheme"] = color_scheme

            # Generate new avatar
            avatar_data = self.avatar_generator.generate_avatar(
                style=avatar_config["style"],
                color_scheme=avatar_config["color_scheme"],
                size=avatar_config["size"],
                customizations=avatar_config["customizations"],
# BRACKET_SURGEON: disabled
#             )

            # Remove old default avatar
            with self._get_db_connection() as conn:
                conn.execute(
                    "UPDATE avatars SET is_default = 0 WHERE channel_id = ?",
                    (channel_id,),
# BRACKET_SURGEON: disabled
#                 )

            # Save new avatar
            avatar_id = self._save_avatar_to_db(
                channel_id=channel_id,
                avatar_data=avatar_data,
                is_default=True,
                generation_method="golden_ratio_regenerated",
# BRACKET_SURGEON: disabled
#             )

            # Save avatar file
            avatar_filename = f"channel_{channel_id}_regen_{avatar_id}.png"
            avatar_path = self.avatar_dir / avatar_filename

            with open(avatar_path, "wb") as f:
                f.write(avatar_data["image_bytes"])

            return {
                "success": True,
                "avatar_id": avatar_id,
                "avatar_url": f"/static/avatars/{avatar_filename}",
                "config": avatar_config,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            self.logger.error(f"Error regenerating avatar: {e}")
            return {"success": False, "error": str(e)}

    def ensure_all_channels_have_avatars(self) -> Dict:
        """Ensure all channels have at least one avatar, generating if needed."""

        Returns:
            Dictionary with processing results
        """"""
        try:
            with self._get_db_connection() as conn:
                # Get all channels without avatars
                channels_without_avatars = conn.execute(
                    """"""
                    SELECT c.* FROM channels c
                    LEFT JOIN avatars a ON c.id = a.channel_id
                    WHERE a.id IS NULL
                    """"""
                ).fetchall()

                results = {"processed_channels": [], "errors": [], "total_processed": 0}

                for channel in channels_without_avatars:
                    try:
                        avatar_info = self._generate_default_avatar(
                            channel["id"], channel["channel_name"]
# BRACKET_SURGEON: disabled
#                         )

                        results["processed_channels"].append(
                            {
                                "channel_id": channel["id"],
                                "channel_name": channel["channel_name"],
                                "avatar_info": avatar_info,
# BRACKET_SURGEON: disabled
#                             }
# BRACKET_SURGEON: disabled
#                         )

                        results["total_processed"] += 1

                    except Exception as e:
                        results["errors"].append(
                            {
                                "channel_id": channel["id"],
                                "channel_name": channel["channel_name"],
                                "error": str(e),
# BRACKET_SURGEON: disabled
#                             }
# BRACKET_SURGEON: disabled
#                         )

                return results

        except Exception as e:
            self.logger.error(f"Error ensuring all channels have avatars: {e}")
            return {
                "processed_channels": [],
                "errors": [{"error": str(e)}],
                "total_processed": 0,
# BRACKET_SURGEON: disabled
#             }


# Utility functions for easy integration


def get_or_create_channel_avatar(channel_id: int) -> Optional[Dict]:
    """Quick function to get or create a channel avatar."""

    Args:
        channel_id: ID of the channel

    Returns:
        Avatar information dictionary
    """"""
    manager = ChannelAvatarManager()
    return manager.get_channel_avatar(channel_id)


def upload_and_process_avatar(channel_id: int, image_data: str) -> Dict:
    """Quick function to upload and process a custom avatar."""

    Args:
        channel_id: ID of the channel
        image_data: Base64 encoded image data

    Returns:
        Upload results dictionary
    """"""
    manager = ChannelAvatarManager()
    return manager.upload_custom_avatar(channel_id, image_data)