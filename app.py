#!/usr/bin/env python3
"""
Cloud Ops Sentinel - HuggingFace Spaces Entry Point
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and create the UI (without auth - HF Spaces limitation)
from app.ui_gradio import launch

# Create the demo
demo = launch()

# Launch without auth (Gradio auth doesn't work on HF Spaces)
demo.launch(
    server_name="0.0.0.0",
    server_port=7860
)
