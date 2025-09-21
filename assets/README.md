# Assets Directory Structure

This directory contains all assets for the TRAE.AI Max-Out Pack workflow, organized by stage and
type.

## Directory Structure

### `/incoming/`

Staging area for new content before processing:

- `bundles/` - Raw bundle files awaiting synthesis
- `roadmaps/` - CSV roadmap files for channel processing
- `media/` - Raw media files (images, videos, audio)

### `/releases/`

Processed and finalized releases organized by version:

- `v1/` - Version 1 releases (legacy)
- `v2/` - Version 2 releases (legacy)
- `v3/` - Version 3 releases (current synthesis format)

### `/temp/`

Temporary processing files (automatically cleaned):

- `synthesis/` - Temporary files during bundle synthesis
- `channels/` - Temporary files during channel processing
- `processing/` - General temporary processing files

### `/archive/`

Long-term storage for historical data:

- `old_bundles/` - Archived bundle files
- `old_releases/` - Archived release files

## Workflow Integration

### Bundle Synthesis (v3)

1. Place bundle files in `incoming/bundles/`
2. Run synthesis via dashboard action "Synthesize bundles v3"
3. Processed releases appear in `releases/v3/`
4. Original bundles moved to `archive/old_bundles/`

### Channel Processing

1. Place roadmap CSV in `incoming/roadmaps/`
2. Run channel processing via dashboard action "Run one channel"
3. Generated MP4 and PDF files saved to appropriate release directory
4. Temporary files cleaned from `temp/channels/`

### Release Management

1. Use dashboard action "Get release manifest" to view available releases
2. Releases are immutable once created
3. Historical releases preserved in archive

## File Naming Conventions

### Bundles

- Format: `bundle_YYYYMMDD_HHMMSS.zip`
- Example: `bundle_20240115_143022.zip`

### Releases

- Format: `release_v3_YYYYMMDD_HHMMSS/`
- Example: `release_v3_20240115_143500/`

### Roadmaps

- Format: `roadmap_CHANNELNAME_YYYYMMDD.csv`
- Example: `roadmap_tech_insights_20240115.csv`

## Maintenance

### Automatic Cleanup

- Temp files older than 24 hours are automatically cleaned
- Processing logs are rotated weekly

### Manual Cleanup

- Archive old releases periodically to manage disk space
- Review and clean incoming directory of processed files

### Monitoring

- Directory sizes are monitored via dashboard
- Alerts triggered if directories exceed size limits

## Security Notes

- All directories have appropriate permissions set
- Sensitive content should be encrypted before placement
- Access logs are maintained for audit purposes

## Integration Points

### Scripts

- `scripts/synthesize_release_v3.py` - Processes bundles from incoming
- `backend/runner/channel_executor.py` - Processes roadmaps from incoming
- `scripts/phoenix_protocol.sh` - Includes asset directory verification

### Dashboard Actions

- All Max-Out Pack actions integrate with this directory structure
- File paths are automatically resolved relative to project root
- Status and progress updates reflect directory contents

For technical details, see the individual component documentation in the respective script files.
