"""SQL Generation Agent."""
from typing import Dict, Any
from app.services.llm_service import llm_service
from app.services.data_service import data_service
from app.utils.prompts import SQL_GENERATION_SYSTEM, SQL_GENERATION_USER
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


async def sql_generation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that generates SQL queries from natural language.
    
    Converts user intent and entities into DuckDB SQL.
    """
    try:
        logger.info(f"SQL Generation Agent: Generating SQL")
        
        intent = state.get("intent")
        entities = state.get("entities", {})
        file_metadata = state.get("file_metadata")
        table_name = state.get("table_name")
        
        if not file_metadata or not table_name:
            errors = state.get("errors", [])
            return {
                "errors": errors + ["No file metadata or table name available"],
                "sql_valid": False
            }
        
        # Prepare schema information
        schema_info = {
            "columns": file_metadata.get("columns", []),
            "schema": file_metadata.get("schema", {}),
            "date_columns": file_metadata.get("date_columns", []),
            "categorical_columns": file_metadata.get("categorical_columns", []),
            "numerical_columns": file_metadata.get("numerical_columns", []),
            "sample_values": file_metadata.get("unique_values", {})
        }
        
        # Check if this is a retry and include error context
        retry_count = state.get("retry_count", 0)
        errors = state.get("errors", [])
        
        prompt = SQL_GENERATION_USER.format(
            intent=intent,
            entities=json.dumps(entities, indent=2),
            table_name=table_name,
            schema=json.dumps(schema_info["schema"], indent=2),
            date_columns=", ".join(file_metadata.get("date_columns", [])) or "None",
            categorical_columns=", ".join(file_metadata.get("categorical_columns", [])) or "None",
            numerical_columns=", ".join(file_metadata.get("numerical_columns", [])) or "None"
        )
        
        # Add error context if this is a retry
        if retry_count > 0 and errors:
            prompt += f"\n\nPREVIOUS ATTEMPT FAILED with errors:\n" + "\n".join(errors[-3:])
            prompt += "\n\nPlease fix the query to handle these issues. Use TRY_CAST and filter out invalid values like 'Nill', 'Null', empty strings."
        
        # Generate SQL
        sql_query = await llm_service.generate(
            prompt=prompt,
            system_prompt=SQL_GENERATION_SYSTEM
        )
        
        # Clean up SQL (remove markdown, extra whitespace)
        sql_query = sql_query.strip()
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Track all SQL attempts
        sql_attempts = state.get("sql_attempts", [])
        sql_attempts.append(sql_query)
        
        # Validate SQL
        is_valid, error = data_service.validate_sql(sql_query)
        
        if not is_valid:
            logger.warning(f"Invalid SQL generated: {error}")
            errors = state.get("errors", [])
            return {
                "sql_query": sql_query,
                "sql_valid": False,
                "sql_attempts": sql_attempts,
                "errors": errors + [f"Invalid SQL: {error}"]
            }
        
        logger.info(f"Generated valid SQL: {sql_query[:100]}...")
        
        return {
            "sql_query": sql_query,
            "sql_valid": True,
            "sql_attempts": sql_attempts
        }
    
    except Exception as e:
        logger.error(f"Error in SQL generation agent: {e}")
        errors = state.get("errors", [])
        return {
            "sql_valid": False,
            "errors": errors + [f"SQL generation error: {str(e)}"]
        }

