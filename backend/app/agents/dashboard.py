"""Dashboard Generation Agent."""
from typing import Dict, Any, List
from app.models.schemas import FileMetadata, KPICard, ChartConfig
from app.services.data_service import data_service
from app.services.llm_service import llm_service
from app.utils.prompts import DASHBOARD_GENERATION_SYSTEM, DASHBOARD_GENERATION_USER
from app.utils.chunking import create_table_name
from app.utils.logger import setup_logger
import json

logger = setup_logger(__name__)


async def dashboard_agent(
    file_id: str,
    file_metadata: FileMetadata
) -> Dict[str, Any]:
    """
    Agent that generates dynamic dashboards.
    
    Creates KPI cards and chart configurations.
    """
    try:
        logger.info(f"Dashboard Agent: Generating dashboard for {file_id}")
        
        table_name = create_table_name(file_id)
        
        # Get sample data
        sample_data = data_service.get_preview(table_name, limit=20)
        
        # Generate KPIs
        kpis = await _generate_kpis(table_name, file_metadata)
        
        # Generate charts
        charts = await _generate_charts(table_name, file_metadata, sample_data)
        
        logger.info(f"Generated {len(kpis)} KPIs and {len(charts)} charts")
        
        return {
            "file_id": file_id,
            "kpis": kpis,
            "charts": charts
        }
    
    except Exception as e:
        logger.error(f"Error in dashboard agent: {e}")
        raise


async def _generate_kpis(
    table_name: str,
    file_metadata: FileMetadata
) -> List[Dict[str, Any]]:
    """Generate KPI cards."""
    kpis = []
    
    try:
        # Total rows KPI
        kpis.append({
            "title": "Total Records",
            "value": file_metadata.row_count,
            "unit": "rows",
            "trend": "neutral"
        })
        
        # Generate KPIs for numerical columns
        for col in file_metadata.numerical_columns[:3]:  # Limit to 3
            if col in file_metadata.summary_stats:
                stats = file_metadata.summary_stats[col]
                
                if stats.get("sum"):
                    kpis.append({
                        "title": f"Total {col}",
                        "value": round(stats["sum"], 2),
                        "unit": "",
                        "trend": "neutral"
                    })
                
                if stats.get("mean"):
                    kpis.append({
                        "title": f"Average {col}",
                        "value": round(stats["mean"], 2),
                        "unit": "",
                        "trend": "neutral"
                    })
        
        # Count distinct for categorical columns
        for col in file_metadata.categorical_columns[:2]:  # Limit to 2
            try:
                result = data_service.execute_query(
                    f"SELECT COUNT(DISTINCT {col}) as count FROM {table_name}"
                )
                if result:
                    kpis.append({
                        "title": f"Unique {col}",
                        "value": result[0]["count"],
                        "unit": "",
                        "trend": "neutral"
                    })
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error generating KPIs: {e}")
    
    return kpis[:6]  # Limit to 6 KPIs


async def _generate_charts(
    table_name: str,
    file_metadata: FileMetadata,
    sample_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate chart configurations."""
    charts = []
    
    try:
        # Chart 1: Distribution of categorical column
        if file_metadata.categorical_columns and file_metadata.numerical_columns:
            cat_col = file_metadata.categorical_columns[0]
            num_col = file_metadata.numerical_columns[0]
            
            # Get top categories
            query = f"""
                SELECT {cat_col}, SUM({num_col}) as total
                FROM {table_name}
                WHERE {cat_col} IS NOT NULL AND {num_col} IS NOT NULL
                GROUP BY {cat_col}
                ORDER BY total DESC
                LIMIT 10
            """
            
            try:
                data = data_service.execute_query(query)
                if data:
                    charts.append({
                        "type": "bar",
                        "title": f"{num_col} by {cat_col}",
                        "data": data,
                        "x_axis": cat_col,
                        "y_axis": "total",
                        "height": 300
                    })
            except:
                pass
        
        # Chart 2: Time series if date column exists
        if file_metadata.date_columns and file_metadata.numerical_columns:
            date_col = file_metadata.date_columns[0]
            num_col = file_metadata.numerical_columns[0]
            
            query = f"""
                SELECT {date_col} as date, SUM({num_col}) as total
                FROM {table_name}
                WHERE {date_col} IS NOT NULL AND {num_col} IS NOT NULL
                GROUP BY {date_col}
                ORDER BY {date_col}
                LIMIT 30
            """
            
            try:
                data = data_service.execute_query(query)
                if data:
                    charts.append({
                        "type": "line",
                        "title": f"{num_col} Over Time",
                        "data": data,
                        "x_axis": "date",
                        "y_axis": "total",
                        "height": 300
                    })
            except:
                pass
        
        # Chart 3: Top items table
        if file_metadata.categorical_columns and file_metadata.numerical_columns:
            cat_col = file_metadata.categorical_columns[0]
            num_col = file_metadata.numerical_columns[0]
            
            query = f"""
                SELECT {cat_col}, COUNT(*) as count, 
                       ROUND(AVG({num_col}), 2) as avg_{num_col}
                FROM {table_name}
                WHERE {cat_col} IS NOT NULL
                GROUP BY {cat_col}
                ORDER BY count DESC
                LIMIT 10
            """
            
            try:
                data = data_service.execute_query(query)
                if data:
                    charts.append({
                        "type": "table",
                        "title": f"Top {cat_col} Summary",
                        "data": data,
                        "height": 300
                    })
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
    
    return charts[:4]  # Limit to 4 charts

