"""
Services package for the Research Agents project.

This package contains service modules including graph operations,
workflow management, and business logic services.

Import modules directly instead of using automatic imports to avoid
dependency issues when using individual graph modules.
"""

# Individual modules can be imported directly:
# from .reportgraph import create_research_graph
# from .documentsummarygraph import create_document_summary_graph  
# from .financedatagraph import create_finance_data_graph
# from .pdf_table_extraction_graph import create_pdf_table_extraction_graph, extract_pdf_tables

__all__ = [
    "create_research_graph", 
    "create_document_summary_graph",
    "create_finance_data_graph",
    "create_pdf_table_extraction_graph",
    "extract_pdf_tables"
]
