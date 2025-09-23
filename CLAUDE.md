# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Healthcare Analytics AI - An AI-powered data explorer for synthetic healthcare data (FHIR Synthea) using BigQuery, Vertex AI, and Streamlit. The application translates natural language healthcare queries into SQL and provides visualizations.

## Architecture

- **Backend**: FastAPI service (main.py) on port 8000
- **Frontend**: Streamlit web UI (streamlit_app.py) on port 8501
- **Database**: BigQuery public dataset: `bigquery-public-data.fhir_synthea`
- **AI Model**: Vertex AI (Gemini 1.5 Flash) for NL to SQL translation
- **Services Architecture**:
  - `BigQueryService`: Handles BigQuery operations and query execution
  - `VertexAIService`: Manages Vertex AI model interactions
  - `QueryProcessor`: Orchestrates NL query processing pipeline
  - `VisualizationService`: Generates Plotly chart configurations

## Development Commands

### Setup
```bash
# Create virtual environment and install dependencies
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Locally
```bash
# Backend
python main.py

# Frontend (in new terminal)
streamlit run streamlit_app.py

# With Docker
docker-compose up --build
```

### Testing Connection
```bash
python test_connection.py
```

## Configuration

Required environment variables (in .env):
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to service account JSON key
- `BIGQUERY_DATASET`: Default is `bigquery-public-data.fhir_synthea`
- `VERTEX_MODEL`: Default is `gemini-1.5-flash`
- `REGION`: Default is `us-central1`

## Key API Endpoints

- `GET /`: Health check
- `GET /health`: Detailed health check with service status
- `POST /ask`: Process natural language queries
- `GET /datasets`: List available FHIR datasets

## FHIR Synthea Dataset Tables

Primary tables in `bigquery-public-data.fhir_synthea`:
- `patient`: Patient demographics
- `observation`: Clinical observations
- `condition`: Medical conditions
- `procedure`: Medical procedures
- `medication_request`: Medications prescribed
- `encounter`: Healthcare visits
- `organization`: Healthcare organizations
- `practitioner`: Healthcare providers

## Project Structure

- `config.py`: Central configuration management
- `services/`: Core service implementations
  - `bigquery_service.py`: BigQuery client and query execution
  - `vertex_service.py`: Vertex AI model interactions
  - `query_processor.py`: Query processing pipeline
  - `visualization_service.py`: Chart generation logic
- `streamlit_app.py`: Frontend UI implementation
- `test_connection.py`: Service connectivity testing