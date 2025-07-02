"""
Test script for the finance data extraction functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphs.financedatagraph import create_finance_data_graph
import json

def test_finance_extraction():
    """Test the finance data extraction with sample data"""
    
    # Create the finance data graph
    finance_graph = create_finance_data_graph()
    
    # Test data similar to the markdown table from the user
    test_text = """
    RENEWABLES AND ENERGY SOLUTIONS
    The company reported strong financial results for Q1 2025. 
    The PE ratio stands at 22.34, and the current selling price is $201.45.
    Revenue grew by 12.5% compared to last quarter.
    Market capitalization reached $1.2 billion.
    EBITDA margin improved to 18.7%.
    Debt-to-equity ratio is 0.65.
    Return on equity (ROE) is 15.2%.
    """
    
    config = {"configurable": {"thread_id": "test_session"}}
    
    print("Testing finance data extraction...")
    print(f"Input text: {test_text[:100]}...")
    
    # Run the graph
    for state in finance_graph.stream(
        {
            "messages": [("user", test_text)],
        }, 
        config,
        stream_mode="values"
    ):
        if "structured_output" in state:
            structured_metrics = state["structured_output"]
            print(f"\nExtracted {len(structured_metrics)} metrics:")
            print(json.dumps(structured_metrics, indent=2))
        
        if "messages" in state:
            messages = state["messages"]
            for msg in reversed(messages):
                if (hasattr(msg, 'content') and 
                    msg.content and 
                    hasattr(msg, 'type') and 
                    msg.type == 'ai'):
                    print(f"\nFinal JSON output:")
                    print(msg.content)
                    break

if __name__ == "__main__":
    test_finance_extraction()
