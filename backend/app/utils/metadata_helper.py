"""Helper functions for metadata handling."""
from typing import Dict, Any
from datetime import datetime


def normalize_metadata(metadata_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize metadata to ensure all required fields exist.
    Handles both old and new metadata formats.
    """
    # Required fields with defaults
    normalized = {
        "file_id": metadata_dict.get("file_id", ""),
        "filename": metadata_dict.get("filename", "unknown.csv"),
        "size": metadata_dict.get("size", 0),
        "upload_date": metadata_dict.get("upload_date", datetime.now().isoformat()),
        "row_count": metadata_dict.get("row_count", 0),
        "column_count": metadata_dict.get("column_count", 0),
        "columns": metadata_dict.get("columns", []),
        "schema": metadata_dict.get("schema", {}),
        "date_columns": metadata_dict.get("date_columns", []),
        "categorical_columns": metadata_dict.get("categorical_columns", []),
        "numerical_columns": metadata_dict.get("numerical_columns", []),
        "date_range": metadata_dict.get("date_range"),
        "unique_values": metadata_dict.get("unique_values", {}),
        "summary_stats": metadata_dict.get("summary_stats", {})
    }
    
    # Convert upload_date string to datetime if needed
    if isinstance(normalized["upload_date"], str):
        try:
            normalized["upload_date"] = datetime.fromisoformat(normalized["upload_date"])
        except:
            normalized["upload_date"] = datetime.now()
    
    # Remove 'type' field if present (Qdrant internal)
    normalized.pop("type", None)
    
    return normalized

