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
from .mapreduce_graph import create_transcript_mapreduce_graph, analyze_transcript
from .simple_analysis_graph import create_simple_analysis_graph, run_simple_analysis, continue_analysis_with_input
from .simple_calculator_graph import create_calculator_graph, run_calculator, continue_calculator_with_input, get_calculator_state

__all__ = [
    "create_research_graph", 
    "create_document_summary_graph",
    "create_finance_data_graph",
    "create_pdf_table_extraction_graph",
    "extract_pdf_tables",
    "create_transcript_mapreduce_graph",
    "analyze_transcript",
    "create_simple_analysis_graph",
    "run_simple_analysis",
    "continue_analysis_with_input",
    "create_calculator_graph",
    "run_calculator", 
    "continue_calculator_with_input",
    "get_calculator_state"
]
