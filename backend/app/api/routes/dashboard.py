"""Dashboard endpoints."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import DashboardResponse, FileMetadata
from app.services.vector_service import vector_service
from app.services.cache_service import cache_service
from app.agents.dashboard import dashboard_agent
from app.utils.metadata_helper import normalize_metadata
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{file_id}", response_model=DashboardResponse)
async def get_dashboard(file_id: str):
    """Get dashboard for a file."""
    try:
        # Check cache first
        cache_key = f"dashboard:{file_id}"
        cached_dashboard = cache_service.get(cache_key)
        
        if cached_dashboard:
            logger.info(f"Returning cached dashboard for {file_id}")
            return DashboardResponse(**cached_dashboard)
        
        # Get file metadata
        metadata_dict = await vector_service.get_file_metadata(file_id)
        if not metadata_dict:
            raise HTTPException(
                status_code=404,
                detail=f"File {file_id} not found"
            )
        
        # Normalize metadata to handle old and new formats
        normalized = normalize_metadata(metadata_dict)
        file_metadata = FileMetadata(**normalized)
        
        # Generate dashboard
        dashboard_data = await dashboard_agent(file_id, file_metadata)
        
        # Create response
        response = DashboardResponse(
            file_id=file_id,
            kpis=dashboard_data["kpis"],
            charts=dashboard_data["charts"],
            generated_at=datetime.now()
        )
        
        # Cache the dashboard
        cache_service.set(
            cache_key,
            response.model_dump(),
            ttl=1800  # 30 minutes
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_id}/refresh")
async def refresh_dashboard(file_id: str):
    """Refresh dashboard (clear cache and regenerate)."""
    try:
        # Clear cache
        cache_key = f"dashboard:{file_id}"
        cache_service.delete(cache_key)
        
        # Regenerate
        return await get_dashboard(file_id)
    
    except Exception as e:
        logger.error(f"Error refreshing dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

