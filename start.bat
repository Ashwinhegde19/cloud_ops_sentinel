@echo off
REM Cloud Ops Sentinel - Quick Start Script for Windows
REM This script sets up and runs the Cloud Ops Sentinel demo

echo 🚀 Cloud Ops Sentinel - Quick Start
echo ==================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚙️ Creating environment file...
    copy .env.example .env
    echo 📝 Edit .env with your API keys (optional)
)

echo.
echo ✅ Setup complete! Available commands:
echo.
echo 🌐 Start UI:           python app/ui_gradio.py
echo 🔧 Test MCP Tools:     python app/mcp_server.py
echo 🧪 Run Demo:           python demo.py
echo 🧪 Run Demo (idle):    python demo.py --tool idle
echo 🧪 Run Demo (all):     python demo.py --all
echo.
echo 🌐 UI will be available at: http://localhost:7860
echo.

REM Ask user what to run
set /p choice="What would you like to do? (1=Start UI, 2=Run demo, 3=Test MCP tools, 4=Exit): "

if "%choice%"=="1" (
    echo 🚀 Starting Gradio UI...
    python app/ui_gradio.py
) else if "%choice%"=="2" (
    echo 🧪 Running demo script...
    python demo.py
) else if "%choice%"=="3" (
    echo 🔧 Testing MCP tools...
    python app/mcp_server.py
) else if "%choice%"=="4" (
    echo 👋 Goodbye!
) else (
    echo ❌ Invalid option
)

pause