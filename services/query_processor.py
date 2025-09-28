"""Query processor service that orchestrates the entire query pipeline."""
import logging
import time
from typing import Dict, Any, List, Optional

from services.bigquery_service import BigQueryService
from services.vertex_service import VertexAIService
from services.visualization_service import VisualizationService

logger = logging.getLogger(__name__)

class QueryProcessor:
    """Orchestrates the complete query processing pipeline."""
    
    def __init__(self, bigquery_service: BigQueryService, vertex_service: VertexAIService):
        """Initialize query processor with required services."""
        self.bigquery_service = bigquery_service
        self.vertex_service = vertex_service
        self.visualization_service = VisualizationService()
        logger.info("Query processor initialized")
    
    async def process_query(
        self, 
        natural_language_query: str,
        limit: int = 1000,
        include_visualization: bool = True
    ) -> Dict[str, Any]:
        """Process a natural language query through the complete pipeline."""
        start_time = time.time()
        
        try:
            logger.info(f"Starting query processing for: {natural_language_query}")
            
            # Step 0: Get all table schemas for accurate SQL generation
            logger.info("Step 0: Fetching all table schemas...")
            table_schemas = self._get_all_table_schemas()
            logger.info(f"Retrieved schemas for {len(table_schemas)} tables")
            
            # Step 1: Generate SQL from natural language with schema information
            logger.info("Step 1: Generating SQL from natural language with schema data...")
            sql_generation_result = self.vertex_service.generate_sql_from_natural_language(
                natural_language_query, table_schemas
            )
            sql_query = sql_generation_result["sql_query"]
            logger.info(f"Generated SQL Query:\n{'='*60}\n{sql_query}\n{'='*60}")

            # Step 2: Estimate query cost (for free tier optimization)
            logger.info("Step 2: Estimating query cost...")
            cost_estimate = self.bigquery_service.estimate_query_cost(sql_query)
            
            # Step 3: Execute SQL query
            logger.info(f"Step 3: Executing SQL query with limit={limit}...")
            data = self.bigquery_service.execute_query(sql_query, limit=limit)
            logger.info(f"Query returned {len(data)} rows")
            
            # Step 4: Generate visualization config if requested
            visualization_config = None
            if include_visualization and data:
                visualization_config = self.visualization_service.generate_config(
                    data, natural_language_query
                )
            
            # Step 5: Generate natural language summary
            summary = self.vertex_service.generate_summary_from_data(
                natural_language_query, data, sql_query
            )
            
            execution_time = time.time() - start_time
            
            result = {
                "sql_query": sql_query,
                "data": data,
                "summary": summary,
                "visualization_config": visualization_config,
                "execution_time": execution_time,
                "bytes_scanned": cost_estimate.get("bytes_scanned"),
                "estimated_cost_usd": cost_estimate.get("estimated_cost_usd"),
                "row_count": len(data)
            }
            
            logger.info(f"Query processing completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            logger.error(f"Failed at natural language query: {natural_language_query}")
            if 'sql_query' in locals():
                logger.error(f"Generated SQL that failed:\n{sql_query}")
            raise
    
    def _get_all_table_schemas(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get schema information for all available tables."""
        try:
            # Get all available tables
            all_tables = self.bigquery_service.list_datasets()
            logger.info(f"Available tables: {all_tables}")
            
            # Fetch schemas for all tables
            table_schemas = {}
            for table_name in all_tables:
                try:
                    schema = self.bigquery_service.get_table_schema(table_name)
                    table_schemas[table_name] = schema
                    logger.info(f"Retrieved schema for {table_name}: {len(schema)} fields")
                except Exception as e:
                    logger.warning(f"Failed to get schema for {table_name}: {e}")
            
            return table_schemas
            
        except Exception as e:
            logger.error(f"Failed to get table schemas: {e}")
            return {}