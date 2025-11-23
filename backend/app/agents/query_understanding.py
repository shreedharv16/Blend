"""Query Understanding Agent."""
from typing import Dict, Any
from app.services.llm_service import llm_service
from app.utils.prompts import QUERY_UNDERSTANDING_SYSTEM, QUERY_UNDERSTANDING_USER
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


async def query_understanding_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that understands user query and extracts intent.
    
    Determines:
    - Query type (summarization, qa, dashboard)
    - Intent (what user wants to know)
    - Entities (dates, regions, categories, metrics)
    """
    try:
        logger.info(f"Query Understanding Agent: Processing query")
        
        user_query = state.get("user_query", "")
        file_metadata = state.get("file_metadata")
        
        # Prepare schema information
        schema_info = {}
        if file_metadata:
            schema_info = {
                "columns": file_metadata.get("columns", []),
                "schema": file_metadata.get("schema", {}),
                "date_columns": file_metadata.get("date_columns", []),
                "categorical_columns": file_metadata.get("categorical_columns", []),
                "numerical_columns": file_metadata.get("numerical_columns", [])
            }
        
        # Format prompt
        prompt = QUERY_UNDERSTANDING_USER.format(
            query=user_query,
            schema=json.dumps(schema_info, indent=2) if schema_info else "No schema available"
        )
        
        # Generate response
        response = await llm_service.generate_json(
            prompt=prompt,
            system_prompt=QUERY_UNDERSTANDING_SYSTEM
        )
        
        # Extract information
        query_type_str = response.get("query_type", "qa")
        intent = response.get("intent", user_query)
        entities = response.get("entities", {})
        
        # Store as string for dict compatibility
        query_type = query_type_str if query_type_str in ["summarization", "qa", "dashboard"] else "qa"
        
        logger.info(f"Query type: {query_type}, Intent: {intent}")
        
        # Return only the fields we're updating, LangGraph will merge with existing state
        return {
            "query_type": query_type,
            "intent": intent,
            "entities": entities if entities else {}
        }
    
    except Exception as e:
        logger.error(f"Error in query understanding agent: {e}")
        errors = state.get("errors", [])
        return {
            "query_type": "qa",
            "intent": state.get("user_query", ""),
            "entities": {},
            "errors": errors + [f"Query understanding error: {str(e)}"]
        }

