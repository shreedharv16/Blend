"""File upload endpoints."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import time
import shutil
from datetime import datetime
from app.models.schemas import UploadResponse
from app.services.data_service import data_service
from app.agents.data_profiling import data_profiling_agent
from app.utils.chunking import generate_file_id
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV or Excel file."""
    try:
        start_time = time.time()
        
        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only CSV and Excel files are supported"
            )
        
        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Generate file ID
        file_id = generate_file_id(file.filename)
        
        # Save file
        file_path = settings.UPLOAD_DIR / f"{file_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        
        # Load into DuckDB and profile
        metadata = data_service.load_csv_to_table(file_path, file_id)
        
        # Profile with data profiling agent
        file_metadata = await data_profiling_agent(
            file_id=file_id,
            metadata={
                **metadata,
                "filename": file.filename,
                "size": file_size,
                "upload_date": datetime.now()
            }
        )
        
        # Get preview
        try:
            preview = data_service.get_preview(metadata["table_name"], limit=5)
        except Exception as preview_error:
            logger.warning(f"Could not generate preview: {preview_error}")
            preview = []
        
        processing_time = time.time() - start_time
        
        try:
            return UploadResponse(
                file_id=file_id,
                filename=file.filename,
                size=file_size,
                row_count=metadata["row_count"],
                column_count=metadata["column_count"],
                columns=metadata["columns"],
                preview=preview,
                summary=f"Successfully loaded {metadata['row_count']} rows with {metadata['column_count']} columns",
                processing_time=processing_time
            )
        except Exception as response_error:
            logger.error(f"Error creating response: {response_error}")
            logger.error(f"Metadata: {metadata}")
            logger.error(f"Preview: {preview}")
            raise
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
async def list_files():
    """List all uploaded files."""
    try:
        files = []
        for file_path in settings.UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "uploaded_at": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
        
        return {"files": files}
    
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

