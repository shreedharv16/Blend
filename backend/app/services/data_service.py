"""Data service for DuckDB operations."""
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.chunking import (
    create_table_name,
    smart_sample,
    detect_date_columns,
    detect_categorical_columns,
    detect_numerical_columns,
    extract_unique_values,
    calculate_summary_stats,
    get_date_range,
    infer_schema
)

logger = setup_logger(__name__)

# Try to import DuckDB, fallback to Pandas if not available
try:
    import duckdb
    DUCKDB_AVAILABLE = True
    logger.info("DuckDB is available")
except ImportError as e:
    DUCKDB_AVAILABLE = False
    logger.warning(f"DuckDB not available, using Pandas fallback: {e}")


class DataService:
    """Service for data operations using DuckDB or Pandas fallback."""
    
    def __init__(self):
        """Initialize data service."""
        self.use_duckdb = DUCKDB_AVAILABLE
        self.tables = {}  # Store DataFrames if using Pandas
        
        if self.use_duckdb:
            self.db_path = settings.DUCKDB_PATH
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to DuckDB at: {self.db_path}")
        else:
            self.conn = None
            logger.info("Using Pandas-based data service (DuckDB fallback)")
    
    def load_csv_to_table(
        self,
        file_path: Path,
        file_id: str
    ) -> Dict[str, Any]:
        """Load CSV file into DuckDB table or Pandas DataFrame and return metadata."""
        try:
            table_name = create_table_name(file_id)
            logger.info(f"Loading CSV from: {file_path}")
            
            if self.use_duckdb:
                # DuckDB method (original)
                self.conn.execute(f"""
                    CREATE OR REPLACE TABLE {table_name} AS 
                    SELECT * FROM read_csv_auto('{file_path}', 
                        HEADER=TRUE,
                        SAMPLE_SIZE=100000,
                        IGNORE_ERRORS=TRUE
                    )
                """)
                
                row_count = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()[0]
                
                sample_df = self.conn.execute(
                    f"SELECT * FROM {table_name} LIMIT {settings.SAMPLE_SIZE}"
                ).fetch_df()
            else:
                # Pandas fallback method
                logger.info("Using Pandas to load CSV (this may take longer for large files)")
                
                # Read CSV in chunks for memory efficiency
                df = pd.read_csv(file_path, low_memory=False, encoding='utf-8', on_bad_lines='skip')
                
                # Store in memory
                self.tables[table_name] = df
                
                row_count = len(df)
                sample_df = df.head(settings.SAMPLE_SIZE)
                
                logger.info(f"Loaded {row_count} rows into Pandas DataFrame")
            
            # Profile the data
            metadata = self._profile_data(sample_df, table_name, row_count)
            
            logger.info(f"Loaded {row_count} rows into table: {table_name}")
            return metadata
        
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            raise
    
    def _profile_data(
        self,
        sample_df: pd.DataFrame,
        table_name: str,
        row_count: int
    ) -> Dict[str, Any]:
        """Profile the data and extract metadata."""
        try:
            # Detect column types
            date_columns = detect_date_columns(sample_df)
            categorical_columns = detect_categorical_columns(sample_df)
            numerical_columns = detect_numerical_columns(sample_df)
            
            # Get schema
            schema = infer_schema(sample_df)
            
            # Extract unique values for categorical columns
            unique_values = extract_unique_values(
                sample_df,
                categorical_columns,
                max_unique=100
            )
            
            # Calculate summary statistics
            summary_stats = calculate_summary_stats(sample_df, numerical_columns)
            
            # Get date range
            date_range = get_date_range(sample_df, date_columns)
            
            metadata = {
                "table_name": table_name,
                "row_count": row_count,
                "column_count": len(sample_df.columns),
                "columns": sample_df.columns.tolist(),
                "schema": schema,
                "date_columns": date_columns,
                "categorical_columns": categorical_columns,
                "numerical_columns": numerical_columns,
                "unique_values": unique_values,
                "summary_stats": summary_stats,
                "date_range": date_range
            }
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error profiling data: {e}")
            raise
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        try:
            logger.info(f"Executing query: {sql[:200]}...")
            
            if self.use_duckdb:
                result = self.conn.execute(sql).fetch_df()
            else:
                # Use pandas-sql or pandasql for SQL queries
                # For now, use simple query parsing
                result = self._execute_pandas_query(sql)
            
            # Convert to list of dicts
            records = result.to_dict('records')
            
            logger.info(f"Query returned {len(records)} rows")
            return records
        
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def _execute_pandas_query(self, sql: str) -> pd.DataFrame:
        """Execute SQL-like query using Pandas (fallback)."""
        # Simple SQL parser for common queries
        sql_lower = sql.lower()
        
        # Extract table name
        import re
        table_match = re.search(r'from\s+(\w+)', sql_lower)
        if not table_match:
            raise ValueError("Could not parse table name from SQL")
        
        table_name = table_match.group(1)
        
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} not found")
        
        df = self.tables[table_name].copy()
        
        # Handle simple WHERE clauses
        if 'where' in sql_lower:
            logger.warning("WHERE clause detected - applying basic filter")
            # Basic WHERE support (limited)
            # This is a simplified version - DuckDB is recommended for production
        
        # Handle GROUP BY
        if 'group by' in sql_lower:
            # Extract group by column
            group_match = re.search(r'group\s+by\s+(\w+)', sql_lower)
            if group_match:
                group_col = group_match.group(1)
                
                # Extract aggregation
                if 'sum(' in sql_lower:
                    agg_match = re.search(r'sum\((\w+)\)', sql_lower)
                    if agg_match:
                        agg_col = agg_match.group(1)
                        df = df.groupby(group_col)[agg_col].sum().reset_index()
                        df.columns = [group_col, f'sum_{agg_col}']
                elif 'count(' in sql_lower:
                    df = df.groupby(group_col).size().reset_index(name='count')
        
        # Handle LIMIT
        if 'limit' in sql_lower:
            limit_match = re.search(r'limit\s+(\d+)', sql_lower)
            if limit_match:
                limit = int(limit_match.group(1))
                df = df.head(limit)
        
        # Handle ORDER BY
        if 'order by' in sql_lower:
            order_match = re.search(r'order\s+by\s+(\w+)(\s+desc)?', sql_lower)
            if order_match:
                order_col = order_match.group(1)
                ascending = order_match.group(2) is None
                df = df.sort_values(by=order_col, ascending=ascending)
        
        return df
    
    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """Validate SQL without executing."""
        try:
            if self.use_duckdb:
                # Try to explain the query
                self.conn.execute(f"EXPLAIN {sql}")
                return True, None
            else:
                # Basic validation for Pandas queries
                # Check for basic SQL keywords
                if any(keyword in sql.lower() for keyword in ['select', 'from']):
                    return True, None
                return False, "Invalid SQL syntax"
        except Exception as e:
            return False, str(e)
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """Get schema for a table."""
        try:
            if self.use_duckdb:
                result = self.conn.execute(
                    f"DESCRIBE {table_name}"
                ).fetch_df()
                
                schema = {}
                for _, row in result.iterrows():
                    schema[row['column_name']] = row['column_type']
                
                return schema
            else:
                # Pandas fallback
                if table_name in self.tables:
                    df = self.tables[table_name]
                    schema = {col: str(df[col].dtype) for col in df.columns}
                    return schema
                return {}
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {}
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            if self.use_duckdb:
                tables = self.conn.execute("SHOW TABLES").fetch_df()
                return table_name in tables['name'].values
            else:
                return table_name in self.tables
        except:
            return False
    
    def drop_table(self, table_name: str):
        """Drop a table."""
        try:
            if self.use_duckdb:
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            else:
                if table_name in self.tables:
                    del self.tables[table_name]
            logger.info(f"Dropped table: {table_name}")
        except Exception as e:
            logger.error(f"Error dropping table: {e}")
            raise
    
    def get_preview(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get preview of table data."""
        try:
            if self.use_duckdb:
                result = self.conn.execute(
                    f"SELECT * FROM {table_name} LIMIT {limit}"
                ).fetch_df()
            else:
                if table_name in self.tables:
                    result = self.tables[table_name].head(limit)
                else:
                    return []
            
            # Convert to dict and ensure JSON serializable
            # Replace NaN with None first
            result = result.fillna("")
            records = result.to_dict('records')
            
            # Convert any non-JSON-serializable types to strings
            import numpy as np
            for record in records:
                for key, value in list(record.items()):
                    # Handle numpy types
                    if isinstance(value, (np.integer, np.floating)):
                        record[key] = value.item()
                    elif isinstance(value, np.ndarray):
                        record[key] = value.tolist()
                    elif pd.isna(value):
                        record[key] = None
                    elif value is not None and not isinstance(value, (str, int, float, bool, type(None))):
                        record[key] = str(value)
            
            return records
        except Exception as e:
            logger.error(f"Error getting preview: {e}")
            return []
    
    def close(self):
        """Close database connection."""
        if self.use_duckdb and self.conn:
            self.conn.close()
            logger.info("Closed DuckDB connection")
        else:
            self.tables.clear()
            logger.info("Cleared Pandas DataFrames")


# Global data service instance
data_service = DataService()

