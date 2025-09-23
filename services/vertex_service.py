"""Vertex AI service for natural language to SQL translation."""
import vertexai
from vertexai.generative_models import GenerativeModel
import logging
from typing import Dict, Any, Optional

from config import Config

logger = logging.getLogger(__name__)

class VertexAIService:
    """Service for interacting with Vertex AI."""
    
    def __init__(self):
        """Initialize Vertex AI."""
        try:
            # Validate configuration
            if not Config.GCP_PROJECT_ID:
                raise ValueError("GCP_PROJECT_ID is required for Vertex AI initialization")
            
            # Initialize Vertex AI
            vertexai.init(project=Config.GCP_PROJECT_ID, location=Config.REGION)
            
            # Initialize the model
            self.model = GenerativeModel(Config.VERTEX_MODEL)
            logger.info(f"Vertex AI initialized successfully with model: {Config.VERTEX_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            logger.error(f"Project ID: {Config.GCP_PROJECT_ID}, Region: {Config.REGION}, Model: {Config.VERTEX_MODEL}")
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 1024,
                    "temperature": 0.1,  # Low temperature for more consistent SQL
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            # Parse the response
            logger.info(f"Raw model response:\n{response.text}")
            sql_query = self._extract_sql_from_response(response.text)

            logger.info(f"Extracted SQL query:\n{sql_query}")
            
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
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 512,
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40
                }
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
2. Always include a LIMIT clause (use LIMIT 1000 if not specified in the question)
3. Use appropriate JOINs when needed
4. Handle date filtering properly
5. Use descriptive column aliases
6. Return ONLY the SQL query itself, no explanations or additional text
7. Do not include markdown formatting or code blocks
8. Ensure there is only ONE LIMIT clause in the entire query

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
        # Clean up the response
        response = response.strip()

        # Check if the response contains code blocks
        if '```sql' in response.lower():
            # Extract content between ```sql and ```
            import re
            pattern = r'```sql\s*([\s\S]*?)```'
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                sql_query = matches[0].strip()
            else:
                # Fallback: try to find content between any ``` markers
                pattern = r'```([\s\S]*?)```'
                matches = re.findall(pattern, response)
                if matches:
                    sql_query = matches[0].strip()
                else:
                    sql_query = response
        elif '```' in response:
            # Extract content between ``` markers
            import re
            pattern = r'```([\s\S]*?)```'
            matches = re.findall(pattern, response)
            if matches:
                sql_query = matches[0].strip()
            else:
                sql_query = response
        else:
            # No code blocks, use the entire response
            sql_query = response

        # Remove any leading/trailing whitespace and common prefixes
        sql_query = sql_query.strip()

        # Remove common prefixes like "SQL Query:", "Query:", etc.
        import re
        sql_query = re.sub(r'^(SQL\s*Query:|Query:|SQL:)\s*', '', sql_query, flags=re.IGNORECASE)

        # Ensure it doesn't have duplicate semicolons
        sql_query = sql_query.rstrip(';').strip()

        # Add a single semicolon at the end if not present
        if not sql_query.endswith(';'):
            sql_query += ';'

        return sql_query