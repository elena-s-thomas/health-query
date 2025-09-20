#!/bin/bash

# Healthcare Analytics AI Setup Script

set -e

echo "🏥 Healthcare Analytics AI Setup"
echo "================================"

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.template .env
    echo "📝 Please edit .env file with your GCP project details"
fi

# Check for service account key
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️ GOOGLE_APPLICATION_CREDENTIALS environment variable not set"
    echo "Please set it to the path of your service account key file"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your GCP project details"
echo "2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable"
echo "3. Run: python main.py (for backend)"
echo "4. Run: streamlit run streamlit_app.py (for frontend)"
echo ""
echo "Or use Docker: docker-compose up --build"