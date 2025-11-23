"""Smart chunking utilities for large datasets."""
import pandas as pd
from typing import Iterator, Dict, Any, List
from pathlib import Path
import hashlib


def generate_file_id(filename: str) -> str:
    """Generate unique file ID."""
    return hashlib.md5(f"{filename}".encode()).hexdigest()[:16]


def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 10000) -> Iterator[pd.DataFrame]:
    """Chunk a DataFrame into smaller pieces."""
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]


def smart_sample(df: pd.DataFrame, sample_size: int = 10000) -> pd.DataFrame:
    """Intelligently sample a DataFrame for profiling."""
    if len(df) <= sample_size:
        return df
    
    # Take samples from beginning, middle, and end
    chunk_size = sample_size // 3
    return pd.concat([
        df.head(chunk_size),
        df.iloc[len(df)//2 - chunk_size//2: len(df)//2 + chunk_size//2],
        df.tail(chunk_size)
    ])


def detect_date_columns(df: pd.DataFrame) -> List[str]:
    """Detect columns that contain dates."""
    import warnings
    date_columns = []
    
    # Keywords that suggest date columns
    date_keywords = ['date', 'time', 'day', 'month', 'year', 'timestamp', 'created', 'updated']
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Check if already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_columns.append(col)
            continue
        
        # Skip if column name suggests it's not a date
        if any(keyword in col_lower for keyword in ['price', 'mrp', 'amount', 'value', 'cost', 'qty', 'quantity']):
            continue
        
        # Try to parse as date only if column name suggests it
        if df[col].dtype == 'object':
            # Check if column name contains date-related keywords
            has_date_keyword = any(keyword in col_lower for keyword in date_keywords)
            
            try:
                sample = df[col].dropna().head(100)
                if len(sample) > 0:
                    # Try to parse (suppress warnings)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        parsed = pd.to_datetime(sample, errors='coerce')
                    
                    # Check if parsing was successful (not all NaT)
                    valid_dates = parsed.notna().sum()
                    total = len(sample)
                    
                    # Only consider as date if:
                    # 1. Column name suggests it's a date, OR
                    # 2. >80% of values successfully parsed as reasonable dates
                    if has_date_keyword or (valid_dates / total > 0.8 and parsed.min().year > 1900 and parsed.max().year < 2100):
                        date_columns.append(col)
            except:
                pass
    
    return date_columns


def detect_categorical_columns(df: pd.DataFrame, threshold: int = 50) -> List[str]:
    """Detect categorical columns."""
    categorical_columns = []
    
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].nunique() < threshold:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                categorical_columns.append(col)
    
    return categorical_columns


def detect_numerical_columns(df: pd.DataFrame) -> List[str]:
    """Detect numerical columns."""
    return df.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()


def extract_unique_values(df: pd.DataFrame, columns: List[str], max_unique: int = 100) -> Dict[str, List[Any]]:
    """Extract unique values for categorical columns."""
    unique_values = {}
    
    for col in columns:
        if col in df.columns:
            uniques = df[col].dropna().unique()
            if len(uniques) <= max_unique:
                unique_values[col] = uniques.tolist()
            else:
                # Take most frequent values
                unique_values[col] = df[col].value_counts().head(max_unique).index.tolist()
    
    return unique_values


def calculate_summary_stats(df: pd.DataFrame, numerical_columns: List[str]) -> Dict[str, Any]:
    """Calculate summary statistics for numerical columns."""
    stats = {}
    
    for col in numerical_columns:
        if col in df.columns:
            stats[col] = {
                'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                'median': float(df[col].median()) if not df[col].isna().all() else None,
                'min': float(df[col].min()) if not df[col].isna().all() else None,
                'max': float(df[col].max()) if not df[col].isna().all() else None,
                'sum': float(df[col].sum()) if not df[col].isna().all() else None,
                'count': int(df[col].count())
            }
    
    return stats


def get_date_range(df: pd.DataFrame, date_columns: List[str]) -> Dict[str, str]:
    """Get date range from date columns."""
    date_range = {}
    
    for col in date_columns:
        if col in df.columns:
            try:
                dates = pd.to_datetime(df[col], errors='coerce')
                date_range[col] = {
                    'start': dates.min().isoformat() if not dates.isna().all() else None,
                    'end': dates.max().isoformat() if not dates.isna().all() else None
                }
            except:
                pass
    
    return date_range


def create_table_name(file_id: str) -> str:
    """Create a valid DuckDB table name from file ID."""
    return f"data_{file_id}"


def infer_schema(df: pd.DataFrame) -> Dict[str, str]:
    """Infer schema from DataFrame."""
    schema = {}
    
    for col in df.columns:
        dtype = df[col].dtype
        
        if pd.api.types.is_datetime64_any_dtype(dtype):
            schema[col] = 'TIMESTAMP'
        elif pd.api.types.is_integer_dtype(dtype):
            schema[col] = 'BIGINT'
        elif pd.api.types.is_float_dtype(dtype):
            schema[col] = 'DOUBLE'
        elif pd.api.types.is_bool_dtype(dtype):
            schema[col] = 'BOOLEAN'
        else:
            schema[col] = 'VARCHAR'
    
    return schema

