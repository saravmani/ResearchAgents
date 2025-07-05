import streamlit as st
import time
import io
from graphs.documentsummarygraph import create_document_summary_graph
from typing import Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Document Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'document_graph' not in st.session_state:
    st.session_state.document_graph = create_document_summary_graph()

if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

if 'summary_result' not in st.session_state:
    st.session_state.summary_result = ""

def get_file_type(filename: str) -> str:
    """Extract file type from filename"""
    if filename.lower().endswith('.pdf'):
        return 'pdf'
    elif filename.lower().endswith(('.docx', '.doc')):
        return 'docx'
    elif filename.lower().endswith('.txt'):
        return 'txt'
    else:
        return 'unknown'

def process_document_with_progress(uploaded_file, user_instruction: str = ""):
    """Process document with progress tracking"""
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Initialize
        status_text.text("🚀 Initializing document processing...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # Read file content
        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = get_file_type(file_name)
        
        # Step 2: Setup graph execution
        status_text.text("📋 Setting up processing pipeline...")
        progress_bar.progress(20)
        time.sleep(0.5)
        
        config = {"configurable": {"thread_id": f"doc_session_{int(time.time())}"}}
        
        # Step 3: Start processing
        status_text.text("🔍 Parsing document content...")
        progress_bar.progress(30)
        
        final_result = ""
        current_stage = ""
        
        # Run the document processing graph
        for state in st.session_state.document_graph.stream(
            {
                "messages": [("user", user_instruction or "Please provide a comprehensive summary")],
                "file_content": file_content,
                "file_name": file_name,
                "file_type": file_type
            }, 
            config,
            stream_mode="values"
        ):
            # Update progress based on processing stage
            processing_stage = state.get("processing_stage", "")
            
            if processing_stage == "initialized":
                status_text.text("📝 Document loaded successfully...")
                progress_bar.progress(40)
                
            elif processing_stage == "parsed":
                parsed_length = len(state.get("parsed_text", ""))
                status_text.text(f"✅ Document parsed! Extracted {parsed_length:,} characters...")
                progress_bar.progress(60)
                time.sleep(0.5)
                
            elif processing_stage == "completed":
                status_text.text("🤖 Generating intelligent summary...")
                progress_bar.progress(80)
                time.sleep(0.5)
                
            elif processing_stage in ["parse_error", "summary_error"]:
                error_msg = state.get("error_message", "Unknown error")
                status_text.text(f"❌ Error: {error_msg}")
                progress_bar.progress(100)
                return f"Error processing document: {error_msg}"
            
            # Get final result from messages
            if "messages" in state:
                messages = state["messages"]
                for msg in reversed(messages):
                    if (hasattr(msg, 'content') and 
                        msg.content and 
                        hasattr(msg, 'type') and 
                        msg.type == 'ai'):
                        final_result = msg.content
                        break
        
        # Step 4: Complete
        status_text.text("✅ Document summary completed!")
        progress_bar.progress(100)
        time.sleep(0.5)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return final_result
        
    except Exception as e:
        status_text.text(f"❌ Error: {str(e)}")
        progress_bar.progress(100)
        return f"Error processing document: {str(e)}"

def main():
    """Main Streamlit application"""
    
    # Header
    st.title("📄 Intelligent Document Summarizer")
    st.markdown("Upload your documents and get AI-powered summaries with detailed insights!")
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        **Supported File Types:**
        - 📑 PDF files (.pdf)
        - 📝 Word documents (.docx, .doc)
        - 📄 Text files (.txt)
        
        **Features:**
        - 🤖 AI-powered parsing
        - 📊 Intelligent summarization
        - 🔍 Key insights extraction
        - 📈 Progress tracking
        
        **How to use:**
        1. Upload your document
        2. Add custom instructions (optional)
        3. Click "Process Document"
        4. Get your summary!
        """)
        
        st.header("⚙️ Settings")
        show_debug = st.checkbox("Show debug information", value=False)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📤 Upload Document")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a document to summarize",
            type=['pdf', 'docx', 'doc', 'txt'],
            help="Upload PDF, Word, or text documents for AI-powered summarization"
        )
        
        # Custom instructions
        user_instruction = st.text_area(
            "📝 Custom Instructions (Optional)",
            placeholder="Enter specific instructions for the summary (e.g., 'Focus on financial data', 'Extract key decisions', 'Highlight risks')",
            height=100
        )
        
        # Process button
        process_button = st.button(
            "🚀 Process Document",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True
        )
        
        # File information
        if uploaded_file is not None:
            st.info(f"""
            **File Details:**
            - Name: {uploaded_file.name}
            - Type: {get_file_type(uploaded_file.name).upper()}
            - Size: {uploaded_file.size:,} bytes
            """)
    
    with col2:
        st.header("📊 Summary Results")
        
        # Processing area
        if process_button and uploaded_file is not None:
            st.session_state.processing_complete = False
            
            with st.container():
                # Process the document
                result = process_document_with_progress(uploaded_file, user_instruction)
                
                if result:
                    st.session_state.summary_result = result
                    st.session_state.processing_complete = True
        
        # Display results
        if st.session_state.processing_complete and st.session_state.summary_result:
            st.markdown("### 📋 Document Summary")
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["📄 Summary", "💾 Export"])
            
            with tab1:
                st.markdown(st.session_state.summary_result)
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("🔄 Process Another", use_container_width=True):
                        st.session_state.processing_complete = False
                        st.session_state.summary_result = ""
                        st.experimental_rerun()
                
                with col_b:
                    if st.button("📋 Copy Summary", use_container_width=True):
                        st.code(st.session_state.summary_result, language=None)
                
                with col_c:
                    # Download button
                    st.download_button(
                        label="💾 Download Summary",
                        data=st.session_state.summary_result,
                        file_name=f"summary_{uploaded_file.name if uploaded_file else 'document'}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            with tab2:
                st.markdown("### 💾 Export Options")
                
                # Text format
                st.text_area(
                    "Plain Text Summary",
                    value=st.session_state.summary_result,
                    height=300,
                    help="Copy this text for use in other applications"
                )
                
                # Export formats
                col_x, col_y = st.columns(2)
                
                with col_x:
                    # JSON export
                    json_data = {
                        "document_name": uploaded_file.name if uploaded_file else "document",
                        "summary": st.session_state.summary_result,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.download_button(
                        label="📄 Export as JSON",
                        data=str(json_data),
                        file_name=f"summary_{uploaded_file.name if uploaded_file else 'document'}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col_y:
                    # Markdown export
                    markdown_content = f"""# Document Summary
                    
**Document:** {uploaded_file.name if uploaded_file else 'Unknown'}
**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S")}

---

{st.session_state.summary_result}
"""
                    
                    st.download_button(
                        label="📝 Export as Markdown",
                        data=markdown_content,
                        file_name=f"summary_{uploaded_file.name if uploaded_file else 'document'}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
    
    # Debug information
    if show_debug and st.session_state.processing_complete:
        with st.expander("🔧 Debug Information"):
            st.json({
                "processing_complete": st.session_state.processing_complete,
                "summary_length": len(st.session_state.summary_result),
                "file_info": {
                    "name": uploaded_file.name if uploaded_file else None,
                    "type": get_file_type(uploaded_file.name) if uploaded_file else None,
                    "size": uploaded_file.size if uploaded_file else None
                }
            })
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🤖 **Powered by LangGraph & AI** | Built with Streamlit | "
        "Upload documents to get intelligent summaries with key insights!"
    )

if __name__ == "__main__":
    main()
