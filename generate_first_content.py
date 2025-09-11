#!/usr / bin / env python3
"""
First Content Generator for The Right Perspective Channel
Generates audio - only content using the configured voice profile
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import requests

# Setup logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FirstContentGenerator:


    def __init__(self):
        self.base_dir = Path.cwd()
        self.channel_name = "The Right Perspective"
        self.channel_dir = "the_right_perspective"
        self.output_dir = self.base_dir / "output" / "audio" / self.channel_dir
        self.scripts_dir = self.base_dir / "content" / "scripts" / self.channel_dir
        self.templates_dir = self.base_dir / "content" / "templates" / self.channel_dir

        # Load channel configuration
        self.load_channel_config()


    def load_channel_config(self):
        """Load channel configuration from pipeline file"""
        config_file = self.base_dir / f"{self.channel_dir}_pipeline.json"
        try:
            with open(config_file, "r") as f:
                self.config = json.load(f)
                logger.info(f"Loaded configuration for {self.channel_name}")
        except FileNotFoundError:
            logger.error(f"Pipeline configuration not found: {config_file}")
            self.config = {}


    def create_sample_script(self):
        """Create a sample script for the first episode"""
        today = datetime.now()
        episode_date = today.strftime("%Y-%m-%d")

        sample_script = f"""
# The Right Perspective - Episode 1
## {episode_date} - Welcome to The Right Perspective

### Introduction (60 seconds)
Welcome to The Right Perspective, where we cut through the mainstream media noise to bring you unfiltered conservative political commentary. I'm your host, and today we're launching something special - a daily dose of truth that the establishment doesn't want you to hear.

Today's episode is all about setting the foundation for what this channel represents and why your voice matters in today's political landscape.

### Main Content (12 minutes)

#### Segment 1: Why The Right Perspective Matters (4 minutes)
In a world where mainstream media has become nothing more than a propaganda machine for the left, we need voices that aren't afraid to tell the truth. This channel is inspired by the fearless commentary style of Greg Gutfeld and Jesse Watters - we're going to tackle the issues that matter to real Americans.

We're not here to play nice with the establishment. We're here to call out the hypocrisy, expose the lies, and give you the perspective that Fox News and other conservative outlets are bringing to light every single day.

#### Segment 2: What You Can Expect (4 minutes)
Every day at 6 PM Eastern, we'll be diving deep into the stories that are shaping our nation. From breaking down the latest political theater in Washington to exposing the radical agenda being pushed in our schools and communities.

We'll be covering:
- Daily political analysis with a conservative lens
- Breakdown of mainstream media bias and misinformation
- Real stories from real Americans who are fighting back
- Actionable insights on how you can make a difference

#### Segment 3: Building Our Community (4 minutes)
This isn't just a one - way conversation. This is about building a community of patriots who refuse to be silenced. We want to hear from you - your stories, your concerns, your victories.

We'll be featuring listener submissions, highlighting local conservative victories, and connecting like - minded Americans who are ready to take back our country from the radical left.

### Conclusion (2 minutes)
So that's what The Right Perspective is all about - giving you the unfiltered truth that the mainstream media won't tell you. We're going to be your daily source for conservative commentary that cuts through the noise.

Make sure to subscribe and hit that notification bell so you never miss an episode. We're publishing daily at 6 PM Eastern, and trust me, you won't want to miss what we have planned.

Tomorrow, we're diving into the latest developments in the ongoing battle for election integrity - something the mainstream media continues to ignore but that every American should be paying attention to.

This is The Right Perspective, where your voice matters and the truth always wins. See you tomorrow at 6 PM Eastern.

---

## Production Notes
- Voice: Matthew (Speechelo) - Authoritative tone
- Background: Subtle patriotic music (low volume)
- Duration Target: 15 minutes
- Call - to - Action: Subscribe, notifications, tomorrow's preview
- Monetization: Mention merchandise store launch coming soon
"""

        script_file = self.scripts_dir / f"episode_001_{episode_date}.md"
        with open(script_file, "w") as f:
            f.write(sample_script)

        logger.info(f"Sample script created: {script_file}")
        return script_file


    def generate_audio_content(self, script_file):
        """Generate audio content from script (placeholder for actual TTS integration)"""
        logger.info("Generating audio content...")

        # Read the script
        with open(script_file, "r") as f:
            script_content = f.read()

        # Extract just the spoken content (remove markdown formatting)
        spoken_content = self.extract_spoken_content(script_content)

        # Create audio metadata
        audio_metadata = {
            "title": "The Right Perspective - Episode 1: Welcome",
                "description": "Welcome to The Right Perspective - unfiltered conservative political commentary",
                "duration_target": "15 minutes",
                "voice_profile": "Matthew (Speechelo)",
                "script_file": str(script_file),
                "generated_date": datetime.now().isoformat(),
                "content_length": len(spoken_content),
                "word_count": len(spoken_content.split()),
                "estimated_duration": f"{len(spoken_content.split()) / 150:.1f} minutes",  # ~150 WPM average
            "status": "ready_for_tts_generation",
                }

        # Save metadata
        metadata_file = self.output_dir / "episode_001_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(audio_metadata, f, indent = 2)

        # Save clean spoken content for TTS
        content_file = self.output_dir / "episode_001_content.txt"
        with open(content_file, "w") as f:
            f.write(spoken_content)

        logger.info(f"Audio content prepared: {content_file}")
        logger.info(f"Metadata saved: {metadata_file}")
        logger.info(f"Estimated duration: {audio_metadata['estimated_duration']}")

        return audio_metadata


    def extract_spoken_content(self, script_content):
        """Extract only the spoken content from the script"""
        lines = script_content.split("\n")
        spoken_lines = []

        skip_sections = ["## Production Notes", "---", "###"]
        in_skip_section = False

        for line in lines:
            # Skip markdown headers and production notes
            if any(skip in line for skip in skip_sections):
                in_skip_section = True
                continue

            # Skip empty lines and markdown formatting
            if line.strip() == "" or line.startswith("#") or line.startswith("-"):
                continue

            # Skip production notes section
            if "Production Notes" in line or line.startswith("##"):
                in_skip_section = True
                continue

            if not in_skip_section and line.strip():
                # Clean up any remaining markdown
                clean_line = line.replace("**", "").replace("*", "").strip()
                if clean_line and not clean_line.startswith("####"):
                    spoken_lines.append(clean_line)

        return "\n\n".join(spoken_lines)


    def create_production_schedule(self):
        """Create a production schedule for the first week"""
        today = datetime.now()
        schedule = []

        for i in range(7):  # First week
            episode_date = today + timedelta(days = i)
            episode_info = {
                "episode_number": i + 1,
                    "date": episode_date.strftime("%Y-%m-%d"),
                    "publish_time": "18:00 EST",  # 6 PM EST
                "title": f"Episode {i + 1}: {self.get_episode_title(i + 1)}",
                    "status": "planned" if i > 0 else "in_production",
                    "duration_target": "12 - 15 minutes",
                    "content_focus": self.get_content_focus(i + 1),
                    }
            schedule.append(episode_info)

        schedule_file = self.base_dir / f"{self.channel_dir}_production_schedule.json"
        with open(schedule_file, "w") as f:
            json.dump(
                {
                    "channel": self.channel_name,
                        "schedule_created": today.isoformat(),
                        "episodes": schedule,
                        },
                    f,
                    indent = 2,
                    )

        logger.info(f"Production schedule created: {schedule_file}")
        return schedule


    def get_episode_title(self, episode_num):
        """Generate episode titles"""
        titles = {
            1: "Welcome to The Right Perspective",
                2: "Election Integrity: The Battle Continues",
                3: "Media Bias Exposed: This Week's Biggest Lies",
                4: "Border Crisis: What They Don't Want You to Know",
                5: "Economic Reality Check: Inflation vs. Propaganda",
                6: "Education Under Attack: Fighting for Our Children",
                7: "Week in Review: Conservative Wins You Missed",
                }
        return titles.get(episode_num, f"Daily Conservative Commentary")


    def get_content_focus(self, episode_num):
        """Get content focus for each episode"""
        focuses = {
            1: "Channel introduction and mission statement",
                2: "Current election integrity developments",
                3: "Weekly mainstream media bias analysis",
                4: "Border security and immigration policy",
                5: "Economic policy and inflation impact",
                6: "Education policy and parental rights",
                7: "Weekly roundup of conservative victories",
                }
        return focuses.get(episode_num, "Daily political commentary")


    def generate_first_content(self):
        """Generate the complete first content package"""
        logger.info(f"Starting first content generation for {self.channel_name}")

        try:
            # Create sample script
            script_file = self.create_sample_script()

            # Generate audio content
            audio_metadata = self.generate_audio_content(script_file)

            # Create production schedule
            schedule = self.create_production_schedule()

            # Generate summary report
            report = {
                "generation_completed": datetime.now().isoformat(),
                    "channel": self.channel_name,
                    "first_episode": {
                    "script_file": str(script_file),
                        "audio_metadata": audio_metadata,
                        "status": "ready_for_voice_generation",
                        },
                    "production_schedule": f"{self.channel_dir}_production_schedule.json",
                    "next_steps": [
                    "Generate audio using Speechelo with Matthew voice profile",
                        "Create episode thumbnail",
                        "Upload to YouTube channel",
                        "Schedule for 6 PM EST publication",
                        "Prepare episode 2 script",
                        ],
                    "files_created": [
                    str(script_file),
                        str(self.output_dir / "episode_001_metadata.json"),
                        str(self.output_dir / "episode_001_content.txt"),
                        f"{self.channel_dir}_production_schedule.json",
                        ],
                    }

            report_file = (
                self.base_dir / f"{self.channel_dir}_first_content_report.json"
            )
            with open(report_file, "w") as f:
                json.dump(report, f, indent = 2)

            logger.info("✅ First content generation completed successfully!")
            logger.info(f"📝 Script ready: {script_file}")
            logger.info(f"🎵 Audio content prepared for TTS generation")
            logger.info(f"📅 Production schedule created for first week")
            logger.info(f"📊 Report generated: {report_file}")

            return True

        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return False


def main():
    """Main execution function"""
    print("🎙️ First Content Generator - The Right Perspective")
    print("=" * 55)

    generator = FirstContentGenerator()
    success = generator.generate_first_content()

    if success:
        print("\n✅ First content package generated successfully!")
        print("\n📋 What was created:")
        print("• Episode 1 script with full content")
        print("• Audio content ready for TTS generation")
        print("• Production schedule for first week")
        print("• Metadata and content files")
        print("\n🎯 Next steps:")
        print("1. Review the generated script")
        print("2. Generate audio using Speechelo (Matthew voice)")
        print("3. Create episode thumbnail")
        print("4. Upload and schedule on YouTube")
        print("5. Monitor engagement and feedback")
    else:
        print("\n❌ Content generation failed. Check the logs for details.")

    return success

if __name__ == "__main__":
    main()
