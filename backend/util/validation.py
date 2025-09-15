#!/usr/bin/env python3
""""""



Validation utilities for TRAE.AI System
Provides bundle structure validation and data integrity checks

""""""

import json
import os
from pathlib import Path
from typing import Any, Dict


def validate_bundle_structure(bundle_path: str) -> Dict[str, Any]:
    """"""

   

    
   
"""
    Validate bundle directory structure and required files
   """

    
   

    Args:
        bundle_path: Path to bundle directory
   
""""""

    Validate bundle directory structure and required files
   

    
   
"""
    Returns:
        Dict with validation results
   """"""
    
   """

    bundle_dir = Path(bundle_path)
   

    
   
""""""


    

   

    bundle_dir = Path(bundle_path)
   
""""""
    if not bundle_dir.exists():
        return {
            "valid": False,
            "error": f"Bundle directory does not exist: {bundle_path}",
         }

    if not bundle_dir.is_dir():
        return {
            "valid": False,
            "error": f"Bundle path is not a directory: {bundle_path}",
         }

    # Check for required files
    required_files = ["README.md"]

    missing_required = []
    for req_file in required_files:
        if not (bundle_dir / req_file).exists():
            missing_required.append(req_file)

    if missing_required:
        return {"valid": False, "error": f"Missing required files: {missing_required}"}

    # Validate config.json if present
    config_file = bundle_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)

            # Basic config validation
            if not isinstance(config, dict):
                return {"valid": False, "error": "config.json must be a JSON object"}

        except json.JSONDecodeError as e:
            return {"valid": False, "error": f"Invalid JSON in config.json: {e}"}

    return {
        "valid": True,
        "bundle_name": bundle_dir.name,
        "files_found": [f.name for f in bundle_dir.iterdir() if f.is_file()],
        "size_bytes": sum(f.stat().st_size for f in bundle_dir.rglob("*") if f.is_file()),
     }


def validate_csv_roadmap(csv_path: str) -> Dict[str, Any]:
    """"""

   

    
   
"""
    Validate CSV roadmap file structure
   """

    
   

    Args:
        csv_path: Path to CSV file
   
""""""

    Validate CSV roadmap file structure
   

    
   
"""
    Returns:
        Dict with validation results
   """"""
    
   """

    csv_file = Path(csv_path)
   

    
   
""""""


    

   

    csv_file = Path(csv_path)
   
""""""
    if not csv_file.exists():
        return {"valid": False, "error": f"CSV file does not exist: {csv_path}"}

    try:
        import csv

        with open(csv_file, "r", encoding="utf - 8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return {"valid": False, "error": "CSV file is empty"}

        # Check for required columns
        required_columns = ["title"]
        if not all(col in reader.fieldnames for col in required_columns):
            return {
                "valid": False,
                "error": f"Missing required columns: {required_columns}",
             }

        return {"valid": True, "row_count": len(rows), "columns": reader.fieldnames}

    except Exception as e:
        return {"valid": False, "error": f"Error reading CSV: {e}"}


def validate_file_permissions(file_path: str, required_perms: str = "r") -> Dict[str, Any]:
    """"""

   

    
   
"""
    Validate file permissions
   """

    
   

    Args:
        file_path: Path to file
        required_perms: Required permissions (r/w/x)
   
""""""

    Validate file permissions
   

    
   
"""
    Returns:
        Dict with validation results
   """"""
    
   """

    file_obj = Path(file_path)
   

    
   
""""""


    

   

    file_obj = Path(file_path)
   
""""""
    if not file_obj.exists():
        return {"valid": False, "error": f"File does not exist: {file_path}"}

    try:
        # Check read permission
        if "r" in required_perms and not os.access(file_path, os.R_OK):
            return {"valid": False, "error": "File is not readable"}

        # Check write permission
        if "w" in required_perms and not os.access(file_path, os.W_OK):
            return {"valid": False, "error": "File is not writable"}

        # Check execute permission
        if "x" in required_perms and not os.access(file_path, os.X_OK):
            return {"valid": False, "error": "File is not executable"}

        return {"valid": True, "permissions": oct(file_obj.stat().st_mode)[-3:]}

    except Exception as e:
        return {"valid": False, "error": f"Error checking permissions: {e}"}