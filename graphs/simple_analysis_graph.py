import asyncio
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
import json
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
import fitz  # PyMuPDF

# Define the state for our simple analysis graph
class SimpleAnalysisState(TypedDict):
    file_path: str
    document_text: str
    analysis_result: str
    missing_info: str
    human_input: str
    final_result: str
    error: str
    needs_human_input: bool

# Define prompt templates
DOCUMENT_ANALYSIS_TEMPLATE = PromptTemplate.from_template("""
You are a financial document analyst. Analyze the following document and extract key information about:

1. **Company Performance**: Revenue, profits, key financial metrics
2. **Risk Factors**: Major risks and challenges mentioned
3. **Future Outlook**: Guidance and forward-looking statements
4. **Key Highlights**: Important announcements or developments

**Document Text:**
{document_text}

**Instructions:**
- If you can find sufficient information for all categories, provide a comprehensive analysis
- If critical information is missing or unclear, respond with "INSUFFICIENT_INFO" and specify what information is needed

**Response Format:**
If sufficient info: Provide detailed analysis in structured format
If insufficient: INSUFFICIENT_INFO: [Specify what specific information is needed]
""")

ANALYSIS_WITH_HUMAN_INPUT_TEMPLATE = PromptTemplate.from_template("""
You are a financial document analyst. You previously analyzed a document but needed additional information.

**Original Document Analysis:**
{original_analysis}

**Additional Information Provided by Human:**
{human_input}

**Your Task:**
Combine the original document analysis with the human-provided information to create a comprehensive final analysis covering:
1. Company Performance
2. Risk Factors  
3. Future Outlook
4. Key Highlights

Provide a well-structured, comprehensive analysis.
""")

# Node 1: Extract text from PDF
def extract_document_text(state: SimpleAnalysisState) -> SimpleAnalysisState:
    """Extract text from the PDF document."""
    print("--- Step 1: Extracting Document Text ---")
    
    file_path = state.get("file_path", "")
    if not file_path:
        return {**state, "error": "No file path provided"}
    
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        # Limit text for demo (first 5000 characters)
        text = text[:5000]
        
        print(f"Extracted {len(text)} characters from document")
        return {**state, "document_text": text}
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        return {**state, "error": f"Failed to extract text: {e}"}

# Node 2: Analyze document
def analyze_document(state: SimpleAnalysisState) -> SimpleAnalysisState:
    """Analyze the document and determine if human input is needed."""
    print("--- Step 2: Analyzing Document ---")
    
    document_text = state.get("document_text", "")
    if not document_text:
        return {**state, "error": "No document text to analyze"}
    
    # Use the prompt template
    prompt = DOCUMENT_ANALYSIS_TEMPLATE.invoke({"document_text": document_text})
    
    try:
        model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)
        messages = [
            SystemMessage(content="You are a financial document analyst. Follow the instructions precisely."),
            HumanMessage(content=prompt.text)
        ]
        
        response = model.invoke(messages)
        analysis_result = response.content
        
        print(f"Analysis result: {analysis_result[:100]}...")
          # Check if human input is needed
        if "INSUFFICIENT_INFO" in analysis_result:
            missing_info = analysis_result.replace("INSUFFICIENT_INFO:", "").strip()
            return {
                **state, 
                "analysis_result": analysis_result,
                "missing_info": missing_info,
                "needs_human_input": True
            }
        else:
            return {
                **state, 
                "analysis_result": analysis_result,
                "final_result": analysis_result,
                "needs_human_input": False
            }
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        return {**state, "error": f"Analysis failed: {e}"}

# Node 3: Human interrupt for additional information
def request_human_input(state: SimpleAnalysisState) -> SimpleAnalysisState:
    """Request additional information from human."""
    print("--- Step 3: Requesting Human Input ---")
    
    # This node will pause execution - the UI will handle the actual human input
    return {
        **state,
        "needs_human_input": True
    }

# Node 4: Generate final analysis with human input
def generate_final_analysis(state: SimpleAnalysisState) -> SimpleAnalysisState:
    """Generate final analysis incorporating human input."""
    print("--- Step 4: Generating Final Analysis ---")
    
    original_analysis = state.get("analysis_result", "")
    human_input = state.get("human_input", "")
    
    if not human_input:
        # If no human input provided, use original analysis
        return {**state, "final_result": original_analysis}
    
    # Use prompt template to combine original analysis with human input
    prompt = ANALYSIS_WITH_HUMAN_INPUT_TEMPLATE.invoke({
        "original_analysis": original_analysis,
        "human_input": human_input
    })
    
    try:
        model = init_chat_model("groq:llama3-8b-8192", temperature=0.2)
        messages = [
            SystemMessage(content="You are a financial analyst creating a comprehensive analysis."),
            HumanMessage(content=prompt.text)
        ]
        
        response = model.invoke(messages)
        final_result = response.content
        
        print("Final analysis generated successfully")
        return {**state, "final_result": final_result, "needs_human_input": False}
        
    except Exception as e:
        print(f"Error generating final analysis: {e}")
        return {**state, "error": f"Failed to generate final analysis: {e}"}

# Conditional routing function
def should_request_human_input(state: SimpleAnalysisState) -> str:
    """Determine if human input is needed."""
    needs_input = state.get("needs_human_input", False)
    final_result = state.get("final_result", "")
    
    # If we already have a final result, go to finalize
    if final_result and not needs_input:
        return "request_input"
    # If we need human input, go to request input
    elif needs_input:
        return "request_input"
    else:
        return "request_input"

# Node 5: Finalize results
def finalize_analysis(state: SimpleAnalysisState) -> SimpleAnalysisState:
    """Finalize the analysis."""
    print("--- Step 5: Analysis Complete ---")
    return {**state, "needs_human_input": False}

# Create the graph
def create_simple_analysis_graph():
    """Create and compile the simple analysis graph."""
    
    workflow = StateGraph(SimpleAnalysisState)
    
    # Add nodes
    workflow.add_node("extract_text", extract_document_text)
    workflow.add_node("analyze", analyze_document)
    workflow.add_node("request_input", request_human_input)
    workflow.add_node("final_analysis", generate_final_analysis)
    workflow.add_node("finalize", finalize_analysis)    # Add edges
    workflow.add_edge(START, "extract_text")
    workflow.add_edge("extract_text", "analyze")
    workflow.add_conditional_edges("analyze", should_request_human_input, {
        "request_input": "request_input",
        "finalize": "finalize"
    })
    workflow.add_edge("request_input", END)  # Stop here for human input
    workflow.add_edge("final_analysis", "finalize")
    workflow.add_edge("finalize", END)
    
    # Compile with memory
    app = workflow.compile(checkpointer=MemorySaver())
    
    print("✅ Simple Analysis Graph compiled successfully")
    return app

# Main function to run analysis
async def run_simple_analysis(file_path: str, thread_id: str = "simple_analysis", human_input: str = ""):
    """Run the simple analysis graph."""
    graph = create_simple_analysis_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "file_path": file_path,
        "document_text": "",
        "analysis_result": "",
        "missing_info": "",
        "human_input": human_input,
        "final_result": "",
        "error": "",
        "needs_human_input": False
    }
    
    async for state in graph.astream(initial_state, config=config, stream_mode="values"):
        yield state

# Function to continue analysis with human input
async def continue_analysis_with_input(thread_id: str, human_input: str):
    """Continue analysis with human-provided input."""
    graph = create_simple_analysis_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get the current state
    current_state = await graph.aget_state(config)
    
    if current_state and current_state.values:
        # Update state with human input
        updated_state = {
            **current_state.values,
            "human_input": human_input,
            "needs_human_input": False
        }
        
        # Run final analysis and finalize
        final_analysis_result = generate_final_analysis(updated_state)
        finalized_result = finalize_analysis(final_analysis_result)
        
        yield finalized_result
    else:
        yield {"error": "No previous state found for thread ID: " + thread_id}
