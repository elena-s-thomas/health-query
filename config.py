"""Configuration management for the healthcare analytics application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # GCP Configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # BigQuery Configuration
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "bigquery-public-data.fhir_synthea")
    
    # Vertex AI Configuration
    VERTEX_MODEL = os.getenv("VERTEX_MODEL", "text-bison@002")
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