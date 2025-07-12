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
    from graphs.simple_analysis_graph import (
        create_simple_analysis_graph, 
        run_simple_analysis, 
        continue_analysis_with_input
    )
except ImportError as e:
    st.error(f"Could not import simple analysis graph: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

def initialize_session_state():
    """Initialize session state variables."""
    if 'simple_analysis_complete' not in st.session_state:
        st.session_state.simple_analysis_complete = False
    
    if 'simple_analysis_result' not in st.session_state:
        st.session_state.simple_analysis_result = ""
    
    if 'simple_analysis_error' not in st.session_state:
        st.session_state.simple_analysis_error = ""
    
    if 'needs_human_input' not in st.session_state:
        st.session_state.needs_human_input = False
    
    if 'missing_info' not in st.session_state:
        st.session_state.missing_info = ""
    
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = f"analysis_{int(datetime.now().timestamp())}"
    
    if 'analysis_state' not in st.session_state:
        st.session_state.analysis_state = {}

def run_analysis():
    """Run the document analysis."""
    file_path = "docs/2025/Q1/SHELL/QRAReport/q1-2025-qra-document.pdf"
    
    # Check if file exists
    if not os.path.exists(file_path):
        st.error(f"❌ File not found: {file_path}")
        return
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async def run_async_analysis():
        status_text.text("📄 Starting document analysis...")
        progress_bar.progress(20)
        
        async for state in run_simple_analysis(file_path, st.session_state.thread_id):
            # Store the state
            st.session_state.analysis_state = state
            
            if state.get("error"):
                st.session_state.simple_analysis_error = state["error"]
                status_text.text(f"❌ Error: {state['error']}")
                progress_bar.progress(100)
                return
            
            if state.get("document_text"):
                status_text.text("✅ Document text extracted")
                progress_bar.progress(40)
            
            if state.get("analysis_result"):
                status_text.text("🔍 Analysis completed")
                progress_bar.progress(70)
            
            if state.get("needs_human_input"):
                st.session_state.needs_human_input = True
                st.session_state.missing_info = state.get("missing_info", "")
                status_text.text("👤 Human input required")
                progress_bar.progress(80)
                return
            
            if state.get("final_result"):
                st.session_state.simple_analysis_result = state["final_result"]
                st.session_state.simple_analysis_complete = True
                st.session_state.needs_human_input = False
                status_text.text("✅ Analysis complete!")
                progress_bar.progress(100)
                return
    
    # Run the async analysis
    asyncio.run(run_async_analysis())
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def continue_with_human_input(human_input: str):
    """Continue analysis with human input."""
    
    # Create progress indicators
    progress_bar = st.progress(80)
    status_text = st.empty()
    
    async def run_async_continuation():
        status_text.text("🔄 Processing human input...")
        progress_bar.progress(85)
        
        async for state in continue_analysis_with_input(st.session_state.thread_id, human_input):
            # Store the state
            st.session_state.analysis_state = state
            
            if state.get("error"):
                st.session_state.simple_analysis_error = state["error"]
                status_text.text(f"❌ Error: {state['error']}")
                progress_bar.progress(100)
                return
            
            if state.get("final_result"):
                st.session_state.simple_analysis_result = state["final_result"]
                st.session_state.simple_analysis_complete = True
                st.session_state.needs_human_input = False
                status_text.text("✅ Analysis complete with human input!")
                progress_bar.progress(100)
                return
    
    # Run the async continuation
    asyncio.run(run_async_continuation())
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

def show_simple_analysis():
    """Main function to display the simple analysis page."""
    initialize_session_state()
    
    st.title("🔍 Simple Document Analysis")
    st.markdown("AI-powered analysis of Shell Q1 2025 QRA Report with human-in-the-loop capability")
    
    # Document info
    st.markdown("### 📄 Document Information")
    file_path = "docs/2025/Q1/SHELL/QRAReport/q1-2025-qra-document.pdf"
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**File:** {os.path.basename(file_path)}")
    with col2:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            st.info(f"**Size:** {size_mb:.1f} MB")
        else:
            st.error("❌ File not found")
    
    # Analysis section
    st.markdown("### 🚀 Analysis")
    
    if st.button("🔍 Start Analysis", type="primary", use_container_width=True, disabled=st.session_state.simple_analysis_complete):
        if not st.session_state.simple_analysis_complete:
            with st.spinner("Analyzing document..."):
                run_analysis()
                st.rerun()
    
    # Human input section (shown when needed)
    if st.session_state.needs_human_input:
        st.markdown("---")
        st.markdown("### 👤 Human Input Required")
        
        st.warning("⚠️ The AI analysis needs additional information to complete the analysis.")
        
        if st.session_state.missing_info:
            st.markdown("**Missing Information:**")
            st.markdown(st.session_state.missing_info)
        
        # Human input form
        with st.form("human_input_form"):
            human_input = st.text_area(
                "Please provide the missing information:",
                height=150,
                help="Add any specific details, clarifications, or additional context that would help complete the analysis."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Submit Information", type="primary", use_container_width=True):
                    if human_input.strip():
                        with st.spinner("Processing your input..."):
                            continue_with_human_input(human_input)
                            st.success("✅ Information submitted successfully!")
                            st.rerun()
                    else:
                        st.error("Please provide some information before submitting.")
            
            with col2:
                if st.form_submit_button("⏭️ Skip & Continue", use_container_width=True):
                    with st.spinner("Continuing without additional input..."):
                        continue_with_human_input("No additional information provided.")
                        st.rerun()
    
    # Results section
    if st.session_state.simple_analysis_complete and st.session_state.simple_analysis_result:
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        
        # Display the result
        st.markdown("#### 🎯 Document Analysis")
        st.markdown(st.session_state.simple_analysis_result)
        
        # Download option
        st.markdown("#### 💾 Export")
        if st.download_button(
            label="📝 Download Analysis",
            data=st.session_state.simple_analysis_result,
            file_name=f"simple_analysis_{int(datetime.now().timestamp())}.txt",
            mime="text/plain",
            use_container_width=True
        ):
            st.success("✅ Analysis downloaded!")
        
        # Reset button
        if st.button("🔄 Start New Analysis", use_container_width=True):
            # Clear session state
            st.session_state.simple_analysis_complete = False
            st.session_state.simple_analysis_result = ""
            st.session_state.simple_analysis_error = ""
            st.session_state.needs_human_input = False
            st.session_state.missing_info = ""
            st.session_state.thread_id = f"analysis_{int(datetime.now().timestamp())}"
            st.session_state.analysis_state = {}
            st.rerun()
    
    # Error section
    elif st.session_state.simple_analysis_error:
        st.markdown("---")
        st.error(f"❌ {st.session_state.simple_analysis_error}")
        
        if st.button("🔄 Try Again", use_container_width=True):
            st.session_state.simple_analysis_error = ""
            st.rerun()
    
    # Instructions
    elif not st.session_state.simple_analysis_complete and not st.session_state.needs_human_input:
        st.markdown("---")
        st.info("💡 Click 'Start Analysis' to begin analyzing the Shell Q1 2025 QRA document. The AI will automatically detect if additional human input is needed.")

if __name__ == "__main__":
    show_simple_analysis()
