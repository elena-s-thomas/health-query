# Healthcare Analytics AI

An AI-powered data explorer for synthetic healthcare data (FHIR Synthea) using BigQuery, Vertex AI, and Streamlit. Users can ask questions in natural language and receive insights, SQL analysis, and visualizations.

## 🏗️ Architecture

- **Backend**: FastAPI with BigQuery and Vertex AI integration
- **Frontend**: Streamlit web interface
- **AI**: Vertex AI for natural language to SQL translation
- **Data**: Public FHIR Synthea dataset on BigQuery
- **Visualization**: Plotly charts and graphs

## 🚀 Quick Start

### Prerequisites

1. **Google Cloud Platform Account**
   - Create a GCP project
   - Enable BigQuery API and Vertex AI API
   - Set up billing (required even for free tier)

2. **Service Account**
   - Create a service account with BigQuery and Vertex AI permissions
   - Download the service account key JSON file

3. **Python 3.11+**
   - Install Python 3.11 or higher

### Installation

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd health-query
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env with your GCP project details
   ```

3. **Set up authentication**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
   ```

### Running Locally

1. **Start the backend**
   ```bash
   python main.py
   ```
   Backend will be available at `http://localhost:8000`

2. **Start the frontend** (in a new terminal)
   ```bash
   streamlit run streamlit_app.py
   ```
   Frontend will be available at `http://localhost:8501`

### Running with Docker

1. **Using Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Individual containers**
   ```bash
   # Backend
   docker build -f Dockerfile.backend -t healthcare-backend .
   docker run -p 8000:8000 --env-file .env healthcare-backend
   
   # Frontend
   docker build -f Dockerfile.frontend -t healthcare-frontend .
   docker run -p 8501:8501 healthcare-frontend
   ```

## 📊 Usage

1. **Open the Streamlit app** at `http://localhost:8501`
2. **Enter a natural language question** such as:
   - "How many patients are there in the dataset?"
   - "What are the most common medical conditions?"
   - "Show me the age distribution of patients"
   - "What medications are most frequently prescribed?"

3. **View results** including:
   - Natural language summary
   - Generated SQL query
   - Data table
   - Interactive visualizations

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Your GCP project ID | Required |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | Required |
| `BIGQUERY_DATASET` | BigQuery dataset to use | `bigquery-public-data.fhir_synthea` |
| `VERTEX_MODEL` | Vertex AI model to use | `text-bison@002` |
| `REGION` | GCP region | `us-central1` |

### API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /ask` - Process natural language queries
- `GET /datasets` - List available datasets

## 📈 Features

### Natural Language Processing
- Converts healthcare questions to SQL queries
- Uses Vertex AI for intelligent query generation
- Handles complex healthcare terminology

### Data Visualization
- Automatic chart type detection
- Time series analysis
- Categorical distributions
- Scatter plots for correlations

### Cost Optimization
- Query cost estimation
- Free tier optimization
- Usage monitoring and limits

## 🏥 Sample Queries

Try these example questions:

- **Demographics**: "Show me patient demographics by gender and age"
- **Conditions**: "What are the top 10 most common medical conditions?"
- **Medications**: "Which medications are prescribed most frequently?"
- **Procedures**: "What procedures are performed most often?"
- **Trends**: "Show me healthcare encounters over time"
- **Specific Conditions**: "How many patients have diabetes?"

## 🚀 Deployment

### Google Cloud Run

1. **Build and push containers**
   ```bash
   # Build backend
   docker build -f Dockerfile.backend -t gcr.io/PROJECT_ID/healthcare-backend .
   docker push gcr.io/PROJECT_ID/healthcare-backend
   
   # Build frontend
   docker build -f Dockerfile.frontend -t gcr.io/PROJECT_ID/healthcare-frontend .
   docker push gcr.io/PROJECT_ID/healthcare-frontend
   ```

2. **Deploy to Cloud Run**
   ```bash
   # Deploy backend
   gcloud run deploy healthcare-backend \
     --image gcr.io/PROJECT_ID/healthcare-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   
   # Deploy frontend
   gcloud run deploy healthcare-frontend \
     --image gcr.io/PROJECT_ID/healthcare-frontend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure service account has proper permissions
   - Check `GOOGLE_APPLICATION_CREDENTIALS` path
   - Verify GCP project ID is correct

2. **BigQuery Access**
   - Enable BigQuery API in GCP console
   - Ensure billing is enabled
   - Check dataset permissions

3. **Vertex AI Issues**
   - Enable Vertex AI API
   - Verify model availability in your region
   - Check quota limits

4. **Connection Issues**
   - Ensure backend is running before starting frontend
   - Check port availability (8000, 8501)
   - Verify firewall settings

## 📚 Data Schema

The application works with the FHIR Synthea dataset, which includes:

- **patient**: Patient demographics and basic information
- **observation**: Clinical observations and measurements
- **condition**: Medical conditions and diagnoses
- **procedure**: Medical procedures performed
- **medication**: Medications prescribed
- **encounter**: Healthcare encounters/visits
- **organization**: Healthcare organizations
- **practitioner**: Healthcare providers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FHIR Synthea](https://synthea.mitre.org/) for the synthetic healthcare dataset
- [Google Cloud BigQuery](https://cloud.google.com/bigquery) for data storage
- [Vertex AI](https://cloud.google.com/vertex-ai) for AI capabilities
- [Streamlit](https://streamlit.io/) for the web interface