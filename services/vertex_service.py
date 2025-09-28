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

Key tables and their purposes (use EXACT table names as shown):
- patient: Patient demographics and basic information
- observation: Clinical observations and measurements
- condition: Medical conditions and diagnoses
- procedure: Medical procedures performed
- medication_request: Medications prescribed
- encounter: Healthcare encounters/visits
- organization: Healthcare organizations
- practitioner: Healthcare providers

CRITICAL TABLE NAME REQUIREMENTS:
- Use EXACT table names: patient, observation, condition, procedure, medication_request, encounter, organization, practitioner
- Do NOT use PascalCase like Patient, Observation, Condition, Procedure, MedicationRequest, Encounter, Organization, Practitioner
- Do NOT use camelCase like patient, observation, condition, procedure, medicationRequest, encounter, organization, practitioner
- Always use lowercase with underscores: medication_request (NOT MedicationRequest)

CRITICAL FIELD NAME REQUIREMENTS:
- medication_request table: Use medication.codeableConcept (NOT medicationCodeableConcept)
- condition table: Use clinicalStatus (NOT status), use code (for condition codes)
- For medication names: Use medication.codeableConcept.text or medication.codeableConcept.coding[0].display
- For condition names: Use code.text or code.coding[0].display
- For patient demographics: Use gender, birthDate, etc. (direct fields)
- For dates: Use authoredOn, assertedDate, etc. (direct fields)

CRITICAL STRUCT FIELD WARNINGS:
- NEVER assume STRUCT fields have an 'id' field unless explicitly confirmed
- Common STRUCT fields: medication.codeableConcept, code.coding, identifier
- When accessing nested STRUCT fields, use dot notation: struct_field.nested_field
- If you need to reference a record identifier, use the top-level 'id' field, not nested STRUCT.id
- Always use the exact field names as they appear in the schema

IMPORTANT DATA TYPE NOTES:
- Date fields in this FHIR dataset are stored as STRING type, not DATE type
- When using EXTRACT() function on date fields, you MUST first convert them to DATE using PARSE_DATE()
- Common date fields: birthDate (patient table), assertedDate (condition table)
- For EXTRACT operations, use: EXTRACT(YEAR FROM PARSE_DATE('%Y-%m-%d', date_field))
- For date comparisons, use: PARSE_DATE('%Y-%m-%d', date_field) >= DATE('2020-01-01')

Guidelines:
1. Use proper BigQuery SQL syntax
2. Always include a LIMIT clause (use LIMIT 1000 if not specified in the question)
3. Use appropriate JOINs when needed
4. Handle date filtering properly - convert STRING dates to DATE using PARSE_DATE()
5. Use descriptive column aliases
6. Return ONLY the SQL query itself, no explanations or additional text
7. Do not include markdown formatting or code blocks
8. Ensure there is only ONE LIMIT clause in the entire query
9. When extracting date parts (year, month, day), always use PARSE_DATE() first
10. CRITICAL: Use exact table names as specified above (lowercase with underscores)

Natural language question: {query}

SQL Query:
"""
        
        if table_schemas:
            schema_info = "\n\nACTUAL TABLE SCHEMAS (use these exact field names):\n"
            for table, schema in table_schemas.items():
                schema_info += f"\n{table}:\n"
                for field in schema:
                    field_name = field['name']
                    field_type = field['type']
                    field_mode = field.get('mode', 'NULLABLE')
                    description = field.get('description', 'No description')
                    
                    schema_info += f"  - {field_name} ({field_type}, {field_mode}): {description}\n"
                    
                    # Add special notes for STRUCT fields
                    if 'STRUCT' in field_type:
                        schema_info += f"    ⚠️  STRUCT field - do NOT assume it has an 'id' field\n"
                        schema_info += f"    ⚠️  Use dot notation to access nested fields: {field_name}.nested_field\n"
                        
                        # Show nested fields if available
                        if 'nested_fields' in field:
                            schema_info += f"    Available nested fields:\n"
                            for nested_field in field['nested_fields']:
                                nested_name = nested_field['name']
                                nested_type = nested_field['type']
                                schema_info += f"      - {field_name}.{nested_name} ({nested_type})\n"
            
            schema_info += "\nCRITICAL SCHEMA RULES:\n"
            schema_info += "- Use ONLY the field names listed above\n"
            schema_info += "- NEVER reference fields that are not in the schema\n"
            schema_info += "- For STRUCT fields, only use the nested fields that actually exist\n"
            schema_info += "- If you need a record ID, use the top-level 'id' field, not STRUCT.id\n"
            
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

        # Post-process to fix common EXTRACT function issues with STRING dates
        sql_query = self._fix_extract_functions(sql_query)
        
        # Post-process to fix table name casing issues
        sql_query = self._fix_table_name_casing(sql_query)
        
        # Post-process to fix field name issues
        sql_query = self._fix_field_name_issues(sql_query)
        
        # Post-process to fix STRUCT field issues
        sql_query = self._fix_struct_field_issues(sql_query)

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