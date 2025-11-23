"""LangGraph workflow for multi-agent system."""
from typing import Dict, Any, TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from app.models.schemas import QueryType
from app.agents.query_understanding import query_understanding_agent
from app.agents.sql_generation import sql_generation_agent
from app.agents.data_retrieval import data_retrieval_agent
from app.agents.validation import validation_agent
from app.agents.insight_generation import insight_generation_agent
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# Define state as TypedDict for LangGraph
class GraphState(TypedDict, total=False):
    """State for LangGraph workflow."""
    # User input
    user_query: str
    file_id: Optional[str]
    conversation_id: str
    
    # Query understanding
    query_type: Optional[str]
    entities: Dict[str, Any]
    intent: Optional[str]
    
    # Data context
    file_metadata: Optional[Dict[str, Any]]
    table_name: Optional[str]
    
    # SQL generation
    sql_query: Optional[str]
    sql_valid: bool
    sql_attempts: List[str]  # Track all SQL queries attempted
    
    # Data retrieval
    query_results: Optional[List[Dict[str, Any]]]
    result_count: int
    
    # Validation
    validation_passed: bool
    validation_errors: List[str]
    retry_count: int
    
    # Insight generation
    insights: Optional[str]
    visualizations: Optional[List[Dict[str, Any]]]
    
    # Error handling
    errors: List[str]


def should_generate_sql(state: GraphState) -> str:
    """Decide if we need to generate SQL (for Q&A queries)."""
    query_type = state.get("query_type")
    # Both Q&A and dashboard queries need SQL execution
    if query_type in ["qa", "dashboard"]:
        return "sql_generation"
    elif query_type == "summarization":
        return "generate_summary"
    else:
        # Default to SQL for unknown types
        return "sql_generation"


def should_retry_sql(state: GraphState) -> str:
    """Decide if we need to retry SQL generation."""
    validation_passed = state.get("validation_passed", False)
    retry_count = state.get("retry_count", 0)
    
    if not validation_passed and retry_count < 2:
        return "sql_generation"
    else:
        return "insight_generation"


def create_agent_graph() -> StateGraph:
    """Create the LangGraph workflow."""
    
    # Create graph with dict-based state
    workflow = StateGraph(GraphState)
    
    # Add nodes (agents)
    workflow.add_node("query_understanding", query_understanding_agent)
    workflow.add_node("sql_generation", sql_generation_agent)
    workflow.add_node("data_retrieval", data_retrieval_agent)
    workflow.add_node("validation", validation_agent)
    workflow.add_node("insight_generation", insight_generation_agent)
    
    # Define the flow
    # Start -> Query Understanding
    workflow.set_entry_point("query_understanding")
    
    # Query Understanding -> Branch based on query type
    workflow.add_conditional_edges(
        "query_understanding",
        should_generate_sql,
        {
            "sql_generation": "sql_generation",
            "generate_summary": "insight_generation"
        }
    )
    
    # SQL Generation -> Data Retrieval
    workflow.add_edge("sql_generation", "data_retrieval")
    
    # Data Retrieval -> Validation
    workflow.add_edge("data_retrieval", "validation")
    
    # Validation -> Branch (retry or continue)
    workflow.add_conditional_edges(
        "validation",
        should_retry_sql,
        {
            "sql_generation": "sql_generation",
            "insight_generation": "insight_generation"
        }
    )
    
    # Insight Generation -> End
    workflow.add_edge("insight_generation", END)
    
    return workflow.compile()


# Global graph instance
agent_graph = create_agent_graph()


async def run_agent_workflow(state_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Run the agent workflow."""
    try:
        logger.info("Starting agent workflow")
        
        # LangGraph works with dicts, not Pydantic models
        # Convert any Pydantic models to dicts
        clean_state = {}
        for key, value in state_dict.items():
            if hasattr(value, 'model_dump'):
                # Convert Pydantic model to dict
                clean_state[key] = value.model_dump()
            else:
                clean_state[key] = value
        
        # Run the graph with dict state
        result = await agent_graph.ainvoke(clean_state)
        
        logger.info("Agent workflow completed")
        
        # Return result (already a dict)
        return result
    
    except Exception as e:
        logger.error(f"Error in agent workflow: {e}")
        raise

