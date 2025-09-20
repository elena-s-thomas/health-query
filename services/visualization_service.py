"""Visualization service for generating chart configurations."""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class VisualizationService:
    """Service for generating visualization configurations."""
    
    def generate_config(self, data: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
        """Generate visualization configuration based on data and query."""
        try:
            if not data:
                return None
            
            df = pd.DataFrame(data)
            
            # Analyze data structure to determine best visualization
            config = self._analyze_data_for_visualization(df, query)
            
            logger.info(f"Generated visualization config: {config['type']}")
            return config
            
        except Exception as e:
            logger.error(f"Visualization config generation failed: {e}")
            return None
    
    def _analyze_data_for_visualization(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Analyze DataFrame to determine appropriate visualization."""
        
        # Check for date/time columns
        date_columns = self._find_date_columns(df)
        
        # Check for numeric columns
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        # Check for categorical columns
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Determine visualization type based on data characteristics
        if date_columns and numeric_columns:
            return self._create_time_series_config(df, date_columns, numeric_columns, query)
        elif len(categorical_columns) > 0 and len(numeric_columns) > 0:
            return self._create_categorical_config(df, categorical_columns, numeric_columns, query)
        elif len(numeric_columns) >= 2:
            return self._create_scatter_config(df, numeric_columns, query)
        else:
            return self._create_table_config(df, query)
    
    def _find_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Find columns that contain date/time data."""
        date_columns = []
        
        for col in df.columns:
            # Check if column name suggests it's a date
            if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated', 'birth']):
                date_columns.append(col)
            # Check if values look like dates
            elif df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].dropna().iloc[0])
                    date_columns.append(col)
                except:
                    continue
        
        return date_columns
    
    def _create_time_series_config(self, df: pd.DataFrame, date_columns: List[str], numeric_columns: List[str], query: str) -> Dict[str, Any]:
        """Create configuration for time series visualization."""
        date_col = date_columns[0]  # Use first date column
        numeric_col = numeric_columns[0]  # Use first numeric column
        
        # Group by date if there are multiple values per date
        if len(df) > len(df[date_col].unique()):
            grouped_data = df.groupby(date_col)[numeric_col].sum().reset_index()
        else:
            grouped_data = df[[date_col, numeric_col]].copy()
        
        return {
            "type": "line",
            "title": f"Trend Analysis: {numeric_col} over Time",
            "x": date_col,
            "y": numeric_col,
            "data": grouped_data.to_dict('records'),
            "x_title": date_col.replace('_', ' ').title(),
            "y_title": numeric_col.replace('_', ' ').title()
        }
    
    def _create_categorical_config(self, df: pd.DataFrame, categorical_columns: List[str], numeric_columns: List[str], query: str) -> Dict[str, Any]:
        """Create configuration for categorical visualization."""
        cat_col = categorical_columns[0]  # Use first categorical column
        numeric_col = numeric_columns[0]  # Use first numeric column
        
        # Group by categorical column
        grouped_data = df.groupby(cat_col)[numeric_col].sum().reset_index()
        
        return {
            "type": "bar",
            "title": f"Distribution: {numeric_col} by {cat_col}",
            "x": cat_col,
            "y": numeric_col,
            "data": grouped_data.to_dict('records'),
            "x_title": cat_col.replace('_', ' ').title(),
            "y_title": numeric_col.replace('_', ' ').title()
        }
    
    def _create_scatter_config(self, df: pd.DataFrame, numeric_columns: List[str], query: str) -> Dict[str, Any]:
        """Create configuration for scatter plot visualization."""
        x_col = numeric_columns[0]
        y_col = numeric_columns[1] if len(numeric_columns) > 1 else numeric_columns[0]
        
        return {
            "type": "scatter",
            "title": f"Correlation: {x_col} vs {y_col}",
            "x": x_col,
            "y": y_col,
            "data": df[[x_col, y_col]].to_dict('records'),
            "x_title": x_col.replace('_', ' ').title(),
            "y_title": y_col.replace('_', ' ').title()
        }
    
    def _create_table_config(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """Create configuration for table visualization."""
        return {
            "type": "table",
            "title": "Query Results",
            "data": df.to_dict('records'),
            "columns": list(df.columns)
        }