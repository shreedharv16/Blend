"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class QueryType(str, Enum):
    """Types of queries supported."""
    SUMMARIZATION = "summarization"
    QA = "qa"
    DASHBOARD = "dashboard"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Upload schemas
class UploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str
    filename: str
    size: int
    row_count: int
    column_count: int
    columns: List[str]
    preview: List[Dict[str, Any]]
    summary: Optional[str] = None
    processing_time: float


class FileMetadata(BaseModel):
    """Metadata about an uploaded file."""
    file_id: str
    filename: str
    size: int
    upload_date: datetime
    row_count: int
    column_count: int
    columns: List[str]  # Add this field
    schema: Dict[str, str]
    date_columns: List[str]
    categorical_columns: List[str]
    numerical_columns: List[str]
    date_range: Optional[Dict[str, Any]] = None
    unique_values: Dict[str, List[Any]] = Field(default_factory=dict)
    summary_stats: Dict[str, Any] = Field(default_factory=dict)


# Chat schemas
class ChatMessage(BaseModel):
    """A single chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    file_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    message: str
    role: MessageRole = MessageRole.ASSISTANT
    conversation_id: str
    query_type: Optional[QueryType] = None
    data: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    processing_time: float


# Agent state schemas
class AgentState(BaseModel):
    """State shared between agents in LangGraph."""
    # User input
    user_query: str
    file_id: Optional[str] = None
    conversation_id: str
    
    # Query understanding
    query_type: Optional[QueryType] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    intent: Optional[str] = None
    
    # Data context
    file_metadata: Optional[Dict[str, Any]] = None  # Changed to Dict for LangGraph compatibility
    table_name: Optional[str] = None
    
    # SQL generation
    sql_query: Optional[str] = None
    sql_valid: bool = False
    
    # Data retrieval
    query_results: Optional[List[Dict[str, Any]]] = None
    result_count: int = 0
    
    # Validation
    validation_passed: bool = False
    validation_errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    
    # Insight generation
    insights: Optional[str] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    
    # Error handling
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


# Dashboard schemas
class KPICard(BaseModel):
    """Key Performance Indicator card."""
    title: str
    value: Any
    unit: Optional[str] = None
    change: Optional[float] = None
    change_label: Optional[str] = None
    trend: Optional[Literal["up", "down", "neutral"]] = None


class ChartConfig(BaseModel):
    """Configuration for a chart."""
    type: Literal["bar", "line", "pie", "area", "scatter", "table"]
    title: str
    data: List[Dict[str, Any]]
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    colors: Optional[List[str]] = None
    height: int = 300


class DashboardResponse(BaseModel):
    """Response containing dashboard data."""
    file_id: str
    kpis: List[KPICard]
    charts: List[ChartConfig]
    generated_at: datetime = Field(default_factory=datetime.now)


# Summarization schemas
class SummaryRequest(BaseModel):
    """Request to generate a summary."""
    file_id: str
    focus_areas: Optional[List[str]] = None


class SummaryResponse(BaseModel):
    """Response containing summary."""
    file_id: str
    summary: str
    key_insights: List[str]
    kpis: List[KPICard]
    generated_at: datetime = Field(default_factory=datetime.now)

