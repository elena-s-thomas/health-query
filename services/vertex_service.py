"""Vertex AI service for natural language to SQL translation."""
import vertexai
from vertexai.language_models import TextGenerationModel
import logging
from typing import Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)

class VertexAIService:
    """Service for interacting with Vertex AI."""
    
    def __init__(self):
        """Initialize Vertex AI."""
        try:
            vertexai.init(project=Config.GCP_PROJECT_ID, location=Config.REGION)
            self.model = TextGenerationModel.from_pretrained(Config.VERTEX_MODEL)
            logger.info(f"Vertex AI initialized with model: {Config.VERTEX_MODEL}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise
    
    def generate_sql_from_natural_language(
        self, 
        natural_language_query: str,
        table_schemas: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate SQL query from natural language input."""
        try:
            # Create prompt for SQL generation
            prompt = self._create_sql_generation_prompt(natural_language_query, table_schemas)
            
            logger.info(f"Generating SQL for query: {natural_language_query}")
            
            # Generate response
            response = self.model.predict(
                prompt,
                max_output_tokens=1024,
                temperature=0.1,  # Low temperature for more consistent SQL
                top_p=0.8,
                top_k=40
            )
            
            # Parse the response
            sql_query = self._extract_sql_from_response(response.text)
            
            logger.info(f"Generated SQL: {sql_query}")
            
            return {
                "sql_query": sql_query,
                "raw_response": response.text,
                "model_used": Config.VERTEX_MODEL
            }
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise
    
    def generate_summary_from_data(
        self, 
        query: str, 
        data: list, 
        sql_query: str
    ) -> str:
        """Generate a natural language summary of query results."""
        try:
            # Create prompt for data summarization
            prompt = self._create_summary_prompt(query, data, sql_query)
            
            logger.info("Generating data summary")
            
            # Generate response
            response = self.model.predict(
                prompt,
                max_output_tokens=512,
                temperature=0.3,
                top_p=0.8,
                top_k=40
            )
            
            summary = response.text.strip()
            logger.info("Data summary generated successfully")
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Unable to generate summary at this time."
    
    def _create_sql_generation_prompt(self, query: str, table_schemas: Optional[Dict[str, Any]] = None) -> str:
        """Create a prompt for SQL generation."""
        base_prompt = f"""
You are a healthcare data analyst expert. Convert the following natural language question into a BigQuery SQL query.

Available dataset: {Config.BIGQUERY_DATASET}

Key tables and their purposes:
- patient: Patient demographics and basic information
- observation: Clinical observations and measurements
- condition: Medical conditions and diagnoses
- procedure: Medical procedures performed
- medication: Medications prescribed
- encounter: Healthcare encounters/visits
- organization: Healthcare organizations
- practitioner: Healthcare providers

Guidelines:
1. Use proper BigQuery SQL syntax
2. Always include LIMIT clause (default 1000 if not specified)
3. Use appropriate JOINs when needed
4. Handle date filtering properly
5. Use descriptive column aliases
6. Return only the SQL query, no explanations

Natural language question: {query}

SQL Query:
"""
        
        if table_schemas:
            schema_info = "\n\nTable schemas:\n"
            for table, schema in table_schemas.items():
                schema_info += f"\n{table}:\n"
                for field in schema:
                    schema_info += f"  - {field['name']} ({field['type']}): {field.get('description', 'No description')}\n"
            
            base_prompt += schema_info
        
        return base_prompt
    
    def _create_summary_prompt(self, original_query: str, data: list, sql_query: str) -> str:
        """Create a prompt for data summarization."""
        # Sample a few rows for context (avoid token limits)
        sample_data = data[:5] if len(data) > 5 else data
        
        prompt = f"""
You are a healthcare data analyst. Provide a clear, concise summary of the query results.

Original question: {original_query}
SQL query used: {sql_query}
Number of results: {len(data)}

Sample data:
{sample_data}

Provide a 2-3 sentence summary that:
1. Answers the original question
2. Highlights key findings or patterns
3. Uses healthcare terminology appropriately

Summary:
"""
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from model response."""
        # Look for SQL between ```sql and ``` or just the SQL query
        lines = response.strip().split('\n')
        
        # Remove markdown formatting if present
        sql_lines = []
        in_sql_block = False
        
        for line in lines:
            if line.strip().startswith('```sql'):
                in_sql_block = True
                continue
            elif line.strip().startswith('```') and in_sql_block:
                break
            elif in_sql_block or (not line.strip().startswith('```') and not line.strip().startswith('SQL')):
                sql_lines.append(line)
        
        sql_query = '\n'.join(sql_lines).strip()
        
        # Ensure it ends with semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query