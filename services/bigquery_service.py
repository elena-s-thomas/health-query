"""BigQuery service for healthcare data queries."""
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import logging
from typing import List, Dict, Any, Optional
import time

from config import Config

logger = logging.getLogger(__name__)

class BigQueryService:
    """Service for interacting with BigQuery."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        try:
            self.client = bigquery.Client(project=Config.GCP_PROJECT_ID)
            self.dataset_id = Config.BIGQUERY_DATASET
            logger.info(f"BigQuery client initialized for project: {Config.GCP_PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
    
    def execute_query(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        try:
            start_time = time.time()
            
            # Add limit if specified
            if limit:
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            logger.info(f"Executing query: {query}")
            
            # Execute query
            query_job = self.client.query(query)
            results = query_job.result()
            
            # Convert to list of dictionaries
            data = []
            for row in results:
                data.append(dict(row))
            
            execution_time = time.time() - start_time
            bytes_scanned = query_job.total_bytes_processed
            
            logger.info(f"Query executed successfully in {execution_time:.2f}s, scanned {bytes_scanned} bytes")
            
            return data
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def list_datasets(self) -> List[str]:
        """List available datasets in the FHIR Synthea dataset."""
        try:
            # Get list of tables in the dataset
            dataset_ref = self.client.dataset_from_string(self.dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            
            table_names = [table.table_id for table in tables]
            logger.info(f"Found {len(table_names)} tables in dataset")
            
            return table_names
            
        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        try:
            table_ref = self.client.dataset_from_string(self.dataset_id).table(table_name)
            table = self.client.get_table(table_ref)
            
            schema = []
            for field in table.schema:
                schema.append({
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description
                })
            
            return schema
            
        except Exception as e:
            logger.error(f"Failed to get schema for table {table_name}: {e}")
            raise
    
    def estimate_query_cost(self, query: str) -> Dict[str, Any]:
        """Estimate the cost of a query before execution."""
        try:
            # Create a dry run query job
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            query_job = self.client.query(query, job_config=job_config)
            
            # Get the dry run results
            bytes_scanned = query_job.total_bytes_processed
            
            # Estimate cost (BigQuery charges $5 per TB scanned)
            cost_per_tb = 5.0
            estimated_cost = (bytes_scanned / (1024**4)) * cost_per_tb
            
            return {
                "bytes_scanned": bytes_scanned,
                "estimated_cost_usd": estimated_cost,
                "is_dry_run": True
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate query cost: {e}")
            raise