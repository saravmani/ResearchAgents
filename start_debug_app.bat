@echo off
echo =====================================
echo  Document Summarizer - Debug Mode
echo =====================================
echo.

echo [1/3] Setting up environment...
set STREAMLIT_SERVER_HEADLESS=false
set STREAMLIT_LOGGER_LEVEL=debug
set PYTHONPATH=%cd%

echo [2/3] Checking dependencies...
python -c "import streamlit, fitz, docx; print('✅ All dependencies available')" 2>nul
if errorlevel 1 (
    echo ❌ Missing dependencies. Installing...
    pip install PyMuPDF python-docx
)

echo [3/3] Starting Streamlit app in debug mode...
echo.
echo 🚀 Starting on http://localhost:8502
echo 🔧 Debug mode enabled
echo 📝 Logs will be shown in console
echo.
echo Press Ctrl+C to stop the application
echo =====================================

streamlit run document_summarizer_app.py --server.port 8502 --logger.level debug

pause
