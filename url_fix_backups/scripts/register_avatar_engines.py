#!/usr / bin / env python3
"""
Avatar Engine Registration Script
Registers Linly - Talker \
    and Talking Heads as avatar generation engines in the API registry.
"""

import json
import os
import sqlite3
from datetime import datetime


def get_database_path():
    """Get the database path from environment or use default."""
    return os.getenv("DATABASE_PATH", "intelligence.db")


def register_avatar_engines():
    """Register both avatar engines in the API registry."""
    db_path = get_database_path()

    # Avatar engine configurations
    engines = [
        {
            "api_name": "linly - talker - enhanced",
                "base_url": "http://localhost:7860",  # Default Gradio port
            "api_version": "1.0",
                "capability": "avatar - generation",
                "authentication_type": "none",
                "status": "active",
                "health_check_url": "http://localhost:7860 / health",
                "health_status": "unknown",
                "allow_automatic_failover": True,
                "failover_priority": 1,  # Legacy field
            "priority": 1,  # Primary engine (highest priority)
            "configuration": json.dumps(
                {
                    "engine_type": "linly - talker",
                        "quality": "high",
                        "features": ["lip_sync", "emotion_control", "voice_cloning"],
                        "max_duration": 300,  # 5 minutes
                    "supported_formats": ["mp4", "avi"],
                        "default_voice": "default",
                        "enhancement_level": "maximum",
                        }
            ),
                "created_by": "system",
                },
            {
            "api_name": "talking - heads - fallback",
                "base_url": "http://localhost:8000",  # Alternative port
            "api_version": "1.0",
                "capability": "avatar - generation",
                "authentication_type": "none",
                "status": "active",
                "health_check_url": "http://localhost:8000 / health",
                "health_status": "unknown",
                "allow_automatic_failover": True,
                "failover_priority": 10,  # Legacy field
            "priority": 10,  # Secondary engine (lower priority)
            "configuration": json.dumps(
                {
                    "engine_type": "talking - heads",
                        "quality": "medium",
                        "features": ["basic_lip_sync", "stable_generation"],
                        "max_duration": 180,  # 3 minutes
                    "supported_formats": ["mp4"],
                        "fallback_mode": True,
                        "reliability": "high",
                        }
            ),
                "created_by": "system",
                },
            ]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if engines already exist
        for engine in engines:
            cursor.execute(
                "SELECT id FROM api_registry WHERE api_name = ?", (engine["api_name"],)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing engine
                cursor.execute(
                    """
                    UPDATE api_registry SET
                        base_url = ?,
                            api_version = ?,
                            capability = ?,
                            authentication_type = ?,
                            status = ?,
                            health_check_url = ?,
                            health_status = ?,
                            allow_automatic_failover = ?,
                            failover_priority = ?,
                            priority = ?,
                            configuration = ?,
                            updated_at = CURRENT_TIMESTAMP
                    WHERE api_name = ?
                """,
                    (
                        engine["base_url"],
                            engine["api_version"],
                            engine["capability"],
                            engine["authentication_type"],
                            engine["status"],
                            engine["health_check_url"],
                            engine["health_status"],
                            engine["allow_automatic_failover"],
                            engine["failover_priority"],
                            engine["priority"],
                            engine["configuration"],
                            engine["api_name"],
                            ),
                        )
                print(f"✅ Updated existing avatar engine: {engine['api_name']}")
            else:
                # Insert new engine
                cursor.execute(
                    """
                    INSERT INTO api_registry (
                        api_name, base_url, api_version, capability,
                            authentication_type, status, health_check_url,
                            health_status, allow_automatic_failover,
                            failover_priority, priority, configuration, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        engine["api_name"],
                            engine["base_url"],
                            engine["api_version"],
                            engine["capability"],
                            engine["authentication_type"],
                            engine["status"],
                            engine["health_check_url"],
                            engine["health_status"],
                            engine["allow_automatic_failover"],
                            engine["failover_priority"],
                            engine["priority"],
                            engine["configuration"],
                            engine["created_by"],
                            ),
                        )
                print(f"✅ Registered new avatar engine: {engine['api_name']}")

        conn.commit()

        # Verify registration
        cursor.execute(
            """
            SELECT api_name, capability, priority, status
            FROM api_registry
            WHERE capability = 'avatar - generation'
            ORDER BY priority ASC
        """
        )

        registered_engines = cursor.fetchall()
        print("\\n🎯 Avatar Generation Engines Registered:")
        for engine in registered_engines:
            name, capability, priority, status = engine
            print(f"  • {name} (Priority: {priority}, Status: {status})")

        print("\\n🚀 Avatar engine registration completed successfully!")
        print("\\n📋 Integration Summary:")
        print(
            "  • Primary Engine: Linly - Talker (Priority 1) - High quality,
    enhanced features"
        )
        print(
            "  • Fallback Engine: Talking Heads (Priority 10) - Reliable backup option"
        )
        print(
            "  • Capability: 'avatar - generation' - Used by API Orchestrator for intelligent selection"
        )
        print(
            "  • Failover: Automatic - System will switch to fallback if primary fails"
        )

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

    return True

if __name__ == "__main__":
    print("🎬 TRAE AI Avatar Engine Registration")
    print("=" * 50)

    success = register_avatar_engines()

    if success:
        print("\\n✨ Avatar engines are now ready for production use!")
        print("\\n🔧 Next Steps:")
        print("  1. Start Linly - Talker service on port 7860")
        print("  2. Start Talking Heads service on port 8000")
        print("  3. API Orchestrator will automatically manage engine selection")
        print("  4. Dashboard controls will be available for manual override")
    else:
        print("\\n❌ Registration failed. Please check the error messages above.")
        exit(1)