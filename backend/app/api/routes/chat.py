"""Chat endpoints."""
from fastapi import APIRouter, HTTPException
import time
import uuid
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    MessageRole,
    AgentState,
    FileMetadata
)
from app.services.vector_service import vector_service
from app.services.cache_service import cache_service
from app.agents.graph import run_agent_workflow
from app.utils.chunking import create_table_name
from app.utils.metadata_helper import normalize_metadata
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get response."""
    try:
        start_time = time.time()
        
        # Generate or use conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get file metadata if file_id provided
        file_metadata = None
        table_name = None
        
        if request.file_id:
            # Try cache first
            cache_key = f"metadata:{request.file_id}"
            cached_metadata = cache_service.get(cache_key)
            
            if cached_metadata:
                # Normalize metadata to handle old and new formats
                normalized = normalize_metadata(cached_metadata)
                file_metadata = FileMetadata(**normalized)
            else:
                # Get from vector store
                metadata_dict = await vector_service.get_file_metadata(request.file_id)
                if metadata_dict:
                    # Normalize metadata to handle old and new formats
                    normalized = normalize_metadata(metadata_dict)
                    file_metadata = FileMetadata(**normalized)
                    cache_service.set(cache_key, normalized)
            
            if not file_metadata:
                raise HTTPException(
                    status_code=404,
                    detail=f"File {request.file_id} not found"
                )
            
            table_name = create_table_name(request.file_id)
        
        # Create initial state with all required defaults for LangGraph
        state_dict = {
            "user_query": request.message,
            "file_id": request.file_id,
            "conversation_id": conversation_id,
            "file_metadata": file_metadata.model_dump() if file_metadata else None,
            "table_name": table_name,
            # Initialize all required fields with defaults
            "query_type": None,
            "entities": {},
            "intent": None,
            "sql_query": None,
            "sql_valid": False,
            "sql_attempts": [],  # Track all SQL queries
            "query_results": None,
            "result_count": 0,
            "validation_passed": False,
            "validation_errors": [],
            "retry_count": 0,
            "insights": None,
            "visualizations": None,
            "errors": []
        }
        
        # Run agent workflow
        result = await run_agent_workflow(state_dict)
        
        # Extract response with proper fallbacks
        insights = result.get("insights")
        
        # Handle None or empty insights
        if not insights:
            # Check if there are errors
            errors = result.get("errors", [])
            if errors:
                insights = f"I encountered some issues:\n" + "\n".join(errors)
            else:
                insights = "I couldn't generate a response. Please try again."
        
        query_type = result.get("query_type")
        visualizations = result.get("visualizations")
        query_results = result.get("query_results")
        
        # Prepare data for response
        data = None
        if query_results:
            # Include all SQL attempts
            sql_attempts = result.get("sql_attempts", [])
            final_sql = result.get("sql_query")
            
            data = {
                "results": query_results[:100],  # Limit results
                "count": len(query_results),
                "sql": final_sql,
                "sql_attempts": sql_attempts if len(sql_attempts) > 1 else None  # Show attempts if there were retries
            }
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            message=insights,
            role=MessageRole.ASSISTANT,
            conversation_id=conversation_id,
            query_type=query_type,
            data=data,
            visualizations=visualizations,
            processing_time=processing_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{conversation_id}")
async def get_history(conversation_id: str):
    """Get conversation history."""
    try:
        # In a production system, this would fetch from a database
        # For now, return empty
        return {
            "conversation_id": conversation_id,
            "messages": []
        }
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

