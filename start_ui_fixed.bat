@echo off
echo Starting Research Agents UI...
echo.
echo Setting up environment...
cd /d "d:\Git\ResearchAgents"
set PYTHONPATH=%CD%

echo.
echo Starting Streamlit application...
python -m streamlit run ui/main_app.py --server.port 8503 --server.headless false

pause
