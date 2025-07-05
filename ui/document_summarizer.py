import streamlit as st
import time
import io
import json
import sys
import os
from collections import Counter

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

try:
    from graphs.documentsummarygraph import create_document_summary_graph
except ImportError as e:
    st.error(f"Could not import document summary graph: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

# Import UI utilities
try:
    from utils import (
        format_file_size, 
        get_processing_status_emoji, 
        create_download_filename,
        update_session_metrics
    )
except ImportError:
    # Define fallback functions if utils import fails
    def format_file_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    def get_processing_status_emoji(stage):
        return "🔄"
    
    def create_download_filename(original_name, suffix="summary"):
        return f"{suffix}_{original_name}"
    
    def update_session_metrics():
        pass

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

def show_document_summarizer():
    """Display the document summarizer page"""
    
    # Header
    st.title("📄 Intelligent Document Summarizer")
    st.markdown("Upload your documents and get AI-powered summaries with detailed insights!")
    
    # Instructions panel
    with st.expander("📋 How to Use", expanded=False):
        st.markdown("""
        **Step-by-step process:**
        1. 📁 **Upload** your document using the file uploader
        2. ✏️ **Add instructions** (optional) for customized summaries
        3. 🚀 **Click "Process Document"** to start analysis
        4. 📊 **View results** in real-time with progress tracking
        5. 💾 **Export** your summary in multiple formats
        
        **Supported formats:** PDF, Word (.docx/.doc), Text (.txt)
        """)
    
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
        
        # Preset instruction templates
        st.markdown("**Quick Templates:**")
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            if st.button("📊 Financial Focus", use_container_width=True):
                st.session_state.instruction_template = "Focus on financial metrics, revenue, costs, and financial performance indicators."
                
            if st.button("🎯 Key Decisions", use_container_width=True):
                st.session_state.instruction_template = "Extract key decisions, recommendations, and action items from the document."
        
        with template_col2:
            if st.button("⚠️ Risk Analysis", use_container_width=True):
                st.session_state.instruction_template = "Highlight risks, challenges, and potential issues mentioned in the document."
                
            if st.button("📈 Executive Summary", use_container_width=True):
                st.session_state.instruction_template = "Create a high-level executive summary suitable for senior management."
        
        # Apply template if selected
        if 'instruction_template' in st.session_state:
            user_instruction = st.text_area(
                "📝 Custom Instructions (Optional)",
                value=st.session_state.instruction_template,
                height=100,
                key="updated_instruction"
            )
            del st.session_state.instruction_template
        
        # Process button
        process_button = st.button(
            "🚀 Process Document",
            type="primary",
            disabled=uploaded_file is None,
            use_container_width=True
        )
          # File information
        if uploaded_file is not None:
            file_size_formatted = format_file_size(uploaded_file.size)
            st.info(f"""
            **File Details:**
            - 📄 Name: {uploaded_file.name}
            - 🏷️ Type: {get_file_type(uploaded_file.name).upper()}
            - 📏 Size: {uploaded_file.size:,} bytes ({file_size_formatted})
            """)
            
            # Show file preview for text files
            if get_file_type(uploaded_file.name) == 'txt' and uploaded_file.size < 10000:  # Less than 10KB
                with st.expander("👀 File Preview", expanded=False):
                    try:
                        file_content = uploaded_file.read()
                        uploaded_file.seek(0)  # Reset file pointer
                        preview_text = file_content.decode('utf-8', errors='ignore')[:500]
                        st.text(preview_text + "..." if len(preview_text) == 500 else preview_text)
                    except Exception as e:
                        st.error(f"Could not preview file: {e}")
    
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
                    st.session_state.last_processed_file = uploaded_file.name
                    st.success("🎉 Document processing completed successfully!")
        
        # Display results
        if st.session_state.processing_complete and st.session_state.summary_result:
            st.markdown("### 📋 Document Summary")
            
            # Add summary metadata
            if 'last_processed_file' in st.session_state:
                st.caption(f"📄 Summary for: **{st.session_state.last_processed_file}** | Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📄 Summary", "💾 Export", "📊 Analytics"])
            
            with tab1:
                st.markdown(st.session_state.summary_result)
                
                # Action buttons
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("🔄 Process Another", use_container_width=True):
                        st.session_state.processing_complete = False
                        st.session_state.summary_result = ""
                        st.rerun()
                
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
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "file_type": get_file_type(uploaded_file.name) if uploaded_file else "unknown",
                        "instructions": user_instruction or "Default comprehensive summary"
                    }
                    
                    st.download_button(
                        label="📄 Export as JSON",
                        data=json.dumps(json_data, indent=2),
                        file_name=f"summary_{uploaded_file.name if uploaded_file else 'document'}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col_y:
                    # Markdown export
                    markdown_content = f"""# Document Summary

**Document:** {uploaded_file.name if uploaded_file else 'Unknown'}  
**Generated:** {time.strftime("%Y-%m-%d %H:%M:%S")}  
**Instructions:** {user_instruction or 'Default comprehensive summary'}

---

{st.session_state.summary_result}

---
*Generated by Research Agents Platform*
"""
                    
                    st.download_button(
                        label="📝 Export as Markdown",
                        data=markdown_content,
                        file_name=f"summary_{uploaded_file.name if uploaded_file else 'document'}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
            
            with tab3:
                st.markdown("### 📊 Summary Analytics")
                
                # Calculate basic analytics
                summary_text = st.session_state.summary_result
                word_count = len(summary_text.split())
                char_count = len(summary_text)
                line_count = len(summary_text.split('\n'))
                
                # Display metrics
                analytics_col1, analytics_col2, analytics_col3 = st.columns(3)
                
                with analytics_col1:
                    st.metric("📝 Word Count", f"{word_count:,}")
                
                with analytics_col2:
                    st.metric("🔤 Character Count", f"{char_count:,}")
                
                with analytics_col3:
                    st.metric("📏 Line Count", f"{line_count:,}")
                
                # Word frequency analysis (simple)
                if word_count > 0:
                    st.markdown("**📈 Most Common Words:**")
                    words = summary_text.lower().split()
                    # Filter out common words
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
                    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]
                    
                    if filtered_words:
                        from collections import Counter
                        word_freq = Counter(filtered_words).most_common(10)
                        
                        freq_data = {
                            "Word": [item[0] for item in word_freq],
                            "Frequency": [item[1] for item in word_freq]
                        }
                        
                        st.bar_chart(freq_data, x="Word", y="Frequency")

def initialize_document_summarizer_session():
    """Initialize session state for document summarizer"""
    if 'document_graph' not in st.session_state:
        st.session_state.document_graph = create_document_summary_graph()

    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

    if 'summary_result' not in st.session_state:
        st.session_state.summary_result = ""
