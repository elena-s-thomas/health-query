"""Test script to verify BigQuery and Vertex AI connections."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(dotenv_path=env_path)

def test_bigquery_connection():
    """Test BigQuery connection."""
    try:
        from google.cloud import bigquery
        
        client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
        
        # Test query
        query = "SELECT COUNT(*) as patient_count FROM `bigquery-public-data.fhir_synthea.patient` LIMIT 1"
        results = client.query(query).result()
        
        for row in results:
            print(f"✅ BigQuery connection successful! Patient count: {row.patient_count}")
            return True
            
    except Exception as e:
        print(f"❌ BigQuery connection failed: {e}")
        return False

def test_vertex_ai_connection():
    """Test Vertex AI connection."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        vertexai.init(project=os.getenv("GCP_PROJECT_ID"), location=os.getenv("REGION", "us-central1"))
        model = GenerativeModel(os.getenv("VERTEX_MODEL", "gemini-1.5-flash"))
        
        # Test generation
        response = model.generate_content("Hello, this is a test.")
        
        print(f"✅ Vertex AI connection successful! Test response: {response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Vertex AI connection failed: {e}")
        return False

def main():
    """Run all connection tests."""
    print("🧪 Testing Healthcare Analytics AI Connections")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["GCP_PROJECT_ID", "GOOGLE_APPLICATION_CREDENTIALS"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    
    print(f"📋 Project ID: {os.getenv('GCP_PROJECT_ID')}")
    print(f"📋 Credentials: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    print()
    
    # Test connections
    bigquery_ok = test_bigquery_connection()
    vertex_ok = test_vertex_ai_connection()
    
    print()
    if bigquery_ok and vertex_ok:
        print("🎉 All connections successful! You're ready to run the application.")
        return True
    else:
        print("❌ Some connections failed. Please check your configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)