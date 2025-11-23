"""Data Retrieval Agent."""
from typing import Dict, Any
from app.services.data_service import data_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def data_retrieval_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that retrieves data by executing SQL queries.
    
    Executes validated SQL and returns results.
    """
    try:
        logger.info(f"Data Retrieval Agent: Executing query")
        
        sql_query = state.get("sql_query")
        sql_valid = state.get("sql_valid", False)
        
        if not sql_query or not sql_valid:
            errors = state.get("errors", [])
            return {
                "errors": errors + ["No valid SQL query to execute"],
                "query_results": [],
                "result_count": 0
            }
        
        # Execute query
        results = data_service.execute_query(sql_query)
        
        logger.info(f"Retrieved {len(results)} rows")
        
        return {
            "query_results": results,
            "result_count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Error in data retrieval agent: {e}")
        errors = state.get("errors", [])
        return {
            "query_results": [],
            "result_count": 0,
            "errors": errors + [f"Data retrieval error: {str(e)}"]
        }

