#!/bin/bash

# ☁️ Cloud Ops Sentinel - Quick Start Script
# Enterprise Cloud Operations Assistant

set -e

echo ""
echo "  ☁️  Cloud Ops Sentinel"
echo "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Enterprise Cloud Operations Assistant"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "📝 Note: Edit .env with your API keys for full functionality"
    echo "   The app works in simulation mode without API keys."
    echo ""
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Starting Cloud Ops Sentinel..."
echo ""
echo "   Dashboard: http://localhost:7860"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the Gradio UI
python app/ui_gradio.py
