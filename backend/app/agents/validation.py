"""Validation Agent."""
from typing import Dict, Any
from app.services.llm_service import llm_service
from app.utils.prompts import VALIDATION_SYSTEM, VALIDATION_USER
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


async def validation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that validates query results.
    
    Checks if results are reasonable and complete.
    """
    try:
        logger.info(f"Validation Agent: Validating results")
        
        query = state.get("user_query", "")
        sql = state.get("sql_query")
        result_count = state.get("result_count", 0)
        results = state.get("query_results", [])
        
        # Basic validation checks
        validation_errors = []
        
        # Check if we have results
        if result_count == 0:
            # Empty results might be valid, but let's check with LLM
            validation_errors.append("No results returned")
        
        # Check for all null results
        if results and all(
            all(v is None for v in row.values())
            for row in results[:10]
        ):
            validation_errors.append("All values are NULL")
        
        # Sample results for LLM validation
        sample_results = results[:5] if results else []
        
        # Use LLM for deeper validation
        prompt = VALIDATION_USER.format(
            query=query,
            sql=sql or "N/A",
            result_count=result_count,
            sample_results=json.dumps(sample_results, indent=2, default=str)
        )
        
        response = await llm_service.generate_json(
            prompt=prompt,
            system_prompt=VALIDATION_SYSTEM
        )
        
        is_valid = response.get("valid", True)
        llm_issues = response.get("issues", [])
        
        # Combine validation errors
        all_errors = validation_errors + llm_issues
        
        # Check retry count
        retry_count = state.get("retry_count", 0)
        if not is_valid and retry_count < 2:
            logger.warning(f"Validation failed: {all_errors}. Will retry.")
            return {
                "validation_passed": False,
                "validation_errors": all_errors,
                "retry_count": retry_count + 1
            }
        
        # If max retries reached or validation passed
        if is_valid or retry_count >= 2:
            logger.info("Validation passed or max retries reached")
            return {
                "validation_passed": True,
                "validation_errors": []
            }
        
        return {
            "validation_passed": False,
            "validation_errors": all_errors
        }
    
    except Exception as e:
        logger.error(f"Error in validation agent: {e}")
        # Continue even if validation fails
        return {
            "validation_passed": True,
            "validation_errors": [f"Validation error: {str(e)}"]
        }

