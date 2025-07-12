# filepath: d:\Git\ResearchAgents\graphs\simple_calculator_graph.py
import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Define the state for our simple calculator graph
class CalculatorState(TypedDict):
    a: float
    b: float
    current_sum: float
    calculation_history: List[Dict[str, Any]]
    should_continue: bool
    needs_human_input: bool
    human_response: str
    total_calculations: int
    error: str

# Node 1: Calculator node - performs addition
def calculator_node(state: CalculatorState) -> CalculatorState:
    """Perform addition calculation (a + b)."""
    print("--- Calculator Node: Performing Addition ---")
    
    try:
        a = state.get("a", 0)
        b = state.get("b", 0)
        
        # Perform the calculation
        result = a + b
        
        # Update the current sum and history
        calculation_history = state.get("calculation_history", [])
        calculation_history.append({
            "calculation": f"{a} + {b}",
            "result": result,
            "step": len(calculation_history) + 1
        })
        
        total_calculations = state.get("total_calculations", 0) + 1
        
        print(f"Calculated: {a} + {b} = {result}")
        
        return {
            **state,
            "current_sum": result,
            "calculation_history": calculation_history,
            "total_calculations": total_calculations,
            "needs_human_input": True,  # Always ask human after calculation
            "error": ""
        }
        
    except Exception as e:
        print(f"Error in calculation: {e}")
        return {
            **state,
            "error": f"Calculation error: {e}"
        }

# Node 2: Should continue node - asks human for input
def should_continue_node(state: CalculatorState) -> CalculatorState:
    """Ask human for input and decide whether to continue."""
    print("--- Should Continue Node: Requesting Human Input ---")
    
    current_sum = state.get("current_sum", 0)
    total_calculations = state.get("total_calculations", 0)
    
    print(f"Current sum: {current_sum}, Total calculations: {total_calculations}")
    
    # This node will pause execution - the UI will handle the actual human input
    return {
        **state,
        "needs_human_input": True,
        "should_continue": False  # Default to false until human responds
    }

# Node 3: Summary node - shows accumulated results
def summary_node(state: CalculatorState) -> CalculatorState:
    """Show summary of all calculations."""
    print("--- Summary Node: Displaying Results ---")
    
    calculation_history = state.get("calculation_history", [])
    total_calculations = state.get("total_calculations", 0)
    current_sum = state.get("current_sum", 0)
    
    # Create summary
    summary = f"""
=== CALCULATION SUMMARY ===
Total Calculations: {total_calculations}
Final Result: {current_sum}

Calculation History:
"""
    
    for calc in calculation_history:
        summary += f"Step {calc['step']}: {calc['calculation']} = {calc['result']}\n"
    
    print(summary)
    
    return {
        **state,
        "needs_human_input": False,
        "should_continue": False
    }

# Routing function to determine next step
def route_after_calculation(state: CalculatorState) -> str:
    """Route after calculation based on human input needs."""
    if state.get("needs_human_input", False):
        return "should_continue"
    else:
        return "summary"

def route_after_human_input(state: CalculatorState) -> str:
    """Route after human input based on their response."""
    should_continue = state.get("should_continue", False)
    human_response = state.get("human_response", "").lower()
    
    # Check if human wants to continue
    if should_continue or "yes" in human_response or "continue" in human_response:
        return "calculator"
    else:
        return "summary"

# Create the graph
def create_calculator_graph():
    """Create and compile the calculator graph."""
    
    workflow = StateGraph(CalculatorState)
    
    # Add nodes
    workflow.add_node("calculator", calculator_node)
    workflow.add_node("should_continue", should_continue_node)
    workflow.add_node("summary", summary_node)
    
    # Add edges
    workflow.add_edge(START, "calculator")
    workflow.add_conditional_edges("calculator", route_after_calculation, {
        "should_continue": "should_continue",
        "summary": "summary"
    })
    workflow.add_conditional_edges("should_continue", route_after_human_input, {
        "calculator": "calculator",
        "summary": "summary"
    })
    workflow.add_edge("summary", END)
    
    # Compile with memory
    app = workflow.compile(checkpointer=MemorySaver())
    
    print("✅ Calculator Graph compiled successfully")
    return app

# Main function to run calculator
async def run_calculator(a: float, b: float, thread_id: str = "calculator"):
    """Run the calculator graph."""
    graph = create_calculator_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "a": a,
        "b": b,
        "current_sum": 0.0,
        "calculation_history": [],
        "should_continue": False,
        "needs_human_input": False,
        "human_response": "",
        "total_calculations": 0,
        "error": ""
    }
    
    async for state in graph.astream(initial_state, config=config, stream_mode="values"):
        yield state

# Function to continue with human input
async def continue_calculator_with_input(thread_id: str, human_response: str, new_a: float = None, new_b: float = None):
    """Continue calculator with human-provided input."""
    graph = create_calculator_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get the current state
    current_state = await graph.aget_state(config)
    
    if current_state and current_state.values:
        # Determine if human wants to continue
        should_continue = ("yes" in human_response.lower() or 
                         "continue" in human_response.lower() or
                         "y" in human_response.lower())
        
        # Update state with human input
        updated_state = {
            **current_state.values,
            "human_response": human_response,
            "should_continue": should_continue,
            "needs_human_input": False
        }
        
        # If continuing with new values, update a and b
        if should_continue and new_a is not None and new_b is not None:
            updated_state["a"] = new_a
            updated_state["b"] = new_b
        
        # Continue the graph execution
        async for state in graph.astream(updated_state, config=config, stream_mode="values"):
            yield state
    else:
        yield {"error": "No previous state found for thread ID: " + thread_id}

# Function to get current state (useful for UI)
async def get_calculator_state(thread_id: str):
    """Get the current state of the calculator."""
    graph = create_calculator_graph()
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state = await graph.aget_state(config)
        if current_state and current_state.values:
            return current_state.values
        else:
            return {"error": "No state found"}
    except Exception as e:
        return {"error": f"Failed to get state: {e}"}
