"""
Test script for the document summary functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.documentsummarygraph import create_document_summary_graph
import io

def test_document_processing():
    """Test the document processing with sample text data"""
    
    # Create the document summary graph
    doc_graph = create_document_summary_graph()
    
    # Create sample text content
    sample_text = """
    FINANCIAL REPORT Q1 2025
    
    Executive Summary:
    Our company has shown remarkable growth in Q1 2025. Revenue increased by 25% compared to the same period last year, reaching $15.2 million. The PE ratio stands at 22.34, and our current selling price is $201.45 per share.
    
    Key Metrics:
    - Revenue: $15.2M (+25% YoY)
    - EBITDA: $3.8M (25% margin)
    - Net Income: $2.1M
    - PE Ratio: 22.34
    - Share Price: $201.45
    - Market Cap: $1.2B
    - Debt-to-Equity: 0.65
    - ROE: 15.2%
    
    Strategic Initiatives:
    1. Expansion into new markets
    2. Technology infrastructure improvements
    3. Talent acquisition in key areas
    4. Sustainability initiatives
    
    Risks and Challenges:
    - Market volatility
    - Supply chain disruptions
    - Regulatory changes
    - Competition from new entrants
    
    Outlook:
    We remain optimistic about Q2 2025 performance based on strong pipeline and market conditions.
    """
    
    # Convert text to bytes (simulating file upload)
    file_content = sample_text.encode('utf-8')
    file_name = "sample_financial_report.txt"
    file_type = "txt"
    
    config = {"configurable": {"thread_id": "test_session"}}
    
    print("Testing document processing workflow...")
    print(f"Input document: {file_name}")
    print(f"Content length: {len(sample_text)} characters")
    print("=" * 50)
    
    # Run the graph
    for state in doc_graph.stream(
        {
            "messages": [("user", "Please provide a comprehensive summary focusing on financial metrics and strategic insights")],
            "file_content": file_content,
            "file_name": file_name,
            "file_type": file_type
        }, 
        config,
        stream_mode="values"
    ):
        processing_stage = state.get("processing_stage", "")
        print(f"Processing stage: {processing_stage}")
        
        if processing_stage == "parsed":
            parsed_length = len(state.get("parsed_text", ""))
            print(f"✅ Parsed {parsed_length} characters")
        
        elif processing_stage == "completed":
            print("✅ Summary generation completed")
        
        elif "error" in processing_stage:
            error_msg = state.get("error_message", "Unknown error")
            print(f"❌ Error: {error_msg}")
        
        if "messages" in state:
            messages = state["messages"]
            for msg in reversed(messages):
                if (hasattr(msg, 'content') and 
                    msg.content and 
                    hasattr(msg, 'type') and 
                    msg.type == 'ai'):
                    print("\n" + "=" * 50)
                    print("FINAL SUMMARY:")
                    print("=" * 50)
                    print(msg.content)
                    print("=" * 50)
                    break

if __name__ == "__main__":
    test_document_processing()
