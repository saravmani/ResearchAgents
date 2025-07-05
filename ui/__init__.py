"""
UI package for Research Agents Platform

This package contains all the Streamlit UI components organized into separate modules:
- home_page.py: Home page with platform overview and metrics
- document_summarizer.py: Document summarization functionality
- main_app.py: Main application with navigation and routing
"""

from .home_page import show_home_page
from .document_summarizer import show_document_summarizer, initialize_document_summarizer_session

__all__ = [
    "show_home_page",
    "show_document_summarizer", 
    "initialize_document_summarizer_session"
]
