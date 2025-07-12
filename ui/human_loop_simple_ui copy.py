import streamlit as st
import sys
import os
from datetime import datetime
import uuid
import io
import contextlib

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from graphs.human_loop_sqlite import build_graph, initiate_analysis, continue_with_human_input, app
except ImportError as e:
    st.error(f"Could not import human loop graph: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = False
    
    if 'needs_human_input' not in st.session_state:
        st.session_state.needs_human_input = False
    
    if 'current_thread_id' not in st.session_state:
        st.session_state.current_thread_id = ""
    
    if 'conversation_output' not in st.session_state:
        st.session_state.conversation_output = []
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    
    if 'waiting_for_input' not in st.session_state:
        st.session_state.waiting_for_input = False

def capture_output(func, *args, **kwargs):
    """Capture printed output from a function."""
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        try:
            result = func(*args, **kwargs)
            output = output_buffer.getvalue()
            return result, output
        except Exception as e:
            output = output_buffer.getvalue()
            return None, f"{output}\nError: {str(e)}"

def run_initial_analysis():
    """Run the initial analysis."""
    thread_id = st.session_state.current_thread_id
    
    # Build the graph if app is None
    if app is None:
        with st.spinner("Building graph..."):
            build_graph()
    
    # Capture output from the analysis
    with st.spinner("Running analysis..."):
        try:
            result, output = capture_output(initiate_analysis, thread_id)
            
            if output:
                st.session_state.conversation_output.append(f"**Analysis Output:**\n```\n{output}\n```")
            
            # Check if we need human input (this is a simple check based on output)
            if "Asking human for input" in output or "interrupt" in output.lower():
                st.session_state.needs_human_input = True
                st.session_state.waiting_for_input = True
            else:
                st.session_state.analysis_complete = True
            
            st.session_state.analysis_started = True
            
        except Exception as e:
            st.error(f"Error during analysis: {str(e)}")
            st.session_state.conversation_output.append(f"**Error:** {str(e)}")

def continue_analysis_with_input(human_input):
    """Continue analysis with human input."""
    thread_id = st.session_state.current_thread_id
    
    with st.spinner("Processing your input..."):
        try:
            # Add human input to conversation
            st.session_state.conversation_output.append(f"**Your Input:** {human_input}")
            
            result, output = capture_output(continue_with_human_input, thread_id, human_input)
            
            if output:
                st.session_state.conversation_output.append(f"**Continued Analysis:**\n```\n{output}\n```")
            
            # Check if we need more human input
            if "Asking human for input" in output or "interrupt" in output.lower():
                st.session_state.needs_human_input = True
                st.session_state.waiting_for_input = True
            else:
                st.session_state.needs_human_input = False
                st.session_state.waiting_for_input = False
                st.session_state.analysis_complete = True
            
        except Exception as e:
            st.error(f"Error continuing analysis: {str(e)}")
            st.session_state.conversation_output.append(f"**Error:** {str(e)}")
            st.session_state.needs_human_input = False
            st.session_state.waiting_for_input = False

def main():
    """Main Streamlit UI function."""
    st.set_page_config(
        page_title="Human Loop Analysis",
        page_icon="🔄",
        layout="centered"
    )
    
    initialize_session_state()
    
    st.title("🔄 Human-in-the-Loop Analysis")    
    
    # Status and controls at the top
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.analysis_complete:
            st.success("✅ Analysis Complete")
        elif st.session_state.waiting_for_input:
            st.warning("⏳ Waiting for Input")
        elif st.session_state.analysis_started:
            st.info("🔄 Analysis Running")
        else:
            st.info("🆕 Ready to Start")
    
    with col2:
        if not st.session_state.analysis_started:
            # Set default thread ID if not set
            if not st.session_state.current_thread_id:
                st.session_state.current_thread_id = f"analysis_{int(datetime.now().timestamp())}"
        else:
            st.caption(f"Thread: `{st.session_state.current_thread_id[-8:]}...`")
    
    with col3:
        if st.button("🔄 Reset", use_container_width=True):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
      # Main content area
    if not st.session_state.analysis_started:      
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 Start Analysis", 
                type="primary", 
                use_container_width=True
            ):
                run_initial_analysis()
                st.rerun()
    
    elif st.session_state.waiting_for_input:
        # Waiting for human input
        st.markdown("### 👤 Human Input Required")
        
        st.warning("⚠️ The AI agent needs your input to continue the analysis.")
        
        # Display conversation so far
        if st.session_state.conversation_output:
            st.markdown("#### 💬 Conversation History")
            for message in st.session_state.conversation_output:
                st.markdown(message)
        
        # Human input form
        st.markdown("#### ✏️ Your Response")
        
        with st.form("human_input_form", clear_on_submit=True):
            human_input = st.text_area(
                "Please provide your response:",
                placeholder="Enter your response here (e.g., your location if asked)...",
                height=100,
                help="This input will be sent to the AI agent to continue the analysis"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button(
                    "✅ Submit Response", 
                    type="primary", 
                    use_container_width=True
                )
            
            with col2:
                skip_button = st.form_submit_button(
                    "⏭️ Skip (Use Default)", 
                    use_container_width=True
                )
            
            if submit_button:
                if human_input.strip():
                    continue_analysis_with_input(human_input.strip())
                    st.rerun()
                else:
                    st.error("Please provide a response before submitting.")
            
            if skip_button:
                # Use a default response
                default_response = "San Francisco"
                st.info(f"Using default response: {default_response}")
                continue_analysis_with_input(default_response)
                st.rerun()
    
    elif st.session_state.analysis_complete:
        # Analysis is complete
        st.markdown("### ✅ Analysis Complete")
        
        st.success("🎉 The analysis has been completed successfully!")
        
        # Display full conversation
        if st.session_state.conversation_output:
            st.markdown("#### 📜 Complete Conversation")
            
            for i, message in enumerate(st.session_state.conversation_output):
                with st.expander(f"Message {i+1}", expanded=True):
                    st.markdown(message)
        
        # Summary
        st.markdown("#### 📊 Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Thread ID", st.session_state.current_thread_id[-8:] + "...")
        with col2:
            st.metric("Messages", len(st.session_state.conversation_output))
        with col3:
            human_messages = len([msg for msg in st.session_state.conversation_output if "Your Input:" in msg])
            st.metric("Human Inputs", human_messages)
        
        # Export option
        st.markdown("#### 💾 Export Conversation")
        export_data = f"Human Loop Analysis Report\n"
        export_data += f"Thread ID: {st.session_state.current_thread_id}\n"
        export_data += f"Timestamp: {datetime.now().isoformat()}\n"
        export_data += "=" * 50 + "\n\n"
        
        for i, message in enumerate(st.session_state.conversation_output):
            export_data += f"{message}\n\n"
        
        st.download_button(
            label="📝 Download Conversation",
            data=export_data,
            file_name=f"human_loop_analysis_{int(datetime.now().timestamp())}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    else:
        # Analysis is running
        st.markdown("### 🔄 Analysis in Progress")
        
        with st.spinner("Analysis is running..."):
            st.info("Please wait while the analysis completes...")
        
        # Display any output so far
        if st.session_state.conversation_output:
            st.markdown("#### 💬 Progress")
            for message in st.session_state.conversation_output:
                st.markdown(message)
    
     

if __name__ == "__main__":
    main()
