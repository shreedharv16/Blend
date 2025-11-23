"""Insight Generation Agent."""
from typing import Dict, Any, List
from app.services.llm_service import llm_service
from app.utils.prompts import INSIGHT_GENERATION_SYSTEM, INSIGHT_GENERATION_USER
from app.utils.logger import setup_logger
import json
import re

logger = setup_logger(__name__)


async def insight_generation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent that generates insights from query results.
    
    Creates human-readable insights and suggests visualizations.
    """
    try:
        logger.info(f"Insight Generation Agent: Generating insights")
        
        query = state.get("user_query", "")
        results = state.get("query_results", [])
        result_count = state.get("result_count", 0)
        file_metadata = state.get("file_metadata")
        
        # Prepare results for LLM (limit to avoid token overflow)
        max_results = 50
        limited_results = results[:max_results] if results else []
        
        # Prepare metadata
        metadata_info = {}
        if file_metadata:
            metadata_info = {
                "filename": file_metadata.get("filename", "unknown"),
                "row_count": file_metadata.get("row_count", 0),
                "date_range": file_metadata.get("date_range", {}),
                "columns": file_metadata.get("columns", [])
            }
        
        # Format prompt
        prompt = INSIGHT_GENERATION_USER.format(
            query=query,
            results=json.dumps(limited_results, indent=2, default=str),
            count=result_count,
            metadata=json.dumps(metadata_info, indent=2)
        )
        
        # Generate insights
        insights = await llm_service.generate(
            prompt=prompt,
            system_prompt=INSIGHT_GENERATION_SYSTEM,
            temperature=0.3
        )
        
        # Ensure insights is not None or empty
        if not insights or not insights.strip():
            logger.warning("LLM returned empty insights, using fallback")
            insights = _generate_fallback_insights(state)
        
        # Try to extract visualizations if mentioned
        visualizations = _extract_visualizations(insights, results)
        
        logger.info(f"Generated insights successfully (length: {len(insights)})")
        
        return {
            "insights": insights,
            "visualizations": visualizations
        }
    
    except Exception as e:
        logger.error(f"Error in insight generation agent: {e}")
        # Provide fallback insights
        fallback = _generate_fallback_insights(state)
        errors = state.get("errors", [])
        return {
            "insights": fallback,
            "visualizations": [],
            "errors": errors + [f"Insight generation error: {str(e)}"]
        }


def _extract_visualizations(insights: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract visualization suggestions from insights."""
    visualizations = []
    
    if not results:
        return visualizations
    
    # Simple heuristics for visualization suggestions
    insights_lower = insights.lower()
    
    # Check for chart keywords
    if any(keyword in insights_lower for keyword in ["chart", "graph", "plot", "visualize"]):
        # Suggest a bar chart if we have categorical and numerical data
        if len(results) > 0:
            sample = results[0]
            keys = list(sample.keys())
            
            if len(keys) >= 2:
                # Assume first column is x-axis, second is y-axis
                visualizations.append({
                    "type": "bar",
                    "title": "Data Visualization",
                    "data": results[:20],  # Limit to 20 items
                    "x_axis": keys[0],
                    "y_axis": keys[1],
                    "height": 300
                })
    
    return visualizations


def _generate_fallback_insights(state: Dict[str, Any]) -> str:
    """Generate simple fallback insights if LLM fails."""
    results = state.get("query_results", [])
    result_count = state.get("result_count", 0)
    
    if result_count == 0:
        return "No data found matching your query. Try rephrasing or checking the date range."
    
    # Simple summary
    insights = f"Found {result_count} records matching your query.\n\n"
    
    if results and len(results) > 0:
        sample = results[0]
        insights += "Sample data:\n"
        for key, value in list(sample.items())[:5]:
            insights += f"- {key}: {value}\n"
    
    return insights

