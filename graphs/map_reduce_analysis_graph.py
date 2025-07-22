from typing import TypedDict, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
import os
import asyncio

# --- State Definition ---
class MapReduceState(TypedDict):
    document: str
    prompts: List[str]
    # The 'mapped_results' will be populated by the parallel mapper node all at once.
    mapped_results: List[str]
    final_summary: str
    status: str  # To hold real-time status updates
    error: str

# --- Prompts ---
PROMPT_DICT = {
    "total_revenue": "What is the total revenue mentioned in the document? Provide only the number.",
    "financial_highlights": "Summarize the key financial highlights in bullet points.",
    "risks_and_outlook": "What are the main risks and the outlook for the next quarter?",
}

# --- Model Initialization ---
# Using a mock model for predictability, but can be swapped with a real one.
# model = init_chat_model("openai:gpt-3.5-turbo", temperature=0)
# For demonstration, we'll use a simple function to simulate model behavior
def get_mock_response(prompt: str, document: str) -> str:
    if "total revenue" in prompt.lower():
        return "$5.2 million"
    if "financial highlights" in prompt.lower():
        return "- Total Revenue: $5.2 million\n- Net Profit: $1.2 million\n- EPS: $0.25"
    if "risks and outlook" in prompt.lower():
        return "The main risk is supply chain disruption. The outlook for Q3 is a projected revenue of $5.5 million."
    return "Could not find relevant information."


# --- Graph Nodes ---
async def parallel_mapper_node(state: MapReduceState) -> MapReduceState:
    """
    Maps all prompts to the document in parallel and gets a result for each.
    """
    document = state["document"]
    prompts = state["prompts"]
    
    print(f"--- Mapping {len(prompts)} prompts in parallel ---")

    # Create a coroutine for each prompt
    async def get_response_for_prompt(prompt: str):
        # In a real scenario, you would make an async call to your model
        # await model.ainvoke(...)
        # For this example, we simulate an async operation
        await asyncio.sleep(0.1) # Simulate network latency
        response = get_mock_response(prompt, document)
        return f"**{prompt}**:\n{response}"

    # Gather all results concurrently
    tasks = [get_response_for_prompt(p) for p in prompts]
    mapped_results = await asyncio.gather(*tasks)
    
    return {
        "mapped_results": mapped_results,
        "status": f"Successfully mapped all {len(prompts)} prompts."
    }

def reduce_node(state: MapReduceState) -> MapReduceState:
    """Aggregates the mapped results into a final summary."""
    print("--- Reducing mapped results ---")
    mapped_results = state["mapped_results"]
    
    final_summary = "## Financial Analysis Report\n\n"
    final_summary += "\n\n---\n\n".join(mapped_results)
    
    return {
        "final_summary": final_summary,
        "status": "Analysis complete. Final summary generated."
    }

# --- Graph Definition ---
def create_map_reduce_graph():
    """Creates and compiles the map-reduce graph."""
    workflow = StateGraph(MapReduceState)

    # Add nodes for parallel mapping and reduction
    workflow.add_node("parallel_mapper", parallel_mapper_node)
    workflow.add_node("reduce_node", reduce_node)

    # Define the simple, linear graph flow
    workflow.add_edge(START, "parallel_mapper")
    workflow.add_edge("parallel_mapper", "reduce_node")
    workflow.add_edge("reduce_node", END)
    
    # Use a file-based checkpointer for better async support
    db_path = os.path.join(os.getcwd(), "checkpoints", "map_reduce_checkpoints.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    memory = SqliteSaver.from_conn_string(db_path)
    
    graph = workflow.compile(checkpointer=MemorySaver())
    
    print("✅ Map-Reduce Graph compiled successfully")
    return graph

# --- Graph Runner ---
async def run_map_reduce_analysis(doc_path: str, thread_id: str):
    """Runs the map-reduce analysis on the given document."""
    graph = create_map_reduce_graph()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        with open(doc_path, 'r') as f:
            document_content = f.read()
    except FileNotFoundError:
        yield {"error": f"File not found at {doc_path}"}
        return

    initial_state = {
        "document": document_content,
        "prompts": list(PROMPT_DICT.values()),
        "mapped_results": [],
        "status": "Starting analysis...",
    }

    # Stream the graph execution. The graph itself now handles the parallel mapping.
    async for output in graph.astream(initial_state, config, stream_mode="values"):
        yield output
