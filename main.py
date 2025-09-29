"""FastAPI backend for healthcare analytics application."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from config import Config
from services.bigquery_service import BigQueryService
from services.vertex_service import VertexAIService
from services.query_processor import QueryProcessor

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Healthcare Analytics AI",
    description="AI-powered data explorer for synthetic healthcare data",
    version="1.0.0"
)

# Add CORS middleware
import os

# Configure CORS for production
allowed_origins = [
    "http://localhost:8501",
    "http://localhost:3000",
    "https://*.run.app",  # Allow all Cloud Run URLs
]

# Add frontend URL from environment if available
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

# In development, allow all origins
if os.getenv("ENVIRONMENT", "development") == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services with better error handling
bigquery_service = None
vertex_service = None
query_processor = None

def initialize_services():
    """Initialize services with proper error handling."""
    global bigquery_service, vertex_service, query_processor

    try:
        logger.info("Starting service initialization...")
        Config.validate()
        logger.info("Config validation passed")

        Config.setup_credentials()
        logger.info("Credentials setup completed")

        bigquery_service = BigQueryService()
        logger.info("BigQuery service initialized")

        vertex_service = VertexAIService()
        logger.info("Vertex AI service initialized")

        query_processor = QueryProcessor(bigquery_service, vertex_service)
        logger.info("Query processor initialized")

        logger.info("All services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# Try to initialize services, but don't crash if it fails
services_initialized = initialize_services()

class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    query: str
    limit: Optional[int] = 1000
    include_visualization: Optional[bool] = True

class QueryResponse(BaseModel):
    """Response model for query results."""
    sql_query: str
    data: List[Dict[str, Any]]
    summary: str
    visualization_config: Optional[Dict[str, Any]] = None
    execution_time: float
    bytes_scanned: Optional[int] = None
    row_count: int

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Healthcare Analytics AI Backend",
        "status": "healthy" if services_initialized else "degraded",
        "services_initialized": services_initialized
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    if not services_initialized:
        return {
            "status": "degraded",
            "bigquery_connected": False,
            "vertex_ai_available": False,
            "project_id": Config.GCP_PROJECT_ID if Config.GCP_PROJECT_ID else "not configured",
            "error": "Services not initialized"
        }

    try:
        # Test BigQuery connection
        test_query = "SELECT COUNT(*) as patient_count FROM `bigquery-public-data.fhir_synthea.patient` LIMIT 1"
        result = bigquery_service.execute_query(test_query)

        return {
            "status": "healthy",
            "bigquery_connected": True,
            "vertex_ai_available": True,
            "project_id": Config.GCP_PROJECT_ID
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "bigquery_connected": False,
            "vertex_ai_available": False,
            "project_id": Config.GCP_PROJECT_ID,
            "error": str(e)
        }

@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Process natural language healthcare queries."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not available. Please check service status at /health")

    try:
        logger.info(f"Processing query: {request.query}")

        # Process the query
        result = await query_processor.process_query(
            natural_language_query=request.query,
            limit=request.limit,
            include_visualization=request.include_visualization
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        logger.error(f"Query that failed: {request.query}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/datasets")
async def list_datasets():
    """List available datasets in the FHIR Synthea dataset."""
    if not services_initialized:
        raise HTTPException(status_code=503, detail="Services not available. Please check service status at /health")

    try:
        datasets = bigquery_service.list_datasets()
        return {"datasets": datasets}
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list datasets: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=Config.BACKEND_HOST,
        port=Config.BACKEND_PORT,
        reload=True
    )