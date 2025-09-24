"""Streamlit frontend for healthcare analytics application."""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional
import time
import os

# Page configuration
st.set_page_config(
    page_title="Healthcare Analytics AI",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration - use environment variable if available
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("Healthcare Analytics AI")
    st.markdown("Healthcare Analytics AI - Powered by BigQuery, Vertex AI, and Streamlit | Data source: FHIR Synthea Public Dataset. Ask questions about healthcare data in natural language and get insights, SQL analysis, and visualizations.")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Backend URL configuration
        backend_url = st.text_input(
            "Backend URL", 
            value=BACKEND_URL,
            help="URL of the FastAPI backend"
        )
        
        # Query settings
        st.subheader("Query Settings")
        limit = st.slider(
            "Result Limit", 
            min_value=100, 
            max_value=5000, 
            value=1000,
            help="Maximum number of rows to return"
        )
        
        include_viz = st.checkbox(
            "Include Visualizations", 
            value=True,
            help="Generate charts and graphs from results"
        )
        
        # Sample queries
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "How many patients are there in the dataset?",
            "What are the most common medical conditions?",
            "Show me the age distribution of patients",
            "What medications are most frequently prescribed?",
            "How many patients have diabetes?",
            "Show me patient demographics by gender",
            "What procedures are performed most often?",
            "How many healthcare encounters occurred last year?"
        ]
        
        for query in sample_queries:
            if st.button(f"{query}", key=f"sample_{hash(query)}"):
                st.session_state.query_input = query
    
    # Main content area

    st.subheader("Ask a Question 💬")
    
    # Query input
    query_input = st.text_area(
        "Enter your healthcare question:",
        value=st.session_state.get("query_input", ""),
        height=100,
        placeholder="e.g., 'How many patients have diabetes?' or 'Show me the most common medications'"
    )
    
    # Submit button
    if st.button("🔍 Analyze", type="primary"):
        if query_input.strip():
            process_query(query_input, limit, include_viz, backend_url)
        else:
            st.error("Please enter a question to analyze.")


def process_query(query: str, limit: int, include_viz: bool, backend_url: str):
    """Process a natural language query."""
    
    with st.spinner("🤖 Processing your question..."):
        try:
            # Prepare request
            request_data = {
                "query": query,
                "limit": limit,
                "include_visualization": include_viz
            }
            
            # Make API call
            response = requests.post(
                f"{backend_url}/ask",
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                display_results(result, query)
            else:
                st.error(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to backend. Please ensure the FastAPI server is running.")
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Please try a simpler query.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")

def display_results(result: Dict[str, Any], original_query: str):
    """Display query results with visualizations."""
    
    # Summary
    st.subheader("📋 Summary")
    st.info(result["summary"])
    
    # Execution info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏱️ Execution Time", f"{result['execution_time']:.2f}s")
    with col2:
        st.metric("📊 Rows Returned", result["row_count"])
    with col3:
        if result.get("bytes_scanned"):
            st.metric("💾 Data Scanned", f"{result['bytes_scanned']:,} bytes")
    
    # SQL Query
    with st.expander("🔍 Generated SQL Query"):
        st.code(result["sql_query"], language="sql")
    
    # Data table
    if result["data"]:
        st.subheader("📊 Results")
        df = pd.DataFrame(result["data"])
        st.dataframe(df, use_container_width=True)
        
        # Visualization
        if result.get("visualization_config") and result["visualization_config"]["type"] != "table":
            st.subheader("📈 Visualization")
            create_visualization(result["visualization_config"])
    else:
        st.warning("No data returned from the query.")

def create_visualization(config: Dict[str, Any]):
    """Create visualization based on configuration."""
    try:
        df = pd.DataFrame(config["data"])
        
        if config["type"] == "line":
            fig = px.line(
                df, 
                x=config["x"], 
                y=config["y"],
                title=config["title"]
            )
            fig.update_layout(
                xaxis_title=config["x_title"],
                yaxis_title=config["y_title"]
            )
            
        elif config["type"] == "bar":
            fig = px.bar(
                df, 
                x=config["x"], 
                y=config["y"],
                title=config["title"]
            )
            fig.update_layout(
                xaxis_title=config["x_title"],
                yaxis_title=config["y_title"]
            )
            
        elif config["type"] == "scatter":
            fig = px.scatter(
                df, 
                x=config["x"], 
                y=config["y"],
                title=config["title"]
            )
            fig.update_layout(
                xaxis_title=config["x_title"],
                yaxis_title=config["y_title"]
            )
            
        else:
            st.info("Visualization type not supported.")
            return
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to create visualization: {str(e)}")

def display_quick_stats(backend_url: str):
    """Display quick statistics about the dataset."""
    try:
        response = requests.get(f"{backend_url}/datasets", timeout=10)
        if response.status_code == 200:
            datasets = response.json()["datasets"]
            st.metric("📁 Available Tables", len(datasets))
            
            # Show some table names
            if datasets:
                st.write("**Sample tables:**")
                for table in datasets[:5]:
                    st.write(f"• {table}")
                if len(datasets) > 5:
                    st.write(f"... and {len(datasets) - 5} more")
        else:
            st.info("Unable to load dataset information")
    except:
        st.info("Backend not available")

if __name__ == "__main__":
    main()