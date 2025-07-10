import asyncio
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import init_chat_model
import json
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
import fitz  # PyMuPDF

# Define the state for our map-reduce graph
class TranscriptMapReduceState(TypedDict):
    file_path: str
    transcript_text: str
    chunks: List[str]
    # The `chunk_results` will now be a list of dictionaries, 
    # where each dictionary is the result of the map_phase_extractor
    chunk_results: List[Dict]
    aggregated_results: Dict[str, Any]
    final_summary: str
    error: str
    # Rules and human intervention
    analysis_rules: str
    rules_validation: Dict[str, Any]
    human_approval: bool
    validation_feedback: str
    human_review_required: bool

# New Node: Extract text from PDF
def extract_pdf_text(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Extracts text content from a given PDF file."""
    print("--- Step 0: Extracting Text from PDF ---")
    file_path = state.get("file_path", "")
    if not file_path:
        return {**state, "error": "No file path provided."}

    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        print(f"Extracted {len(text)} characters from {file_path}")
        return {**state, "transcript_text": text}
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return {**state, "error": f"Failed to read PDF: {e}"}


# Node 1: Chunk the document
def chunk_document(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Splits the transcript text into overlapping chunks."""
    print("--- Step 1: Chunking Document ---")
    text = state.get("transcript_text", "")
     
    if not text:
        return {**state, "error": "No text to chunk."}

    # Limit to first 3000 tokens for POC
    text = text[:3000]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )
    chunks = text_splitter.split_text(text)
    
    print(f"Document split into {len(chunks)} chunks.")
    
    return {
        "file_path": state["file_path"],
        "transcript_text": text,
        "chunks": chunks,
        "chunk_results": [],
        "aggregated_results": {},
        "final_summary": "",
        "error": ""
    }

# Node 2: Parallel extraction from each chunk (Map phase)
async def map_phase_extractor(chunk: str) -> Dict[str, Any]:
    """
    Extracts financial information from a single chunk of text using an LLM.
    """
    print(f"--- Step 2: Processing Chunk (Map Phase) ---")
    
    system_prompt = """You are an expert financial analyst. Your task is to extract key financial metrics, insights, and forward-looking statements from the provided text chunk of an earnings call transcript.

Focus on the following:
- **Key Financial Metrics**: Revenue, Net Income, EPS, Margins, etc.
- **Guidance/Outlook**: Any forward-looking statements about future performance.
- **Key Business Drivers**: What is driving performance? New products, market trends, etc.
- **Risks and Challenges**: Any mentioned risks or headwinds.
- **Management Tone**: Is the tone optimistic, cautious, or pessimistic?

Present the extracted information in a structured JSON format. For example:
{
  "metrics": [{"name": "Revenue", "value": "10B", "period": "Q4 2024"}],
  "guidance": "Company expects 10% revenue growth in the next quarter.",
  "key_drivers": ["Strong cloud segment growth", "New AI product adoption"],
  "risks": ["Macroeconomic uncertainty", "Supply chain constraints"],
  "tone": "Optimistic"
}
"""
    
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=chunk)
    ]
    
    try:
        response = await model.ainvoke(messages)
        # Attempt to parse the JSON output
        extracted_data = json.loads(response.content)
        return {"extracted_data": extracted_data}
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing LLM response for chunk: {e}")
        # Fallback to returning raw text if JSON parsing fails
        return {"extracted_data": {"raw_text": response.content}}
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")
        return {"extracted_data": {"error": str(e)}}


async def map_phase(state: TranscriptMapReduceState) -> dict:
    """
    Asynchronously runs the extractor on all chunks in parallel with progress tracking.
    """
    print("--- Step 2: Processing Chunks in Parallel (Map Phase) ---")
    
    chunks = state["chunks"]
    total_chunks = len(chunks)
    
    # Create tasks for parallel processing
    tasks = []
    for i, chunk in enumerate(chunks):
        task = map_phase_extractor_with_progress(chunk, i + 1, total_chunks)
        tasks.append(task)
    
    # Process all chunks in parallel
    chunk_results = await asyncio.gather(*tasks)
    
    print(f"✅ Completed processing all {len(chunk_results)} chunks.")
    
    return {"chunk_results": chunk_results}

async def map_phase_extractor_with_progress(chunk: str, chunk_number: int, total_chunks: int) -> Dict[str, Any]:
    """
    Extracts financial information from a single chunk with progress tracking.
    """
    print(f"🔍 Processing chunk {chunk_number}/{total_chunks} (Map Phase)")
    
    system_prompt = """You are an expert financial analyst. Your task is to extract key financial metrics, insights, and forward-looking statements from the provided text chunk of an earnings call transcript.

Focus on the following:
- **Key Financial Metrics**: Revenue, Net Income, EPS, Margins, etc.
- **Guidance/Outlook**: Any forward-looking statements about future performance.
- **Key Business Drivers**: What is driving performance? New products, market trends, etc.
- **Risks and Challenges**: Any mentioned risks or headwinds.
- **Management Tone**: Is the tone optimistic, cautious, or pessimistic?

Present the extracted information in a structured JSON format. For example:
{
  "metrics": [{"name": "Revenue", "value": "10B", "period": "Q4 2024"}],
  "guidance": "Company expects 10% revenue growth in the next quarter.",
  "key_drivers": ["Strong cloud segment growth", "New AI product adoption"],
  "risks": ["Macroeconomic uncertainty", "Supply chain constraints"],
  "tone": "Optimistic"
}
"""
    
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=chunk)
    ]
    
    try:
        response = await model.ainvoke(messages)
        # Attempt to parse the JSON output
        extracted_data = json.loads(response.content)
        print(f"✅ Chunk {chunk_number}/{total_chunks} processed successfully")
        return {
            "extracted_data": extracted_data,
            "chunk_number": chunk_number,
            "total_chunks": total_chunks
        }
    except (json.JSONDecodeError, TypeError) as e:
        print(f"⚠️ Chunk {chunk_number}/{total_chunks} - JSON parsing error: {e}")
        # Fallback to returning raw text if JSON parsing fails
        return {
            "extracted_data": {"raw_text": response.content},
            "chunk_number": chunk_number,
            "total_chunks": total_chunks
        }
    except Exception as e:
        print(f"❌ Chunk {chunk_number}/{total_chunks} - Error: {e}")
        return {
            "extracted_data": {"error": str(e)},
            "chunk_number": chunk_number,
            "total_chunks": total_chunks
        }


# Node 3: Aggregate and deduplicate results (Reduce phase)
def reduce_phase_aggregator(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Aggregates results from all chunks, removing duplicates."""
    print("--- Step 3: Aggregating and Deduplicating Results (Reduce Phase) ---")
    
    chunk_results = state.get("chunk_results", [])
    if not chunk_results:
        return {**state, "error": "No chunk results to aggregate."}

    all_metrics = []
    all_guidance = []
    all_drivers = []
    all_risks = []
    
    for result in chunk_results:
        data = result.get("extracted_data", {})
        if isinstance(data, dict):
            all_metrics.extend(data.get("metrics", []))
            if data.get("guidance"): all_guidance.append(data.get("guidance"))
            if data.get("key_drivers"): all_drivers.extend(data.get("key_drivers"))
            if data.get("risks"): all_risks.extend(data.get("risks"))

    # Deduplicate using a simple method
    unique_metrics = []
    seen_metrics = set()
    for metric in all_metrics:
        if isinstance(metric, dict):
            identifier = tuple(sorted(metric.items()))
            if identifier not in seen_metrics:
                unique_metrics.append(metric)
                seen_metrics.add(identifier)
            
    unique_guidance = list(set(all_guidance))
    unique_drivers = list(set(all_drivers))
    unique_risks = list(set(all_risks))
    
    aggregated_results = {
        "metrics": unique_metrics,
        "guidance": unique_guidance,
        "key_drivers": unique_drivers,
        "risks": unique_risks
    }
    
    print(f"Aggregation complete. Found {len(unique_metrics)} unique metrics.")
    
    return {**state, "aggregated_results": aggregated_results}

# Node 4: Generate the final summary
def generate_final_summary(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Generates a final, concise summary from the aggregated data."""
    print("--- Step 4: Generating Final Summary ---")
    
    aggregated_data = state.get("aggregated_results", {})
    if not aggregated_data:
        return {**state, "error": "No aggregated data to summarize."}

    summary_prompt = f"""You are a senior financial analyst. Your task is to synthesize the extracted financial information into a concise, easy-to-read summary.
The information was extracted from a long earnings call transcript. Focus on the most critical insights.

**Extracted Information:**
```json
{json.dumps(aggregated_data, indent=2)}
```

**Your Task:**
Generate a final summary covering the following points:
1.  **Overall Performance**: A brief overview of the company's performance in the quarter.
2.  **Key Financial Highlights**: List the most important metrics (e.g., Revenue, EPS).
3.  **Future Outlook**: Summarize the company's guidance and future expectations.
4.  **Key Themes**: Mention the main business drivers and risks discussed.

Keep the summary professional and to the point. Use bullet points for clarity.
"""
    
    model = init_chat_model("groq:llama3-8b-8192", temperature=0.3)
    messages = [
        SystemMessage(content="You are a senior financial analyst creating a summary."),
        HumanMessage(content=summary_prompt)
    ]
    
    response = model.invoke(messages)
    final_summary = response.content
    
    print("Final summary generated.")
    
    return {**state, "final_summary": final_summary}


# Node 5: Validate rules
def validate_rules(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Validates the analysis results against user-defined rules."""
    print("--- Step 5: Validating Analysis Against Rules ---")
    
    analysis_rules = state.get("analysis_rules", "")
    if not analysis_rules or analysis_rules.strip() == "":
        print("No rules specified, skipping validation.")
        return {**state, "rules_validation": {"satisfied": True, "message": "No rules specified"}, "human_approval": True}
    
    final_summary = state.get("final_summary", "")
    aggregated_results = state.get("aggregated_results", {})
    
    # Create a validation prompt
    validation_prompt = f"""You are a financial analysis validator. Your task is to check if the analysis results satisfy the given rules.

**Analysis Rules:**
{analysis_rules}

**Final Summary:**
{final_summary}

**Extracted Data:**
```json
{json.dumps(aggregated_results, indent=2)}
```

**Your Task:**
Evaluate whether the analysis results satisfy each rule. For each rule:
1. Check if it's satisfied based on the summary and extracted data
2. Provide specific feedback on what's missing or needs improvement

Respond in JSON format:
{{
    "overall_satisfaction": true/false,
    "rule_assessments": [
        {{ 
            "rule": "Rule description",
            "satisfied": true/false,
            "feedback": "Specific feedback"
        }}
    ],
    "recommendations": ["List of recommendations for improvement"]
}}
"""
    
    try:
        model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)
        messages = [
            SystemMessage(content="You are a financial analysis validator. Respond only in valid JSON format."),
            HumanMessage(content=validation_prompt)
        ]
        
        response = model.invoke(messages)
        validation_result = json.loads(response.content)
        
        print(f"Rules validation complete. Overall satisfied: {validation_result.get('overall_satisfaction', False)}")
        
        return {
            **state, 
            "rules_validation": validation_result,
            "human_approval": validation_result.get("overall_satisfaction", False)
        }
        
    except Exception as e:
        print(f"Error during rules validation: {e}")
        return {
            **state, 
            "rules_validation": {
                "satisfied": False, 
                "message": f"Validation error: {str(e)}"
            },
            "human_approval": False
        }


# Node 6: Human interrupt for approval using proper LangGraph interrupt
def human_interrupt(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Pauses for human review when rules are not satisfied using LangGraph interrupt."""
    print("--- Step 6: Human Review Required ---")
    
    rules_validation = state.get("rules_validation", {})
    human_approval = state.get("human_approval", False)
    
    if human_approval:
        print("Analysis passed all rules. No human intervention needed.")
        return {**state, "validation_feedback": "Analysis approved automatically."}
    
    print("Analysis did not satisfy all rules. Human review required.")
    
    # Prepare validation message for human review
    validation_message = "Analysis requires human review:\n\n"
    
    if "rule_assessments" in rules_validation:
        validation_message += "**Rules Assessment:**\n"
        for assessment in rules_validation["rule_assessments"]:
            status = "✅" if assessment.get("satisfied", True) else "❌"
            validation_message += f"{status} {assessment.get('rule', 'Unknown rule')}: {assessment.get('feedback', 'No feedback')}\n"
    
    if "recommendations" in rules_validation:
        validation_message += f"\n**Recommendations:**\n"
        for rec in rules_validation['recommendations']:
            validation_message += f"• {rec}\n"
    
    validation_message += "\n**Analysis Summary:**\n"
    validation_message += state.get("final_summary", "No summary available")
    
    # For Streamlit UI integration, we'll set a special flag to indicate human review is needed
    # and return the state with validation details for the UI to handle
    return {
        **state, 
        "validation_feedback": validation_message,
        "human_review_required": True,
        "human_approval": False  # Will be updated by UI
    }


# Conditional function to determine if human approval is needed
def should_require_human_approval(state: TranscriptMapReduceState) -> str:
    """Determines if human approval is required based on rules validation."""
    human_approval = state.get("human_approval", False)
    
    if human_approval:
        return "finalize"
    else:
        return "human_interrupt"


# Node 7: Finalize analysis
def finalize_analysis(state: TranscriptMapReduceState) -> TranscriptMapReduceState:
    """Final step to complete the analysis."""
    print("--- Step 7: Analysis Complete ---")
    
    return {
        **state,
        "validation_feedback": state.get("validation_feedback", "Analysis completed successfully.")
    }


# Create the graph
def create_transcript_mapreduce_graph():
    """Creates and compiles the map-reduce graph for transcript analysis."""
    
    workflow = StateGraph(TranscriptMapReduceState)
    
    workflow.add_node("extract_pdf_text", extract_pdf_text)
    workflow.add_node("chunk_document", chunk_document)
    workflow.add_node("map_phase", map_phase)
    workflow.add_node("reduce_aggregator", reduce_phase_aggregator)
    workflow.add_node("generate_summary", generate_final_summary)
    workflow.add_node("validate_rules", validate_rules)
    workflow.add_node("human_interrupt", human_interrupt)
    workflow.add_node("finalize_analysis", finalize_analysis)
    workflow.add_edge(START, "extract_pdf_text")
    workflow.add_edge("extract_pdf_text", "chunk_document")
    workflow.add_edge("chunk_document", "map_phase")
    workflow.add_edge("map_phase", "reduce_aggregator")
    workflow.add_edge("reduce_aggregator", "generate_summary")
    workflow.add_edge("generate_summary", "validate_rules")
    workflow.add_conditional_edges("validate_rules", should_require_human_approval, {
        "human_interrupt": "human_interrupt",
        "finalize": "finalize_analysis"
    })
    workflow.add_edge("human_interrupt", "finalize_analysis")
    workflow.add_edge("finalize_analysis", END)
    
    # Compile the graph with memory to allow for streaming intermediate steps.
    app = workflow.compile(checkpointer=MemorySaver())
    
    print("✅ Transcript Map-Reduce Graph compiled successfully.")
    return app

# New function to be called from the API
async def analyze_transcript(file_path: str, thread_id: str, analysis_rules: str = ""):
    """
    Main entry point to run the transcript analysis graph.
    This is an async generator that yields the state at each step.
    """
    graph = create_transcript_mapreduce_graph()
    config = {"configurable": {"thread_id": thread_id}}
      # Initialize state with rules
    initial_state = {
        "file_path": file_path,
        "analysis_rules": analysis_rules,
        "transcript_text": "",
        "chunks": [],
        "chunk_results": [],
        "aggregated_results": {},
        "final_summary": "",
        "error": "",
        "rules_validation": {},
        "human_approval": False,
        "validation_feedback": "",
        "human_review_required": False
    }
    
    async for state in graph.astream(
        initial_state,
        config=config,
        stream_mode="values"
    ):
        yield state
