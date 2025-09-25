#!/bin/bash

# Mental Health Agent Starter - Run Script
# This script helps you get started with the Mental Health Agent

echo "🧠 Mental Health Agent Starter"
echo "=============================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check environment variables
echo "Checking environment variables..."
if [ -z "$AWS_REGION" ]; then
    echo "⚠️  AWS_REGION not set. Defaulting to us-east-1"
    export AWS_REGION=us-east-1
fi

if [ -z "$MH_BUCKET" ]; then
    echo "⚠️  MH_BUCKET not set. Defaulting to mental-health-agent"
    export MH_BUCKET=mental-health-agent
fi

if [ -z "$API_BASE" ]; then
    echo "⚠️  API_BASE not set. Setting to your API Gateway URL"
    export API_BASE=https://ot173x9io1.execute-api.us-west-2.amazonaws.com
    echo "   Set to: $API_BASE"
fi

echo ""
echo "🚀 Ready to use the Mental Health Agent!"
echo ""
echo "Available commands:"
echo "  python scripts/invoke_mental_health_agent.py chat --help"
echo "  python scripts/invoke_mental_health_agent.py checkin --help"
echo "  python scripts/invoke_mental_health_agent.py evaluate --help"
echo "  python scripts/invoke_mental_health_agent.py recommendations --help"
echo "  python scripts/invoke_mental_health_agent.py schedule --help"
echo ""
echo "Web interface:"
echo "  streamlit run streamlit_playground.py"
echo ""
echo "Example usage:"
echo "  python scripts/invoke_mental_health_agent.py chat --user-id 'demo_user' --message 'I feel stressed today'"
echo ""
