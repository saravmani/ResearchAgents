@echo off
echo Starting Research Agents Platform...
echo.
echo Installing required packages...
pip install PyMuPDF python-docx
echo.
echo Starting Streamlit application...
echo Running from UI folder with modular structure
streamlit run ui/main_app.py --server.port 8502
pause
