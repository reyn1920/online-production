# chat_db.py - Chat persistence and conversation management

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatDatabase:
    """SQLite - based chat persistence system"""

    def __init__(self, db_path: str = "data / chat.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize the chat database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                            user_id TEXT,
                            title TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            metadata TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                            conversation_id TEXT,
                            role TEXT CHECK(role IN ('user', 'assistant', 'system')),
                            content TEXT,
                            message_type TEXT DEFAULT 'text',
                            metadata TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
                    )
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON messages(conversation_id, created_at)
                """
                )

                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_conversations_user
                    ON conversations(user_id, updated_at DESC)
                """
                )

                conn.commit()
                logger.info("Chat database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chat database: {e}")
            raise

    def create_conversation(self, user_id: str = "anonymous", title: str = None) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())

        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
                    (conversation_id, user_id, title),
                )
                conn.commit()

            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation_id

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_type: str = "text",
        metadata: Dict = None,
    ) -> str:
        """Add a message to a conversation"""
        message_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO messages
                       (id, conversation_id, role, content, message_type, metadata)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        message_id,
                        conversation_id,
                        role,
                        content,
                        message_type,
                        metadata_json,
                    ),
                )

                # Update conversation timestamp
                conn.execute(
                    "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (conversation_id,),
                )

                conn.commit()

            logger.debug(f"Added message {message_id} to conversation {conversation_id}")
            return message_id

        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise

    def get_conversation_messages(self, conversation_id: str, limit: int = 100) -> List[Dict]:
        """Get messages for a conversation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT id, role, content, message_type, metadata, created_at
                       FROM messages
                       WHERE conversation_id = ?
                       ORDER BY created_at ASC
                       LIMIT ?""",
                    (conversation_id, limit),
                )

                messages = []
                for row in cursor.fetchall():
                    message = dict(row)
                    if message["metadata"]:
                        message["metadata"] = json.loads(message["metadata"])
                    messages.append(message)

                return messages

        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
            return []

    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get conversations for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT id, title, created_at, updated_at, metadata
                       FROM conversations
                       WHERE user_id = ?
                       ORDER BY updated_at DESC
                       LIMIT ?""",
                    (user_id, limit),
                )

                conversations = []
                for row in cursor.fetchall():
                    conversation = dict(row)
                    if conversation["metadata"]:
                        conversation["metadata"] = json.loads(conversation["metadata"])
                    conversations.append(conversation)

                return conversations

        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []

    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE conversations SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (title, conversation_id),
                )
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to update conversation title: {e}")
            return False

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete messages first (foreign key constraint)
                conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))

                # Delete conversation
                cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
                conn.commit()

                logger.info(f"Deleted conversation {conversation_id}")
                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False

    def search_messages(self, query: str, user_id: str = None, limit: int = 50) -> List[Dict]:
        """Search messages by content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                if user_id:
                    cursor = conn.execute(
                        """SELECT m.id, m.conversation_id, m.role, m.content,
                            m.message_type, m.metadata, m.created_at, c.title
                           FROM messages m
                           JOIN conversations c ON m.conversation_id = c.id
                           WHERE m.content LIKE ? AND c.user_id = ?
                           ORDER BY m.created_at DESC
                           LIMIT ?""",
                        (f"%{query}%", user_id, limit),
                    )
                else:
                    cursor = conn.execute(
                        """SELECT m.id, m.conversation_id, m.role, m.content,
                            m.message_type, m.metadata, m.created_at, c.title
                           FROM messages m
                           JOIN conversations c ON m.conversation_id = c.id
                           WHERE m.content LIKE ?
                           ORDER BY m.created_at DESC
                           LIMIT ?""",
                        (f"%{query}%", limit),
                    )

                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    if result["metadata"]:
                        result["metadata"] = json.loads(result["metadata"])
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM conversations")
                total_conversations = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(*) FROM messages")
                total_messages = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM conversations")
                unique_users = cursor.fetchone()[0]

                return {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "unique_users": unique_users,
                    "database_size": (self.db_path.stat().st_size if self.db_path.exists() else 0),
                }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# Global database instance
chat_db = ChatDatabase()

# Utility functions for easy access


def create_conversation(user_id: str = "anonymous", title: str = None) -> str:
    """Create a new conversation"""
    return chat_db.create_conversation(user_id, title)


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    message_type: str = "text",
    metadata: Dict = None,
) -> str:
    """Add a message to conversation"""
    return chat_db.add_message(conversation_id, role, content, message_type, metadata)


def get_messages(conversation_id: str, limit: int = 100) -> List[Dict]:
    """Get conversation messages"""
    return chat_db.get_conversation_messages(conversation_id, limit)


def get_conversations(user_id: str, limit: int = 50) -> List[Dict]:
    """Get user conversations"""
    return chat_db.get_user_conversations(user_id, limit)


def search_chat(query: str, user_id: str = None, limit: int = 50) -> List[Dict]:
    """Search messages by content"""
    if not _db:
        return []
    return _db.search_messages(query, user_id, limit)
