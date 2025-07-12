import streamlit as st
import sys
import os
from datetime import datetime
from langgraph.types import Command

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from graphs.human_loop_sqlite import build_graph
except ImportError as e:
    st.error(f"Could not import human loop graph: {e}")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'analysis_started' not in st.session_state:
        st.session_state.analysis_started = False
    
    if 'needs_human_input' not in st.session_state:
        st.session_state.needs_human_input = False
    
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = f"analysis_{int(datetime.now().timestamp())}"
    
    if 'conversation_output' not in st.session_state:
        st.session_state.conversation_output = []
    
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

def run_initial_analysis():
    """Run the initial analysis."""
    app = build_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    st.session_state.conversation_output = []
    
    try:
        with st.spinner("Running analysis..."):
            for event in app.stream(
                {"messages": [("user", "Ask the user where they are, then look up the weather there")]}, 
                config, 
                stream_mode="values"
            ):
                if "messages" in event:
                    message = event["messages"][-1]
                    st.session_state.conversation_output.append(f"**{message.type}:** {message.content}")
        
        # If we reach here without interrupt, analysis is complete
        st.session_state.analysis_complete = True
        st.session_state.analysis_started = True
        
    except Exception as e:
        if "askhuman" in str(e).lower():
            st.session_state.needs_human_input = True
            st.session_state.analysis_started = True
            # Extract the question from the interrupt
            interrupt_msg = str(e)
            if "Ask the user where they are" in interrupt_msg or "location" in interrupt_msg.lower():
                st.session_state.interrupt_question = "Where are you located?"
            else:
                st.session_state.interrupt_question = "Please provide your input:"
        else:
            st.error(f"Error during analysis: {str(e)}")

def continue_with_human_input(human_input):
    """Continue analysis with human input."""
    app = build_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    try:
        with st.spinner("Processing your input..."):
            for event in app.stream(Command(resume=human_input), config, stream_mode="values"):
                if "messages" in event:
                    message = event["messages"][-1]
                    st.session_state.conversation_output.append(f"**{message.type}:** {message.content}")
        
        # Analysis completed
        st.session_state.needs_human_input = False
        st.session_state.analysis_complete = True
        
    except Exception as e:
        if "interrupt" in str(e).lower():
            st.session_state.needs_human_input = True
            # Handle another interrupt if needed
            st.session_state.interrupt_question = "Please provide additional input:"
        else:
            st.error(f"Error continuing analysis: {str(e)}")

def main():
    """Main Streamlit UI function."""
    st.set_page_config(
        page_title="Human Loop Analysis",
        page_icon="🔄",
        layout="centered"
    )
    
    initialize_session_state()
    
    st.title("🔄 Human-in-the-Loop Analysis")
    st.markdown("Simple LangGraph execution with human interrupts")
    
    # Status
    if st.session_state.analysis_complete:
        st.success("✅ Analysis Complete")
    elif st.session_state.needs_human_input:
        st.warning("⏳ Waiting for Human Input")
    elif st.session_state.analysis_started:
        st.info("🔄 Analysis Running")
    else:
        st.info("🆕 Ready to Start")
    
    # Reset button
    if st.button("🔄 Reset", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    
    # Main content
    if not st.session_state.analysis_started:
        # Start button
        st.markdown("### 🚀 Start Analysis")
        st.info("The AI will ask you for your location and then look up the weather.")
        
        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            run_initial_analysis()
            st.rerun()
    
    elif st.session_state.needs_human_input:
        # Human input required
        st.markdown("### 👤 Human Input Required")
        
        question = getattr(st.session_state, 'interrupt_question', 'Please provide your input:')
        st.warning(f"🤔 {question}")
        
        # Display conversation so far
        if st.session_state.conversation_output:
            st.markdown("#### 💬 Conversation")
            for msg in st.session_state.conversation_output:
                st.markdown(msg)
        
        # Input form
        with st.form("human_input_form"):
            human_input = st.text_input(
                "Your response:",
                placeholder="e.g., San Francisco",
                help="Enter your location or other requested information"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Submit", type="primary", use_container_width=True):
                    if human_input.strip():
                        st.session_state.conversation_output.append(f"**Human:** {human_input}")
                        continue_with_human_input(human_input.strip())
                        st.rerun()
                    else:
                        st.error("Please provide a response.")
            
            with col2:
                if st.form_submit_button("⏭️ Use Default", use_container_width=True):
                    default_response = "San Francisco"
                    st.session_state.conversation_output.append(f"**Human:** {default_response} (default)")
                    continue_with_human_input(default_response)
                    st.rerun()
    
    elif st.session_state.analysis_complete:
        # Show results
        st.markdown("### ✅ Analysis Results")
        
        if st.session_state.conversation_output:
            st.markdown("#### 📜 Complete Conversation")
            for msg in st.session_state.conversation_output:
                st.markdown(msg)
        
        # Export option
        if st.session_state.conversation_output:
            export_data = "Human Loop Analysis Report\n"
            export_data += f"Thread ID: {st.session_state.thread_id}\n"
            export_data += f"Timestamp: {datetime.now().isoformat()}\n"
            export_data += "=" * 50 + "\n\n"
            
            for msg in st.session_state.conversation_output:
                export_data += f"{msg}\n\n"
            
            st.download_button(
                label="📝 Download Conversation",
                data=export_data,
                file_name=f"analysis_{int(datetime.now().timestamp())}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    else:
        # Analysis in progress
        st.markdown("### 🔄 Analysis in Progress")
        st.info("Analysis is running...")

if __name__ == "__main__":
    main()