"""Vertex AI service for natural language to SQL translation."""
import vertexai
from vertexai.generative_models import GenerativeModel
import logging
from typing import Dict, Any, Optional
import os

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

            # Load compact schema if available
            self.schema_context = self._load_compact_schema()

        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            logger.error(f"Project ID: {Config.GCP_PROJECT_ID}, Region: {Config.REGION}, Model: {Config.VERTEX_MODEL}")
            raise

    def _load_compact_schema(self) -> str:
        """Load the compact schema context from file."""
        schema_file = 'dataset_schema_compact.md'
        try:
            with open(schema_file, 'r') as f:
                schema_content = f.read()
            logger.info(f"Loaded compact schema from {schema_file}")
            return schema_content
        except FileNotFoundError:
            error_msg = f"Required schema file {schema_file} not found. Run 'python get_database_schema.py' to generate it."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"Failed to load compact schema: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def generate_sql_from_natural_language(
        self,
        natural_language_query: str
    ) -> Dict[str, Any]:
        """Generate SQL query from natural language input."""
        try:
            # Create prompt for SQL generation
            prompt = self._create_sql_generation_prompt(natural_language_query)
            
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
    
    def _create_sql_generation_prompt(self, query: str) -> str:
        """Create a prompt for SQL generation using compact schema."""

        # Build prompt with compact schema
        prompt = f"""
You are a healthcare data analyst expert. Convert the following natural language question into a BigQuery SQL query.

Available dataset: {Config.BIGQUERY_DATASET}

{'=' * 60}
DATABASE SCHEMA REFERENCE:
{'=' * 60}

{self.schema_context}

{'=' * 60}
CRITICAL SQL GENERATION RULES:
{'=' * 60}

1. TABLE NAMES - Use exact lowercase with underscores:
   ✓ patient, observation, condition, procedure, medication_request, encounter
   ✗ Patient, Observation, Condition, MedicationRequest (WRONG)

2. COMMON FIELDS (present in all tables):
   - id, meta, identifier[], implicitRules, language, text

3. DATE HANDLING - All dates are STRING type:
   - Convert to DATE: PARSE_DATE('%Y-%m-%d', date_field)
   - Extract parts: EXTRACT(YEAR FROM PARSE_DATE('%Y-%m-%d', birthDate))
   - Compare: PARSE_DATE('%Y-%m-%d', date_field) >= DATE('2020-01-01')

4. REFERENCE FIELDS - Use proper navigation:
   - Reference<Patient>: Use subject.reference or subject.patientId
   - Reference<Encounter>: Use encounter.reference or encounter.encounterId
   - Reference<Practitioner>: Use practitioner.reference or practitioner.practitionerId

5. CODEABLE CONCEPTS - Standard structure:
   - code.text for display text
   - code.coding[0].display for first coding display
   - code.coding[0].code for actual code
   - medication_request: Use medication.codeableConcept (NOT medicationCodeableConcept)

6. SPECIFIC FIELD NOTES:
   - condition: Use clinicalStatus (NOT status)
   - Do NOT assume STRUCT fields have an 'id' field
   - Use top-level 'id' field for record identifiers

7. QUERY REQUIREMENTS:
   - Always include LIMIT clause (default 1000)
   - Use fully qualified table names: `{Config.BIGQUERY_DATASET}.table_name`
   - Return ONLY the SQL query, no explanations
   - No markdown formatting or code blocks
   - Single LIMIT clause only

8. DUPLICATE PREVENTION:
   - For "what are the codes..." queries, use DISTINCT to avoid duplicates
   - For "list all..." queries, use DISTINCT unless you specifically need counts
   - For "how many..." queries, use COUNT(DISTINCT patient_id) to count unique patients
   - Examples:
     * "What are the codes for broken bones?" → SELECT DISTINCT code.coding[0].code FROM condition WHERE...
     * "List all medication names" → SELECT DISTINCT medication.codeableConcept.text FROM medication_request WHERE...
     * "How many hip fractures?" → SELECT COUNT(DISTINCT id) FROM condition WHERE...

Natural language question: {query}

SQL Query:
"""

        return prompt
    
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

        # Post-process to fix common EXTRACT function issues with STRING dates
        sql_query = self._fix_extract_functions(sql_query)
        
        # Post-process to fix table name casing issues
        sql_query = self._fix_table_name_casing(sql_query)
        
        # Post-process to fix field name issues
        sql_query = self._fix_field_name_issues(sql_query)
        
        # Post-process to fix STRUCT field issues
        sql_query = self._fix_struct_field_issues(sql_query)
        
        # Post-process to add DISTINCT for code/name queries
        sql_query = self._fix_duplicate_issues(sql_query)

        return sql_query
    
    def _fix_extract_functions(self, sql_query: str) -> str:
        """Fix EXTRACT functions to handle STRING date fields properly."""
        import re
        
        # Common date fields that are STRINGs in the FHIR dataset
        string_date_fields = [
            'birthDate', 'assertedDate', 'effectiveDateTime', 'issued', 
            'start', 'end', 'date', 'onsetDateTime', 'abatementDateTime'
        ]
        
        # Pattern to match EXTRACT functions with STRING date fields
        # This will match: EXTRACT(YEAR FROM birthDate) -> EXTRACT(YEAR FROM PARSE_DATE('%Y-%m-%d', birthDate))
        for field in string_date_fields:
            # Match EXTRACT with the field name
            pattern = rf'EXTRACT\s*\(\s*([^,]+)\s+FROM\s+{field}\s*\)'
            replacement = rf'EXTRACT(\1 FROM PARSE_DATE(\'%Y-%m-%d\', {field}))'
            sql_query = re.sub(pattern, replacement, sql_query, flags=re.IGNORECASE)
        
        return sql_query
    
    def _fix_table_name_casing(self, sql_query: str) -> str:
        """Fix table name casing to use correct lowercase with underscores format."""
        import re
        
        # Define the correct table name mappings
        table_name_mappings = {
            # PascalCase to correct format
            'Patient': 'patient',
            'Observation': 'observation', 
            'Condition': 'condition',
            'Procedure': 'procedure',
            'MedicationRequest': 'medication_request',
            'Encounter': 'encounter',
            'Organization': 'organization',
            'Practitioner': 'practitioner',
            
            # camelCase to correct format
            'medicationRequest': 'medication_request',
        }
        
        # Fix table names in FROM clauses
        for incorrect_name, correct_name in table_name_mappings.items():
            # Pattern to match table names in FROM clauses with backticks
            # This handles cases like: FROM `bigquery-public-data.fhir_synthea.MedicationRequest`
            pattern = rf'`([^`]*\.){re.escape(incorrect_name)}`'
            replacement = rf'`\1{correct_name}`'
            sql_query = re.sub(pattern, replacement, sql_query)
            
            # Pattern to match table names without backticks
            # This handles cases like: FROM bigquery-public-data.fhir_synthea.MedicationRequest
            pattern = rf'([^`\s]*\.){re.escape(incorrect_name)}(?=\s|$|,|;)'
            replacement = rf'\1{correct_name}'
            sql_query = re.sub(pattern, replacement, sql_query)
        
        return sql_query
    
    def _fix_field_name_issues(self, sql_query: str) -> str:
        """Fix common field name issues in FHIR queries."""
        import re
        
        # Define field name mappings for common issues
        field_mappings = {
            # medication_request table field fixes
            'medicationCodeableConcept': 'medication.codeableConcept',
            'medicationCodeableConcept.text': 'medication.codeableConcept.text',
            'medicationCodeableConcept.coding': 'medication.codeableConcept.coding',
            'medicationCodeableConcept.coding[0].display': 'medication.codeableConcept.coding[0].display',
            'medicationCodeableConcept.coding[0].code': 'medication.codeableConcept.coding[0].code',
            
            # condition table field fixes
            'status': 'clinicalStatus',  # in condition table context
            'conditionStatus': 'clinicalStatus',
            'conditionCode': 'code',
            'conditionCode.text': 'code.text',
            'conditionCode.coding': 'code.coding',
            'conditionCode.coding[0].display': 'code.coding[0].display',
            'conditionCode.coding[0].code': 'code.coding[0].code',
            
            # patient table field fixes (these are usually correct, but just in case)
            'patientGender': 'gender',
            'patientBirthDate': 'birthDate',
            'patientId': 'id',
        }
        
        # Fix field names in SELECT, WHERE, and other clauses
        for incorrect_field, correct_field in field_mappings.items():
            # Pattern to match field names in various contexts
            # This handles cases like: SELECT medicationCodeableConcept FROM ...
            pattern = rf'\b{re.escape(incorrect_field)}\b'
            sql_query = re.sub(pattern, correct_field, sql_query)
        
        return sql_query
    
    def _fix_struct_field_issues(self, sql_query: str) -> str:
        """Fix common STRUCT field issues that cause BigQuery errors."""
        import re
        
        # Common problematic patterns where AI assumes STRUCT fields have 'id'
        struct_field_fixes = {
            # Fix cases where AI tries to access .id on STRUCT fields that don't have it
            r'medication\.codeableConcept\.id': 'medication.codeableConcept',  # Remove .id
            r'code\.coding\[0\]\.id': 'code.coding[0]',  # Remove .id
            r'identifier\.id': 'identifier',  # Remove .id
            r'coding\[0\]\.id': 'coding[0]',  # Remove .id
            
            # Fix subject field issues - subject is a STRUCT that references patient
            r'condition\.subject\.id': 'condition.id',  # Use top-level id instead
            r'subject\.id': 'id',  # Use top-level id instead
            
            # Fix cases where AI tries to access non-existent nested fields
            r'medication\.codeableConcept\.identifier': 'medication.codeableConcept',
            r'code\.coding\[0\]\.identifier': 'code.coding[0]',
        }
        
        # Apply fixes
        for pattern, replacement in struct_field_fixes.items():
            sql_query = re.sub(pattern, replacement, sql_query)
        
        # Additional fix: If the query is trying to select or reference STRUCT.id,
        # replace with the top-level id field
        # This handles cases like: SELECT medication.codeableConcept.id FROM medication_request
        # Should become: SELECT id FROM medication_request
        
        # Pattern to match SELECT statements with STRUCT.id references
        select_pattern = r'SELECT\s+([^,]*\.id[^,]*)'
        def replace_struct_id(match):
            # If it's a STRUCT.id reference, replace with just 'id'
            field_ref = match.group(1).strip()
            if '.' in field_ref and field_ref.endswith('.id'):
                return 'SELECT id'
            return match.group(0)
        
        sql_query = re.sub(select_pattern, replace_struct_id, sql_query, flags=re.IGNORECASE)
        
        return sql_query
    
    def _fix_duplicate_issues(self, sql_query: str) -> str:
        """Fix duplicate issues by adding DISTINCT when appropriate."""
        import re
        
        sql_upper = sql_query.upper()
        
        # Check if this is a query that should return unique values
        should_add_distinct = False
        
        # Patterns that suggest we want unique values
        unique_value_patterns = [
            r'SELECT\s+.*code.*FROM',  # Queries selecting codes
            r'SELECT\s+.*name.*FROM',  # Queries selecting names
            r'SELECT\s+.*\.coding\[',  # Queries selecting coding arrays
            r'SELECT\s+.*\.text.*FROM',  # Queries selecting text fields
        ]
        
        # Check if SQL suggests unique values
        for pattern in unique_value_patterns:
            if re.search(pattern, sql_query, re.IGNORECASE):
                should_add_distinct = True
                break
        
        # Check if SQL is already using DISTINCT
        if 'DISTINCT' in sql_upper:
            should_add_distinct = False
        
        # Check if SQL is using GROUP BY (which implies uniqueness)
        if 'GROUP BY' in sql_upper:
            should_add_distinct = False
        
        # Check if SQL is using aggregate functions (COUNT, SUM, etc.)
        aggregate_patterns = [r'\bCOUNT\b', r'\bSUM\b', r'\bAVG\b', r'\bMIN\b', r'\bMAX\b']
        has_aggregate = False
        for pattern in aggregate_patterns:
            if re.search(pattern, sql_upper):
                has_aggregate = True
                break
        
        # Special handling for COUNT queries - convert COUNT(*) to COUNT(DISTINCT id)
        if has_aggregate and 'COUNT' in sql_upper:
            # Check if it's COUNT(*) without DISTINCT
            if re.search(r'COUNT\s*\(\s*\*\s*\)', sql_upper) and 'DISTINCT' not in sql_upper:
                # Convert COUNT(*) to COUNT(DISTINCT id) for better patient counting
                sql_query = re.sub(r'COUNT\s*\(\s*\*\s*\)', 'COUNT(DISTINCT id)', sql_query, flags=re.IGNORECASE)
                logger.info("Converted COUNT(*) to COUNT(DISTINCT id) for unique patient counting")
                return sql_query
        
        if has_aggregate:
            should_add_distinct = False
        
        # Add DISTINCT if appropriate
        if should_add_distinct:
            # Pattern to match SELECT statements
            select_pattern = r'SELECT\s+'
            if re.search(select_pattern, sql_query, re.IGNORECASE):
                sql_query = re.sub(select_pattern, 'SELECT DISTINCT ', sql_query, flags=re.IGNORECASE)
                logger.info("Added DISTINCT to prevent duplicates")
        
        return sql_query