#!/usr / bin / env python3
""""""
First Channel Setup Script
Sets up the primary channel configuration and initializes content generation pipeline
Excludes video production as requested
""""""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("channel_setup.log"), logging.StreamHandler()],
# BRACKET_SURGEON: disabled
# )
logger = logging.getLogger(__name__)


class ChannelSetup:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.channels_file = self.base_dir / "channels.json"
        self.output_dir = self.base_dir / "output"
        self.content_dir = self.base_dir / "content"

    def load_channels_config(self):
        """Load the channels configuration"""
        try:
            with open(self.channels_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Channels config file not found: {self.channels_file}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in channels config: {e}")
            return None

    def get_primary_channel(self, config):
        """Get the primary channel from configuration"""
        for channel_name, channel_data in config["channels"].items():
            if channel_data.get("is_primary", False):
                return channel_name, channel_data
        return None, None

    def create_channel_directories(self, channel_name):
        """Create necessary directories for the channel"""
        directories = [
            self.output_dir / "audio" / channel_name.lower().replace(" ", "_"),
            self.output_dir / "graphics" / channel_name.lower().replace(" ", "_"),
            self.output_dir / "thumbnails" / channel_name.lower().replace(" ", "_"),
            self.content_dir / "scripts" / channel_name.lower().replace(" ", "_"),
            self.content_dir / "templates" / channel_name.lower().replace(" ", "_"),
            Path("logs") / channel_name.lower().replace(" ", "_"),
# BRACKET_SURGEON: disabled
#         ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

    def setup_content_pipeline(self, channel_name, channel_config):
        """Setup content generation pipeline for the channel"""
        pipeline_config = {
            "channel_name": channel_name,
            "channel_id": channel_config.get("channel_id"),
            "content_type": "audio_only",  # No video production
            "voice_profile": channel_config.get("voice"),
            "target_length": channel_config.get("target_length"),
            "posting_schedule": channel_config.get("posting_schedule"),
            "content_style": channel_config.get("content_style"),
            "category": channel_config.get("category"),
            "target_audience": channel_config.get("target_audience"),
            "monetization": channel_config.get("monetization", []),
            "platforms": channel_config.get("platforms", []),
            "setup_date": datetime.now().isoformat(),
            "status": "initialized",
# BRACKET_SURGEON: disabled
#         }

        # Save pipeline config
        config_file = self.base_dir / f'{channel_name.lower().replace(" ", "_")}_pipeline.json'
        with open(config_file, "w") as f:
            json.dump(pipeline_config, f, indent=2)

        logger.info(f"Content pipeline configured for {channel_name}")
        return pipeline_config

    def create_content_templates(self, channel_name, channel_config):
        """Create content templates for the channel"""
        template_dir = self.content_dir / "templates" / channel_name.lower().replace(" ", "_")

        # Script template
        script_template = f""""""
# {channel_name} Content Script Template

## Episode Information
- Title: [EPISODE_TITLE]
- Date: [DATE]
- Duration Target: {channel_config.get('target_length', '10 - 15 minutes')}
- Category: {channel_config.get('category', 'general')}

## Content Structure

### Introduction (30 - 60 seconds)
- Hook / Opening statement
- Brief overview of today's topic'
- Channel branding reminder

### Main Content (8 - 12 minutes)
- Key points and analysis
- Supporting evidence / examples
- Audience engagement elements

### Conclusion (1 - 2 minutes)
- Summary of key takeaways
- Call to action
- Next episode preview

## Voice Notes
- Voice: {channel_config.get('voice', 'Default')}
- Tone: {channel_config.get('content_style', 'Professional')}
- Target Audience: {channel_config.get('target_audience', 'General')}

## Monetization Integration
{chr(10).join(f'- {item}' for item in channel_config.get('monetization', []))}
""""""

        with open(template_dir / "script_template.md", "w") as f:
            f.write(script_template)

        # Audio production checklist
        audio_checklist = f""""""
# {channel_name} Audio Production Checklist

## Pre - Production
- [ ] Script finalized and reviewed
- [ ] Voice profile configured: {channel_config.get('voice')}
- [ ] Background music selected (if applicable)
- [ ] Sound effects prepared (if applicable)

## Production
- [ ] Audio generated using voice profile
- [ ] Quality check completed
- [ ] Audio levels normalized
- [ ] Background elements mixed in

## Post - Production
- [ ] Final audio review
- [ ] Metadata added
- [ ] Thumbnail created
- [ ] Upload assets prepared

## Publishing
- [ ] Content scheduled for: {channel_config.get('posting_schedule')}
- [ ] Platform - specific optimization
- [ ] Monetization elements integrated
- [ ] Analytics tracking enabled
""""""

        with open(template_dir / "production_checklist.md", "w") as f:
            f.write(audio_checklist)

        logger.info(f"Content templates created for {channel_name}")

    def generate_setup_report(self, channel_name, channel_config, pipeline_config):
        """Generate a setup completion report"""
        report = {
            "setup_completed": datetime.now().isoformat(),
            "channel_name": channel_name,
            "channel_configuration": channel_config,
            "pipeline_configuration": pipeline_config,
            "directories_created": [
                str(self.output_dir / "audio" / channel_name.lower().replace(" ", "_")),
                str(self.output_dir / "graphics" / channel_name.lower().replace(" ", "_")),
                str(self.output_dir / "thumbnails" / channel_name.lower().replace(" ", "_")),
                str(self.content_dir / "scripts" / channel_name.lower().replace(" ", "_")),
                str(self.content_dir / "templates" / channel_name.lower().replace(" ", "_")),
# BRACKET_SURGEON: disabled
#             ],
            "templates_created": ["script_template.md", "production_checklist.md"],
            "next_steps": [
                "Create first content script using template",
                "Generate audio content using voice profile",
                "Create thumbnail graphics",
                "Schedule first publication",
                "Monitor analytics and engagement",
# BRACKET_SURGEON: disabled
#             ],
            "status": "READY_FOR_CONTENT_CREATION",
# BRACKET_SURGEON: disabled
#         }

        report_file = self.base_dir / f'{channel_name.lower().replace(" ", "_")}_setup_report.json'
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Setup report generated: {report_file}")
        return report

    def run_setup(self):
        """Run the complete channel setup process"""
        logger.info("Starting first channel setup...")

        # Load configuration
        config = self.load_channels_config()
        if not config:
            logger.error("Failed to load channels configuration")
            return False

        # Get primary channel
        channel_name, channel_config = self.get_primary_channel(config)
        if not channel_name:
            logger.error("No primary channel found in configuration")
            return False

        logger.info(f"Setting up primary channel: {channel_name}")

        try:
            # Create directories
            self.create_channel_directories(channel_name)

            # Setup content pipeline
            pipeline_config = self.setup_content_pipeline(channel_name, channel_config)

            # Create templates
            self.create_content_templates(channel_name, channel_config)

            # Generate report
            report = self.generate_setup_report(channel_name, channel_config, pipeline_config)

            logger.info("✅ Channel setup completed successfully!")
            logger.info(f"Primary channel '{channel_name}' is ready for content creation")
            logger.info("📝 Content templates available in content / templates/")
            logger.info("🎵 Audio - only production pipeline configured")
            logger.info("📊 Setup report generated")

            return True

        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False


def main():
    """Main execution function"""
    print("🚀 First Channel Setup - Audio Content Pipeline")
    print("=" * 50)

    setup = ChannelSetup()
    success = setup.run_setup()

    if success:
        print("\\n✅ Setup completed successfully!")
        print("Your first channel is ready for content creation.")
        print("\\nNext steps:")
        print("1. Review the generated templates")
        print("2. Create your first content script")
        print("3. Generate audio content")
        print("4. Create thumbnails and graphics")
        print("5. Schedule your first publication")
    else:
        print("\\n❌ Setup failed. Check the logs for details.")

    return success


if __name__ == "__main__":
    main()