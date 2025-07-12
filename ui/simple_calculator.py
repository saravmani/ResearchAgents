# filepath: d:\Git\ResearchAgents\ui\simple_calculator.py
import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from graphs.simple_calculator_graph import (
        create_calculator_graph, 
        run_calculator, 
        continue_calculator_with_input,
        get_calculator_state
    )
except ImportError as e:
    st.error(f"Could not import calculator graph: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'calculator_complete' not in st.session_state:
        st.session_state.calculator_complete = False
    
    if 'calculator_result' not in st.session_state:
        st.session_state.calculator_result = {}
    
    if 'calculator_error' not in st.session_state:
        st.session_state.calculator_error = ""
    
    if 'needs_human_input' not in st.session_state:
        st.session_state.needs_human_input = False
    
    if 'calculator_thread_id' not in st.session_state:
        st.session_state.calculator_thread_id = f"calc_{int(datetime.now().timestamp())}"
    
    if 'calculator_state' not in st.session_state:
        st.session_state.calculator_state = {}
    
    if 'calculation_history' not in st.session_state:
        st.session_state.calculation_history = []

def run_calculation(a: float, b: float):
    """Run the calculator analysis."""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def run_async_calculation():
        status_text.text("🧮 Starting calculation...")
        progress_bar.progress(20)
        
        async for state in run_calculator(a, b, st.session_state.calculator_thread_id):
            # Store the state
            st.session_state.calculator_state = state
            
            if state.get("error"):
                st.session_state.calculator_error = state["error"]
                status_text.text(f"❌ Error: {state['error']}")
                progress_bar.progress(100)
                return
            
            if state.get("current_sum") is not None:
                status_text.text(f"✅ Calculation: {a} + {b} = {state.get('current_sum')}")
                progress_bar.progress(60)
            
            if state.get("needs_human_input"):
                st.session_state.needs_human_input = True
                st.session_state.calculation_history = state.get("calculation_history", [])
                status_text.text("👤 Human input required")
                progress_bar.progress(80)
                return
            
            if not state.get("needs_human_input") and state.get("calculation_history"):
                st.session_state.calculator_result = state
                st.session_state.calculator_complete = True
                st.session_state.needs_human_input = False
                st.session_state.calculation_history = state.get("calculation_history", [])
                status_text.text("✅ Calculation complete!")
                progress_bar.progress(100)
                return
    
    # Run the async calculation
    asyncio.run(run_async_calculation())
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def continue_with_human_input(human_response: str, new_a: float = None, new_b: float = None):
    """Continue calculation with human input."""
    
    # Create progress indicators
    progress_bar = st.progress(80)
    status_text = st.empty()
    
    async def run_async_continuation():
        status_text.text("🔄 Processing human input...")
        progress_bar.progress(85)
        
        async for state in continue_calculator_with_input(
            st.session_state.calculator_thread_id, 
            human_response, 
            new_a, 
            new_b
        ):
            # Store the state
            st.session_state.calculator_state = state
            
            if state.get("error"):
                st.session_state.calculator_error = state["error"]
                status_text.text(f"❌ Error: {state['error']}")
                progress_bar.progress(100)
                return
            
            if state.get("current_sum") is not None and not state.get("needs_human_input"):
                st.session_state.calculator_result = state
                st.session_state.calculator_complete = True
                st.session_state.needs_human_input = False
                st.session_state.calculation_history = state.get("calculation_history", [])
                status_text.text("✅ Calculation complete!")
                progress_bar.progress(100)
                return
            
            if state.get("needs_human_input"):
                st.session_state.needs_human_input = True
                st.session_state.calculation_history = state.get("calculation_history", [])
                status_text.text("👤 Additional human input required")
                progress_bar.progress(80)
                return
    
    # Run the async continuation
    asyncio.run(run_async_continuation())
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def show_simple_calculator():
    """Main function to display the simple calculator page."""
    initialize_session_state()
    
    st.title("🧮 Simple Calculator with Human Interrupts")
    st.markdown("A LangGraph demonstration with human-in-the-loop capability (No LLM calls)")
    
    # Calculator input section
    st.markdown("### 🔢 Calculator Input")
    
    col1, col2 = st.columns(2)
    with col1:
        a = st.number_input("Enter first number (a):", value=5.0, step=1.0, key="input_a")
    with col2:
        b = st.number_input("Enter second number (b):", value=3.0, step=1.0, key="input_b")
    
    # Start calculation button
    if st.button("🚀 Start Calculation", type="primary", use_container_width=True, 
                disabled=st.session_state.calculator_complete):
        if not st.session_state.calculator_complete:
            with st.spinner("Performing calculation..."):
                run_calculation(a, b)
                st.rerun()
    
    # Show current calculation history if available
    if st.session_state.calculation_history:
        st.markdown("---")
        st.markdown("### 📊 Calculation History")
        
        for calc in st.session_state.calculation_history:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.info(f"Step {calc['step']}")
            with col2:
                st.code(f"{calc['calculation']} = {calc['result']}")
            with col3:
                st.success(f"✅ {calc['result']}")
    
    # Human input section (shown when needed)
    if st.session_state.needs_human_input:
        st.markdown("---")
        st.markdown("### 👤 Human Input Required")
        
        current_state = st.session_state.calculator_state
        current_sum = current_state.get("current_sum", 0)
        total_calculations = current_state.get("total_calculations", 0)
        
        st.info(f"Current result: **{current_sum}** (after {total_calculations} calculation(s))")
        st.warning("⚠️ Do you want to continue with another calculation?")
        
        # Human input form
        with st.form("human_input_form"):
            st.markdown("**Continue with another calculation?**")
            
            col1, col2 = st.columns(2)
            with col1:
                continue_choice = st.radio(
                    "Your choice:",
                    ["Yes, continue", "No, show summary"],
                    key="continue_choice"
                )
            
            with col2:
                if continue_choice == "Yes, continue":
                    st.markdown("**New calculation values:**")
                    new_a = st.number_input("New first number (a):", value=1.0, step=1.0, key="new_a")
                    new_b = st.number_input("New second number (b):", value=1.0, step=1.0, key="new_b")
                else:
                    new_a = None
                    new_b = None
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Submit Choice", type="primary", use_container_width=True):
                    human_response = "yes" if continue_choice == "Yes, continue" else "no"
                    with st.spinner("Processing your choice..."):
                        continue_with_human_input(human_response, new_a, new_b)
                        st.success("✅ Choice submitted successfully!")
                        st.rerun()
            
            with col2:
                if st.form_submit_button("🛑 Stop Calculation", use_container_width=True):
                    with st.spinner("Finalizing calculation..."):
                        continue_with_human_input("no")
                        st.rerun()
    
    # Results section
    if st.session_state.calculator_complete and st.session_state.calculator_result:
        st.markdown("---")
        st.markdown("### 📊 Final Summary")
        
        result = st.session_state.calculator_result
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Result", f"{result.get('current_sum', 0)}")
        with col2:
            st.metric("Total Calculations", result.get('total_calculations', 0))
        with col3:
            st.metric("Thread ID", st.session_state.calculator_thread_id[-6:])
        
        # Detailed history
        st.markdown("#### 📈 Complete Calculation History")
        calculation_history = result.get("calculation_history", [])
        
        if calculation_history:
            for i, calc in enumerate(calculation_history):
                with st.expander(f"Step {calc['step']}: {calc['calculation']}", expanded=(i == len(calculation_history)-1)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.code(f"Calculation: {calc['calculation']}")
                    with col2:
                        st.code(f"Result: {calc['result']}")
        
        # Export option
        st.markdown("#### 💾 Export")
        export_data = f"""Calculator Summary
Thread ID: {st.session_state.calculator_thread_id}
Final Result: {result.get('current_sum', 0)}
Total Calculations: {result.get('total_calculations', 0)}

Calculation History:
"""
        for calc in calculation_history:
            export_data += f"Step {calc['step']}: {calc['calculation']} = {calc['result']}\n"
        
        if st.download_button(
            label="📝 Download Summary",
            data=export_data,
            file_name=f"calculator_summary_{int(datetime.now().timestamp())}.txt",
            mime="text/plain",
            use_container_width=True
        ):
            st.success("✅ Summary downloaded!")
        
        # Reset button
        if st.button("🔄 Start New Calculation", use_container_width=True):
            # Clear session state
            st.session_state.calculator_complete = False
            st.session_state.calculator_result = {}
            st.session_state.calculator_error = ""
            st.session_state.needs_human_input = False
            st.session_state.calculator_thread_id = f"calc_{int(datetime.now().timestamp())}"
            st.session_state.calculator_state = {}
            st.session_state.calculation_history = []
            st.rerun()
    
    # Error section
    elif st.session_state.calculator_error:
        st.markdown("---")
        st.error(f"❌ {st.session_state.calculator_error}")
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.calculator_error = ""
            st.rerun()
    
    # Instructions
    elif not st.session_state.calculator_complete and not st.session_state.needs_human_input:
        st.markdown("---")
        st.info("💡 Enter two numbers and click 'Start Calculation'. The system will perform the addition and ask if you want to continue with more calculations.")
        
        # Debug section
        with st.expander("🔧 Debug Information", expanded=False):
            st.markdown("**Current Session State:**")
            debug_info = {
                "Thread ID": st.session_state.calculator_thread_id,
                "Calculator Complete": st.session_state.calculator_complete,
                "Needs Human Input": st.session_state.needs_human_input,
                "Has Error": bool(st.session_state.calculator_error),
                "History Length": len(st.session_state.calculation_history)
            }
            st.json(debug_info)

if __name__ == "__main__":
    show_simple_calculator()
