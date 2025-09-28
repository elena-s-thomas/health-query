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

            # Check if query already has a LIMIT clause
            query_upper = query.upper()
            has_limit = 'LIMIT' in query_upper

            # Only add limit if not already present and limit is specified
            if limit and not has_limit:
                query = f"{query.rstrip(';')} LIMIT {limit};"
                logger.info(f"Added LIMIT {limit} to query")
            elif limit and has_limit:
                logger.warning(f"Query already contains LIMIT clause, not adding additional LIMIT {limit}")

            logger.info(f"Executing BigQuery:\n{query}")
            
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
            logger.error(f"Failed query:\n{query}")
            # Add more specific error information for STRUCT field issues
            if "Field name" in str(e) and "does not exist in STRUCT" in str(e):
                logger.error("This appears to be a STRUCT field reference issue. Check if the query is trying to access non-existent nested fields.")
            raise
    
    def list_datasets(self) -> List[str]:
        """List available tables in the FHIR Synthea dataset."""
        try:
            # The dataset_id is in format "project.dataset" for public datasets
            # For bigquery-public-data.fhir_synthea, we need to handle it specially
            parts = self.dataset_id.split('.')

            if len(parts) == 2:
                # Format: project.dataset
                project_id = parts[0]
                dataset_id = parts[1]
            elif len(parts) == 1:
                # Format: just dataset name
                project_id = self.client.project
                dataset_id = parts[0]
            else:
                # Might be a fully qualified name like bigquery-public-data.fhir_synthea
                # Treat everything before last dot as project
                project_id = '.'.join(parts[:-1]) if len(parts) > 1 else self.client.project
                dataset_id = parts[-1]

            # For public datasets, we need to use the full project name
            if 'bigquery-public-data' in self.dataset_id:
                project_id = 'bigquery-public-data'
                dataset_id = 'fhir_synthea'

            logger.info(f"Listing tables from project: {project_id}, dataset: {dataset_id}")

            # Get dataset reference
            dataset_ref = self.client.dataset(dataset_id, project=project_id)

            # List tables in the dataset
            tables = list(self.client.list_tables(dataset_ref))

            table_names = [table.table_id for table in tables]
            logger.info(f"Found {len(table_names)} tables in dataset {self.dataset_id}")

            return table_names

        except Exception as e:
            logger.error(f"Failed to list datasets: {e}")
            logger.error(f"Dataset ID: {self.dataset_id}")
            raise
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        try:
            # For public datasets, handle the special formatting
            if 'bigquery-public-data' in self.dataset_id:
                project_id = 'bigquery-public-data'
                dataset_id = 'fhir_synthea'
            else:
                parts = self.dataset_id.split('.')
                if len(parts) == 2:
                    project_id = parts[0]
                    dataset_id = parts[1]
                else:
                    project_id = self.client.project
                    dataset_id = self.dataset_id

            # Get table reference
            dataset_ref = self.client.dataset(dataset_id, project=project_id)
            table_ref = dataset_ref.table(table_name)
            table = self.client.get_table(table_ref)

            schema = []
            for field in table.schema:
                field_info = {
                    "name": field.name,
                    "type": field.field_type,
                    "mode": field.mode,
                    "description": field.description
                }
                
                # Add nested field information for STRUCT fields
                if field.field_type == 'STRUCT' and hasattr(field, 'fields'):
                    field_info["nested_fields"] = []
                    for nested_field in field.fields:
                        field_info["nested_fields"].append({
                            "name": nested_field.name,
                            "type": nested_field.field_type,
                            "mode": nested_field.mode,
                            "description": nested_field.description
                        })
                
                schema.append(field_info)

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