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
            
            # Step 1: Generate SQL from natural language
            sql_generation_result = self.vertex_service.generate_sql_from_natural_language(
                natural_language_query
            )
            sql_query = sql_generation_result["sql_query"]
            
            # Step 2: Estimate query cost (for free tier optimization)
            cost_estimate = self.bigquery_service.estimate_query_cost(sql_query)
            
            # Step 3: Execute SQL query
            data = self.bigquery_service.execute_query(sql_query, limit=limit)
            
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
            raise