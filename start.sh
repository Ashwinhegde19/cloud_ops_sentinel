#!/bin/bash

# Cloud Ops Sentinel - Quick Start Script
# This script sets up and runs the Cloud Ops Sentinel demo

set -e

echo "🚀 Cloud Ops Sentinel - Quick Start"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    cp .env.example .env
    echo "📝 Edit .env with your API keys (optional)"
fi

echo ""
echo "✅ Setup complete! Available commands:"
echo ""
echo "🌐 Start UI:           python app/ui_gradio.py"
echo "🔧 Test MCP Tools:     python app/mcp_server.py"
echo "🧪 Run Demo:           python demo.py"
echo "🧪 Run Demo (idle):    python demo.py --tool idle"
echo "🧪 Run Demo (all):     python demo.py --all"
echo ""
echo "🌐 UI will be available at: http://localhost:7860"
echo ""

# Ask user what to run
echo "What would you like to do?"
echo "1) Start Gradio UI"
echo "2) Run demo script"
echo "3) Test MCP tools"
echo "4) Exit"
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting Gradio UI..."
        python app/ui_gradio.py
        ;;
    2)
        echo "🧪 Running demo script..."
        python demo.py
        ;;
    3)
        echo "🔧 Testing MCP tools..."
        python app/mcp_server.py
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac