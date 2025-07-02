from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated, List
from pydantic import BaseModel, Field
import json
import re

# Pydantic models for structured output
class FinancialMetric(BaseModel):
    """A single financial metric with name and value"""
    metricName: str = Field(..., description="The name of the financial metric")
    metricValue: float = Field(..., description="The numeric value of the metric")

class FinancialMetricsResponse(BaseModel):
    """Collection of financial metrics"""
    metrics: List[FinancialMetric] = Field(..., description="List of extracted financial metrics")

# State for the finance data extraction workflow
class FinanceDataState(TypedDict):
    messages: Annotated[list, "The conversation messages"]
    user_text: str
    extracted_metrics: str
    structured_output: List[dict]

def initialize_finance_extraction(state):
    """Initialize the finance data extraction process"""
    messages = state["messages"]
    user_text = ""
    
    # Extract user message content
    if messages and len(messages) > 0:
        if isinstance(messages[0], tuple):
            user_text = messages[0][1]  # For ("user", content) format
        else:
            user_text = messages[0].content  # For message object format
    
    print(f"DEBUG: initialize_finance_extraction - Input text length: {len(user_text)} characters")
    
    return {
        "messages": messages,
        "user_text": user_text,
        "extracted_metrics": "",
        "structured_output": []
    }

def finance_data_extractor(state):
    """Single agent that extracts financial metrics from text and returns structured JSON"""
    user_text = state.get("user_text", "")
    messages = state["messages"]
    
    print(f"DEBUG: Finance Data Extractor - Processing text")
    
    system_content = f"""You are a Financial Data Extraction Agent specialized in identifying and extracting financial metrics from unstructured text.

Your task is to:
1. Analyze the provided text for financial metrics and their values
2. Extract metric names and their corresponding numeric values
3. Return the data in a specific JSON format

INPUT TEXT:
=== TEXT TO ANALYZE ===
{user_text}
=== END TEXT ===

EXTRACTION RULES:
- Look for financial metrics like: PE Ratio, PER ratio, current selling price, market cap, revenue, profit, EBITDA, debt, cash, shares outstanding, earnings per share, price to book ratio, dividend yield, ROE, ROA, etc.
- Extract only numeric values (ignore currency symbols, commas, percentages signs - but preserve the numeric value)
- For percentages, convert to decimal (e.g., "5%" becomes 5.0, not 0.05)
- Use clear, standardized metric names (e.g., "PERatio" instead of "P/E" or "Price-to-Earnings")
- If a metric appears multiple times, use the most recent or contextually relevant value

OUTPUT FORMAT:
Return a JSON array in exactly this format:
[
    {{
        "metricName": "PERatio", 
        "metricValue": 22.34
    }},
    {{
        "metricName": "currentSellingPrice",
        "metricValue": 201.45
    }}
]

IMPORTANT:
- Return ONLY the JSON array, no other text
- Ensure all values are numeric (float or int)
- Use camelCase for metric names
- If no financial metrics are found, return an empty array: []
"""
    
    system_message = SystemMessage(content=system_content)
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)  # Low temperature for consistency
    
    # Create proper message for the model
    user_message = HumanMessage(content=user_text)
    response = model.invoke([system_message, user_message])
    extracted_content = response.content.strip()
    
    print(f"DEBUG: Raw extraction result: {extracted_content}")
    
    # Parse the JSON response
    structured_output = []
    try:
        # Clean the response to extract just the JSON
        json_match = re.search(r'\[.*\]', extracted_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            structured_output = json.loads(json_str)
            print(f"DEBUG: Successfully parsed {len(structured_output)} metrics")
        else:
            print("DEBUG: No valid JSON array found in response")
            # Try to parse the entire response as JSON
            structured_output = json.loads(extracted_content)
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSON parsing error: {e}")
        # If JSON parsing fails, return empty array
        structured_output = []
    except Exception as e:
        print(f"DEBUG: Unexpected error during parsing: {e}")
        structured_output = []
    
    return {
        "messages": state["messages"],
        "user_text": user_text,
        "extracted_metrics": extracted_content,
        "structured_output": structured_output
    }

def finalize_finance_extraction(state):
    """Finalize the finance extraction and return structured output"""
    structured_output = state.get("structured_output", [])
    
    print(f"DEBUG: Finalizing finance extraction - returning {len(structured_output)} metrics")
    
    # Convert to JSON string for the final message
    json_output = json.dumps(structured_output, indent=2)
    
    return {
        "messages": [AIMessage(content=json_output)]
    }

def create_finance_data_graph():
    """Create and return the finance data extraction graph."""
    
    # Create the state graph with custom FinanceDataState
    workflow = StateGraph(FinanceDataState)
    
    # Add nodes for the workflow
    workflow.add_node("initialize", initialize_finance_extraction)
    workflow.add_node("extractor", finance_data_extractor)
    workflow.add_node("finalize", finalize_finance_extraction)
    
    # Define the workflow edges (simple linear flow)
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "extractor")
    workflow.add_edge("extractor", "finalize")
    workflow.add_edge("finalize", END)
    
    # Add memory
    memory = MemorySaver()
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
