"""Data Profiling Agent."""
from typing import Dict, Any
from app.models.schemas import AgentState, FileMetadata
from app.services.data_service import data_service
from app.services.vector_service import vector_service
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


async def data_profiling_agent(
    file_id: str,
    metadata: Dict[str, Any]
) -> FileMetadata:
    """
    Agent that profiles uploaded data files.
    
    Extracts:
    - Column types and schema
    - Date ranges
    - Categorical values
    - Summary statistics
    - Business entities
    """
    try:
        logger.info(f"Data Profiling Agent: Profiling file {file_id}")
        
        # Create FileMetadata object
        file_metadata = FileMetadata(
            file_id=file_id,
            filename=metadata.get("filename", "unknown"),
            size=metadata.get("size", 0),
            upload_date=metadata.get("upload_date"),
            row_count=metadata.get("row_count", 0),
            column_count=metadata.get("column_count", 0),
            columns=metadata.get("columns", []),  # Added this field
            schema=metadata.get("schema", {}),
            date_columns=metadata.get("date_columns", []),
            categorical_columns=metadata.get("categorical_columns", []),
            numerical_columns=metadata.get("numerical_columns", []),
            date_range=metadata.get("date_range"),
            unique_values=metadata.get("unique_values", {}),
            summary_stats=metadata.get("summary_stats", {})
        )
        
        # Store metadata in vector store (store ALL fields for retrieval)
        metadata_dict = file_metadata.model_dump()
        # Convert datetime to string for JSON serialization
        if metadata_dict.get("upload_date"):
            metadata_dict["upload_date"] = metadata_dict["upload_date"].isoformat()
        
        await vector_service.store_file_metadata(
            file_id=file_id,
            metadata=metadata_dict
        )
        
        logger.info(f"Profiled {file_metadata.row_count} rows, {file_metadata.column_count} columns")
        
        return file_metadata
    
    except Exception as e:
        logger.error(f"Error in data profiling agent: {e}")
        raise

