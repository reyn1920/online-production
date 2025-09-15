#!/usr/bin/env python3
""""""



Metadata extraction utilities for TRAE.AI System

""""""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def extract_bundle_metadata(bundle_path: str) -> Dict[str, Any]:
    """"""

   

    
   
"""
    Extract metadata from a bundle directory
   """

    
   

    Args:
        bundle_path: Path to bundle directory
   
""""""

    Extract metadata from a bundle directory
   

    
   
"""
    Returns:
        Dict containing bundle metadata
   """"""
    
   """

    bundle_dir = Path(bundle_path)
   

    
   
""""""


    

   

    bundle_dir = Path(bundle_path)
   
""""""
    if not bundle_dir.exists():
        return {
            "name": bundle_dir.name,
            "path": str(bundle_path),
            "exists": False,
            "error": "Bundle directory not found",
         }

    metadata = {
        "name": bundle_dir.name,
        "path": str(bundle_path),
        "exists": True,
        "created": datetime.now().isoformat(),
        "files": [],
        "size_bytes": 0,
        "file_count": 0,
     }

    # Scan files in bundle
    try:
        for file_path in bundle_dir.rglob("*"):
            if file_path.is_file():
                file_info = {
                    "name": file_path.name,
                    "relative_path": str(file_path.relative_to(bundle_dir)),
                    "size_bytes": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                 }
                metadata["files"].append(file_info)
                metadata["size_bytes"] += file_info["size_bytes"]

        metadata["file_count"] = len(metadata["files"])

        # Look for bundle config
        config_path = bundle_dir / "bundle.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    bundle_config = json.load(f)
                metadata["config"] = bundle_config
            except Exception as e:
                metadata["config_error"] = str(e)

    except Exception as e:
        metadata["scan_error"] = str(e)

    return metadata


def create_bundle_manifest(bundles: List[str], output_path: str) -> Dict[str, Any]:
    """"""

   

    
   
"""
    Create a manifest file for multiple bundles
   """

    
   

    Args:
        bundles: List of bundle paths
        output_path: Path to write manifest
   
""""""

    Create a manifest file for multiple bundles
   

    
   
"""
    Returns:
        Dict containing manifest data
   """"""
    manifest = {
        "created": datetime.now().isoformat(),
        "bundles": [],
        "total_size_bytes": 0,
        "total_files": 0,
     }

    for bundle_path in bundles:
        bundle_metadata = extract_bundle_metadata(bundle_path)
        manifest["bundles"].append(bundle_metadata)

        if bundle_metadata.get("exists"):
            manifest["total_size_bytes"] += bundle_metadata.get("size_bytes", 0)
            manifest["total_files"] += bundle_metadata.get("file_count", 0)

    # Write manifest to file
    try:
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        manifest["manifest_path"] = output_path
    except Exception as e:
        manifest["write_error"] = str(e)

    return manifest


def validate_bundle_integrity(bundle_path: str) -> Dict[str, Any]:
    """"""

   

    
   
"""
    Validate bundle integrity and structure
   """

    
   

    Args:
        bundle_path: Path to bundle directory
   
""""""

    Validate bundle integrity and structure
   

    
   
"""
    Returns:
        Dict containing validation results
   """"""
    
   """

    bundle_dir = Path(bundle_path)
   

    
   
""""""


    

   

    bundle_dir = Path(bundle_path)
   
""""""
    validation = {"valid": True, "errors": [], "warnings": [], "checks": []}

    # Check if bundle exists
    if not bundle_dir.exists():
        validation["valid"] = False
        validation["errors"].append("Bundle directory does not exist")
        return validation

    # Check for required files
    required_files = ["README.md", "requirements.txt"]
    for req_file in required_files:
        file_path = bundle_dir / req_file
        if file_path.exists():
            validation["checks"].append(f"✓ {req_file} found")
        else:
            validation["warnings"].append(f"Missing recommended file: {req_file}")

    # Check for empty bundle
    file_count = len(list(bundle_dir.rglob("*")))
    if file_count == 0:
        validation["valid"] = False
        validation["errors"].append("Bundle is empty")
    else:
        validation["checks"].append(f"✓ Bundle contains {file_count} items")

    return validation