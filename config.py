"""Configuration management for the healthcare analytics application."""
import os
import json
import tempfile
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""

    # GCP Configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

    # Handle credentials - can come from file path, JSON string, or base64-encoded JSON
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    _CREDENTIALS_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    _CREDENTIALS_JSON_BASE64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON_BASE64")

    @classmethod
    def setup_credentials(cls):
        """Set up Google Cloud credentials from environment variables."""
        # Try base64-encoded credentials first (from Cloud Run deployment)
        if cls._CREDENTIALS_JSON_BASE64 and not cls.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                # Decode base64 to get JSON string
                decoded_json = base64.b64decode(cls._CREDENTIALS_JSON_BASE64).decode('utf-8')
                # Write JSON to a temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(decoded_json)
                    cls.GOOGLE_APPLICATION_CREDENTIALS = f.name
                    # Set the environment variable for Google Cloud SDK
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
            except Exception as e:
                print(f"Error decoding base64 credentials: {e}")
        # If we have JSON credentials as a string but no file path, create a temp file
        elif cls._CREDENTIALS_JSON and not cls.GOOGLE_APPLICATION_CREDENTIALS:
            # Write JSON to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(cls._CREDENTIALS_JSON)
                cls.GOOGLE_APPLICATION_CREDENTIALS = f.name
                # Set the environment variable for Google Cloud SDK
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
        elif cls.GOOGLE_APPLICATION_CREDENTIALS:
            # Ensure the environment variable is set for Google Cloud SDK
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cls.GOOGLE_APPLICATION_CREDENTIALS
    
    # BigQuery Configuration
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "bigquery-public-data.fhir_synthea")
    
    # Vertex AI Configuration
    VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-1.5-flash")
    REGION = os.getenv("REGION", "us-central1")
    
    # Application Configuration
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8501"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        return True