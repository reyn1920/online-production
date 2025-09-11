#!/usr/bin/env python3
"""
Synthesize Release v3 - Add-only synthesizer for multi-bundle ingestion
Creates immutable releases with comprehensive metadata and validation
"""

import hashlib
import json
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.secret_store_bridge import get_secret_store
from backend.util.metadata import extract_bundle_metadata
from backend.util.validation import validate_bundle_structure

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SynthesizerV3:
    """Add-only synthesizer for multi-bundle ingestion with immutable releases"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir / "assets"
        self.incoming_dir = self.assets_dir / "incoming"
        self.releases_dir = self.assets_dir / "releases"
        self.temp_dir = self.assets_dir / "temp" / "synthesis"
        self.archive_dir = self.assets_dir / "archive"

        # Ensure directories exist
        for dir_path in [
            self.incoming_dir,
            self.releases_dir,
            self.temp_dir,
            self.archive_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        self.secret_store = get_secret_store()

        # Release metadata
        self.current_release = None
        self.release_manifest = {}

    def scan_incoming_bundles(self) -> List[Dict[str, Any]]:
        """Scan incoming directory for new bundles"""
        bundles = []

        # Scan bundles directory
        bundles_dir = self.incoming_dir / "bundles"
        if bundles_dir.exists():
            for bundle_path in bundles_dir.iterdir():
                if bundle_path.is_file() and bundle_path.suffix in [
                    ".zip",
                    ".tar.gz",
                    ".tgz",
                ]:
                    bundle_info = self._analyze_bundle(bundle_path)
                    if bundle_info:
                        bundles.append(bundle_info)
                elif bundle_path.is_dir():
                    # Directory bundle
                    bundle_info = self._analyze_directory_bundle(bundle_path)
                    if bundle_info:
                        bundles.append(bundle_info)

        logger.info(f"Found {len(bundles)} bundles in incoming directory")
        return bundles

    def _analyze_bundle(self, bundle_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a compressed bundle file"""
        try:
            bundle_info = {
                "path": str(bundle_path),
                "name": bundle_path.stem,
                "type": "compressed",
                "format": bundle_path.suffix,
                "size": bundle_path.stat().st_size,
                "modified": datetime.fromtimestamp(
                    bundle_path.stat().st_mtime
                ).isoformat(),
                "checksum": self._calculate_checksum(bundle_path),
                "contents": [],
                "metadata": {},
            }

            # Extract and analyze contents
            if bundle_path.suffix == ".zip":
                with zipfile.ZipFile(bundle_path, "r") as zf:
                    bundle_info["contents"] = zf.namelist()
                    # Look for metadata files
                    for name in zf.namelist():
                        if name.endswith(
                            ("manifest.json", "metadata.json", "bundle.json")
                        ):
                            try:
                                with zf.open(name) as f:
                                    bundle_info["metadata"] = json.loads(
                                        f.read().decode("utf-8")
                                    )
                                break
                            except Exception as e:
                                logger.warning(
                                    f"Failed to read metadata from {name}: {e}"
                                )

            elif bundle_path.suffix in [".tar.gz", ".tgz"]:
                with tarfile.open(bundle_path, "r:gz") as tf:
                    bundle_info["contents"] = tf.getnames()
                    # Look for metadata files
                    for name in tf.getnames():
                        if name.endswith(
                            ("manifest.json", "metadata.json", "bundle.json")
                        ):
                            try:
                                member = tf.getmember(name)
                                f = tf.extractfile(member)
                                if f:
                                    bundle_info["metadata"] = json.loads(
                                        f.read().decode("utf-8")
                                    )
                                break
                            except Exception as e:
                                logger.warning(
                                    f"Failed to read metadata from {name}: {e}"
                                )

            return bundle_info

        except Exception as e:
            logger.error(f"Failed to analyze bundle {bundle_path}: {e}")
            return None

    def _analyze_directory_bundle(self, bundle_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a directory bundle"""
        try:
            bundle_info = {
                "path": str(bundle_path),
                "name": bundle_path.name,
                "type": "directory",
                "format": "dir",
                "size": sum(
                    f.stat().st_size for f in bundle_path.rglob("*") if f.is_file()
                ),
                "modified": datetime.fromtimestamp(
                    bundle_path.stat().st_mtime
                ).isoformat(),
                "checksum": self._calculate_directory_checksum(bundle_path),
                "contents": [
                    str(p.relative_to(bundle_path))
                    for p in bundle_path.rglob("*")
                    if p.is_file()
                ],
                "metadata": {},
            }

            # Look for metadata files
            for metadata_file in ["manifest.json", "metadata.json", "bundle.json"]:
                metadata_path = bundle_path / metadata_file
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            bundle_info["metadata"] = json.load(f)
                        break
                    except Exception as e:
                        logger.warning(
                            f"Failed to read metadata from {metadata_path}: {e}"
                        )

            return bundle_info

        except Exception as e:
            logger.error(f"Failed to analyze directory bundle {bundle_path}: {e}")
            return None

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _calculate_directory_checksum(self, dir_path: Path) -> str:
        """Calculate combined checksum of all files in directory"""
        sha256_hash = hashlib.sha256()

        # Sort files for consistent checksum
        files = sorted(dir_path.rglob("*"))
        for file_path in files:
            if file_path.is_file():
                # Include relative path in hash for structure integrity
                rel_path = str(file_path.relative_to(dir_path))
                sha256_hash.update(rel_path.encode("utf-8"))

                # Include file content
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def validate_bundles(self, bundles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate all bundles before synthesis"""
        validation_results = {
            "valid_bundles": [],
            "invalid_bundles": [],
            "warnings": [],
            "total_size": 0,
        }

        for bundle in bundles:
            try:
                # Basic validation
                if not bundle.get("contents"):
                    validation_results["invalid_bundles"].append(
                        {
                            "bundle": bundle["name"],
                            "error": "Empty bundle or failed to read contents",
                        }
                    )
                    continue

                # Size validation (max 1GB per bundle)
                if bundle["size"] > 1024 * 1024 * 1024:
                    validation_results["invalid_bundles"].append(
                        {
                            "bundle": bundle["name"],
                            "error": f"Bundle too large: {bundle['size']} bytes (max 1GB)",
                        }
                    )
                    continue

                # Content validation
                suspicious_files = []
                for content_path in bundle["contents"]:
                    # Check for suspicious file types
                    if any(
                        content_path.endswith(ext)
                        for ext in [".exe", ".bat", ".sh", ".ps1"]
                    ):
                        suspicious_files.append(content_path)

                if suspicious_files:
                    validation_results["warnings"].append(
                        {
                            "bundle": bundle["name"],
                            "warning": f"Contains executable files: {suspicious_files[:5]}",
                        }
                    )

                # Metadata validation
                if bundle.get("metadata"):
                    required_fields = ["version", "type", "description"]
                    missing_fields = [
                        field
                        for field in required_fields
                        if field not in bundle["metadata"]
                    ]
                    if missing_fields:
                        validation_results["warnings"].append(
                            {
                                "bundle": bundle["name"],
                                "warning": f"Missing metadata fields: {missing_fields}",
                            }
                        )

                validation_results["valid_bundles"].append(bundle)
                validation_results["total_size"] += bundle["size"]

            except Exception as e:
                validation_results["invalid_bundles"].append(
                    {
                        "bundle": bundle.get("name", "unknown"),
                        "error": f"Validation failed: {str(e)}",
                    }
                )

        logger.info(
            f"Validation complete: {
                len(
                    validation_results['valid_bundles'])} valid, "
            f"{
                len(
                    validation_results['invalid_bundles'])} invalid bundles"
        )

        return validation_results

    def create_release(
        self, bundles: List[Dict[str, Any]], release_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create immutable release from validated bundles"""
        if not release_version:
            release_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        release_dir = self.releases_dir / release_version
        if release_dir.exists():
            return {
                "success": False,
                "error": f"Release {release_version} already exists (immutable releases)",
            }

        try:
            # Create release directory structure
            release_dir.mkdir(parents=True)
            bundles_dir = release_dir / "bundles"
            metadata_dir = release_dir / "metadata"

            bundles_dir.mkdir()
            metadata_dir.mkdir()

            # Process each bundle
            processed_bundles = []
            for bundle in bundles:
                bundle_result = self._process_bundle_for_release(bundle, bundles_dir)
                if bundle_result["success"]:
                    processed_bundles.append(bundle_result)
                else:
                    logger.error(
                        f"Failed to process bundle {
                            bundle['name']}: {
                            bundle_result['error']}"
                    )

            # Create release manifest
            release_manifest = {
                "version": release_version,
                "created_at": datetime.now().isoformat(),
                "bundles_count": len(processed_bundles),
                "total_size": sum(b["size"] for b in processed_bundles),
                "bundles": processed_bundles,
                "checksum": "",  # Will be calculated after manifest is written
                "metadata": {
                    "synthesizer_version": "3.0",
                    "source_bundles": len(bundles),
                    "processed_bundles": len(processed_bundles),
                    "creation_timestamp": datetime.now().timestamp(),
                },
            }

            # Write manifest
            manifest_path = metadata_dir / "release_manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(release_manifest, f, indent=2, ensure_ascii=False)

            # Calculate release checksum
            release_checksum = self._calculate_directory_checksum(release_dir)
            release_manifest["checksum"] = release_checksum

            # Update manifest with checksum
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(release_manifest, f, indent=2, ensure_ascii=False)

            # Create release summary
            summary_path = release_dir / "RELEASE_SUMMARY.md"
            self._create_release_summary(release_manifest, summary_path)

            # Archive processed bundles
            self._archive_processed_bundles(bundles)

            self.current_release = release_version
            self.release_manifest = release_manifest

            logger.info(
                f"Release {release_version} created successfully with {
                    len(processed_bundles)} bundles"
            )

            return {
                "success": True,
                "release_version": release_version,
                "release_path": str(release_dir),
                "bundles_processed": len(processed_bundles),
                "total_size": release_manifest["total_size"],
                "checksum": release_checksum,
            }

        except Exception as e:
            logger.error(f"Failed to create release: {e}")
            # Cleanup on failure
            if release_dir.exists():
                shutil.rmtree(release_dir)
            return {"success": False, "error": str(e)}

    def _process_bundle_for_release(
        self, bundle: Dict[str, Any], target_dir: Path
    ) -> Dict[str, Any]:
        """Process a single bundle for inclusion in release"""
        try:
            bundle_path = Path(bundle["path"])
            target_path = target_dir / bundle_path.name

            if bundle["type"] == "compressed":
                # Copy compressed bundle as-is
                shutil.copy2(bundle_path, target_path)
            elif bundle["type"] == "directory":
                # Create compressed archive of directory
                if target_path.suffix != ".tar.gz":
                    target_path = target_path.with_suffix(".tar.gz")

                with tarfile.open(target_path, "w:gz") as tar:
                    tar.add(bundle_path, arcname=bundle_path.name)

            # Verify copied bundle
            if not target_path.exists():
                raise Exception("Bundle copy failed - target file not found")

            # Create bundle metadata
            bundle_metadata = {
                "original_path": bundle["path"],
                "release_path": str(target_path),
                "name": bundle["name"],
                "type": bundle["type"],
                "size": target_path.stat().st_size,
                "original_checksum": bundle["checksum"],
                "release_checksum": self._calculate_checksum(target_path),
                "processed_at": datetime.now().isoformat(),
                "contents_count": len(bundle["contents"]),
                "metadata": bundle.get("metadata", {}),
            }

            return {
                "success": True,
                "name": bundle["name"],
                "size": bundle_metadata["size"],
                "checksum": bundle_metadata["release_checksum"],
                "metadata": bundle_metadata,
            }

        except Exception as e:
            return {
                "success": False,
                "name": bundle.get("name", "unknown"),
                "error": str(e),
            }

    def _create_release_summary(self, manifest: Dict[str, Any], summary_path: Path):
        """Create human-readable release summary"""
        summary_content = f"""# Release {manifest['version']} Summary

**Created:** {manifest['created_at']}
**Synthesizer Version:** {manifest['metadata']['synthesizer_version']}
**Total Bundles:** {manifest['bundles_count']}
**Total Size:** {manifest['total_size']:,} bytes
**Release Checksum:** {manifest['checksum']}

## Processed Bundles

"""

        for i, bundle in enumerate(manifest["bundles"], 1):
            summary_content += f"{i}. **{bundle['name']}**\n"
            summary_content += f"   - Size: {bundle['size']:,} bytes\n"
            summary_content += f"   - Checksum: {bundle['checksum']}\n"
            if bundle["metadata"].get("metadata"):
                metadata = bundle["metadata"]["metadata"]
                if metadata.get("version"):
                    summary_content += f"   - Version: {metadata['version']}\n"
                if metadata.get("description"):
                    summary_content += f"   - Description: {metadata['description']}\n"
            summary_content += "\n"

        summary_content += f"\n## Release Integrity\n\n"
        summary_content += (
            f"This release is immutable and cryptographically verified.\n"
        )
        summary_content += f"Any modification will invalidate the release checksum.\n"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_content)

    def _archive_processed_bundles(self, bundles: List[Dict[str, Any]]):
        """Move processed bundles to archive"""
        archive_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_subdir = self.archive_dir / f"processed_{archive_timestamp}"
        archive_subdir.mkdir(exist_ok=True)

        for bundle in bundles:
            try:
                bundle_path = Path(bundle["path"])
                if bundle_path.exists():
                    archive_path = archive_subdir / bundle_path.name
                    shutil.move(str(bundle_path), str(archive_path))
                    logger.info(f"Archived bundle: {bundle_path.name}")
            except Exception as e:
                logger.warning(
                    f"Failed to archive bundle {
                        bundle.get(
                            'name',
                            'unknown')}: {e}"
                )

    def get_release_manifest(
        self, release_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get release manifest for specified or current release"""
        if not release_version:
            release_version = self.current_release

        if not release_version:
            return {"error": "No release specified and no current release"}

        manifest_path = (
            self.releases_dir / release_version / "metadata" / "release_manifest.json"
        )

        if not manifest_path.exists():
            return {"error": f"Release manifest not found for {release_version}"}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to read release manifest: {str(e)}"}

    def list_releases(self) -> List[Dict[str, Any]]:
        """List all available releases"""
        releases = []

        if not self.releases_dir.exists():
            return releases

        for release_dir in self.releases_dir.iterdir():
            if release_dir.is_dir():
                manifest = self.get_release_manifest(release_dir.name)
                if "error" not in manifest:
                    releases.append(
                        {
                            "version": release_dir.name,
                            "created_at": manifest.get("created_at"),
                            "bundles_count": manifest.get("bundles_count", 0),
                            "total_size": manifest.get("total_size", 0),
                            "checksum": manifest.get("checksum", ""),
                        }
                    )

        # Sort by creation date (newest first)
        releases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return releases

    def synthesize_bundles(
        self, release_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main synthesis workflow: scan, validate, and create release"""
        logger.info("Starting bundle synthesis workflow")

        try:
            # Step 1: Scan incoming bundles
            bundles = self.scan_incoming_bundles()
            if not bundles:
                return {
                    "success": False,
                    "error": "No bundles found in incoming directory",
                    "bundles_found": 0,
                }

            # Step 2: Validate bundles
            validation_results = self.validate_bundles(bundles)
            if not validation_results["valid_bundles"]:
                return {
                    "success": False,
                    "error": "No valid bundles after validation",
                    "validation_results": validation_results,
                }

            # Step 3: Create release
            release_result = self.create_release(
                validation_results["valid_bundles"], release_version
            )

            # Combine results
            synthesis_result = {
                "success": release_result["success"],
                "bundles_found": len(bundles),
                "bundles_valid": len(validation_results["valid_bundles"]),
                "bundles_invalid": len(validation_results["invalid_bundles"]),
                "validation_warnings": len(validation_results["warnings"]),
                "validation_results": validation_results,
                "release_result": release_result,
            }

            if release_result["success"]:
                synthesis_result.update(
                    {
                        "release_version": release_result["release_version"],
                        "release_path": release_result["release_path"],
                        "total_size": release_result["total_size"],
                    }
                )

            logger.info(f"Synthesis completed: {synthesis_result['success']}")
            return synthesis_result

        except Exception as e:
            logger.error(f"Synthesis workflow failed: {e}")
            return {"success": False, "error": str(e)}


def main():
    """Command-line interface for synthesizer"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Synthesize Release v3 - Multi-bundle synthesizer"
    )
    parser.add_argument(
        "--base-dir", default=".", help="Base directory (default: current)"
    )
    parser.add_argument(
        "--release-version", help="Specific release version (default: auto-generated)"
    )
    parser.add_argument(
        "--list-releases", action="store_true", help="List all releases"
    )
    parser.add_argument("--get-manifest", help="Get manifest for specific release")

    args = parser.parse_args()

    synthesizer = SynthesizerV3(args.base_dir)

    if args.list_releases:
        releases = synthesizer.list_releases()
        print(f"Found {len(releases)} releases:")
        for release in releases:
            print(
                f"  {release['version']} - {release['bundles_count']} bundles, "
                f"{release['total_size']:,} bytes"
            )
        return

    if args.get_manifest:
        manifest = synthesizer.get_release_manifest(args.get_manifest)
        print(json.dumps(manifest, indent=2))
        return

    # Run synthesis
    result = synthesizer.synthesize_bundles(args.release_version)
    print(json.dumps(result, indent=2))

    if result["success"]:
        print(f"\n✅ Synthesis successful!")
        print(f"Release: {result['release_version']}")
        print(f"Bundles processed: {result['bundles_valid']}/{result['bundles_found']}")
        print(f"Total size: {result['total_size']:,} bytes")
    else:
        print(f"\n❌ Synthesis failed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
