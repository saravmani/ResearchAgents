import streamlit as st
import sys
import os

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(current_dir)

# Import page modules
from ui.home_page import show_home_page
from ui.document_summarizer import show_document_summarizer, initialize_document_summarizer_session
from ui.excel_data_extraction import excel_data_extraction_ui

# Configure Streamlit page
st.set_page_config(
    page_title="Research Agents Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Initialize document summarizer session state
initialize_document_summarizer_session()

def main():
    """Main Streamlit application with navigation"""
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🤖 Research Agents")
        st.markdown("---")
          # Navigation menu
        page = st.radio(
            "Navigation",
            ["Home", "Document Summarizer", "Excel Vision Extraction"],
            index=["Home", "Document Summarizer", "Excel Vision Extraction"].index(st.session_state.current_page) if st.session_state.current_page in ["Home", "Document Summarizer", "Excel Vision Extraction"] else 0
        )
        
        # Update current page
        if page != st.session_state.current_page:
            st.session_state.current_page = page
            st.rerun()
        
        st.markdown("---")
        
        # Add debug toggle in sidebar for document summarizer page
        if st.session_state.current_page == "Document Summarizer":
            st.markdown("### 🛠️ Debug Tools")
            show_debug = st.checkbox("Show debug information", value=False)
            
            if st.button("🔄 Reset Session State", help="Clear all session data"):
                keys_to_keep = ['current_page', 'document_graph']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.success("Session state reset successfully!")
                st.rerun()
                
            if st.button("📊 Show Session State", help="Display current session state"):
                st.json(dict(st.session_state))
                
            # Quick stats in sidebar for document summarizer
            if st.session_state.get('processing_complete', False):
                st.markdown("### 📈 Current Session")
                st.metric("Summary Length", f"{len(st.session_state.get('summary_result', ''))}")
                if 'last_processed_file' in st.session_state:
                    st.info(f"📄 Last file: {st.session_state.last_processed_file}")
        else:
            show_debug = False
            
        # Platform info in sidebar
        st.markdown("---")
        st.markdown("### ℹ️ Platform Info")
        st.caption("Version: 1.0.0")
        st.caption("Environment: Production")
        st.caption("Status: 🟢 Online")    # Display the selected page
    if st.session_state.current_page == "Home":
        show_home_page()
    elif st.session_state.current_page == "Document Summarizer":
        show_document_summarizer()
    elif st.session_state.current_page == "Excel Vision Extraction":
        excel_data_extraction_ui()
        
        # Debug information for document summarizer
        if show_debug and st.session_state.current_page == "Document Summarizer":
            with st.expander("🔧 Debug Information", expanded=True):
                debug_col1, debug_col2 = st.columns(2)
                
                with debug_col1:
                    st.markdown("**Session State:**")
                    st.json({
                        "processing_complete": st.session_state.get("processing_complete", False),
                        "summary_length": len(st.session_state.get("summary_result", "")),
                        "current_page": st.session_state.current_page,
                        "total_session_keys": len(st.session_state.keys()),
                        "last_processed_file": st.session_state.get("last_processed_file", "None")
                    })
                
                with debug_col2:
                    st.markdown("**Graph State:**")
                    if hasattr(st.session_state, 'document_graph'):
                        st.success("✅ Document graph initialized")
                        st.info("Graph type: DocumentSummaryGraph")
                    else:
                        st.error("❌ Document graph not found")
                    
                    st.markdown("**Environment:**")
                    st.code(f"""
Streamlit: {st.__version__}
Current Page: {st.session_state.current_page}
Working Directory: {os.getcwd()}
UI Module Path: {current_dir}
                    """)
                
                # Add a code execution area for debugging
                st.markdown("**Debug Code Execution:**")
                debug_code = st.text_area(
                    "Execute Python code (use st.session_state to access session)",
                    placeholder="# Example:\n# st.write(len(st.session_state.keys()))\n# st.write(st.session_state.current_page)",
                    height=100,
                    key="debug_code_area"
                )
                
                if st.button("🚀 Execute Debug Code") and debug_code:
                    try:
                        exec(debug_code)
                    except Exception as e:
                        st.error(f"Debug code error: {e}")
    
    # Footer
    st.markdown("---")
    
    footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])
    
    with footer_col1:
        st.markdown(
            "🤖 **Powered by LangGraph & AI** | Built with Streamlit"
        )
    
    with footer_col2:
        st.markdown(f"**Current Page:** {st.session_state.current_page}")
    
    with footer_col3:
        # Add a theme toggle (placeholder for future implementation)
        if st.button("🌙 Toggle Theme", help="Theme switching coming soon"):
            st.info("Theme switching will be available in future updates!")

if __name__ == "__main__":
    main()
