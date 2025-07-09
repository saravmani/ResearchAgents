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
    from graphs.mapreduce_graph import create_transcript_mapreduce_graph, analyze_transcript
except ImportError as e:
    st.error(f"Could not import transcript analysis graph: {e}")
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
    
    def create_download_filename(original_name, suffix="analysis"):
        return f"{suffix}_{original_name}"
    
    def update_session_metrics():
        pass

def get_file_type(filename: str) -> str:
    """Get file type from filename extension"""
    extension = filename.lower().split('.')[-1]
    file_types = {
        'pdf': 'PDF Document',
        'txt': 'Text Document',
        'docx': 'Word Document',
        'doc': 'Word Document',
    }
    return file_types.get(extension, 'Unknown')

def initialize_transcript_analysis_session():
    """Initialize session state for transcript analysis"""
    if 'transcript_analysis_graph' not in st.session_state:
        st.session_state.transcript_analysis_graph = None
    
    if 'transcript_analysis_complete' not in st.session_state:
        st.session_state.transcript_analysis_complete = False
    
    if 'transcript_analysis_result' not in st.session_state:
        st.session_state.transcript_analysis_result = ""
    
    if 'transcript_analysis_error' not in st.session_state:
        st.session_state.transcript_analysis_error = ""
    
    if 'transcript_analysis_metrics' not in st.session_state:
        st.session_state.transcript_analysis_metrics = {}

def process_transcript_file(file_path: str) -> str:
    """Process transcript file using the map-reduce graph"""
    try:
        # Initialize graph if not exists
        if st.session_state.transcript_analysis_graph is None:
            st.session_state.transcript_analysis_graph = create_transcript_mapreduce_graph()
            graph = st.session_state.transcript_analysis_graph
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        chunk_progress_container = st.empty()
        
        # Process the file
        status_text.text("📄 Starting transcript analysis...")
        progress_bar.progress(10)
        
        final_result = ""
        config = {"configurable": {"thread_id": "transcript_analysis_session"}}
        
        async def run_analysis():
            nonlocal final_result
            chunks_status = {}  # Track individual chunk progress
            
            async for state in analyze_transcript(file_path, "transcript_analysis_session"):
                # Update progress based on processing stage
                if "error" in state and state["error"]:
                    status_text.text(f"❌ Error: {state['error']}")
                    progress_bar.progress(100)
                    return f"Error processing document: {state['error']}"
                
                if "file_path" in state:
                    status_text.text("📄 PDF text extraction in progress...")
                    progress_bar.progress(20)
                
                if "transcript_text" in state and state["transcript_text"]:
                    text_length = len(state["transcript_text"])
                    status_text.text(f"✅ Text extracted! {text_length:,} characters...")
                    progress_bar.progress(30)
                
                if "chunks" in state and state["chunks"]:
                    chunk_count = len(state["chunks"])
                    status_text.text(f"📝 Document chunked into {chunk_count} pieces...")
                    progress_bar.progress(40)
                
                if "chunk_results" in state and state["chunk_results"]:
                    # Show detailed progress for each chunk
                    results_count = len(state["chunk_results"])
                    total_chunks = len(state.get("chunks", []))
                    
                    # Count successful vs failed chunks
                    successful_chunks = 0
                    failed_chunks = 0
                    for result in state["chunk_results"]:
                        if result.get("extracted_data", {}).get("error"):
                            failed_chunks += 1
                        else:
                            successful_chunks += 1
                    
                    # Display chunk progress in a nice format
                    chunk_progress_container.markdown(f"""
                    **🔍 Chunk Processing Progress:**
                    - ✅ Successful: {successful_chunks}/{total_chunks}
                    - ❌ Failed: {failed_chunks}/{total_chunks}
                    - 📊 Overall: {results_count}/{total_chunks} chunks processed
                    """)
                    
                    if failed_chunks > 0:
                        status_text.text(f"🔍 Processed {results_count}/{total_chunks} chunks (✅ {successful_chunks} success, ❌ {failed_chunks} failed)")
                    else:
                        status_text.text(f"🔍 Processed {results_count}/{total_chunks} chunks (✅ All successful)")
                    
                    # Update progress based on chunk completion
                    chunk_progress = 40 + (results_count / total_chunks) * 30  # 40-70% range
                    progress_bar.progress(min(int(chunk_progress), 70))
                
                if "aggregated_results" in state and state["aggregated_results"]:
                    status_text.text("📊 Aggregating and deduplicating results...")
                    progress_bar.progress(80)
                
                if "final_summary" in state and state["final_summary"]:
                    status_text.text("✅ Final summary generated!")
                    progress_bar.progress(100)
                    final_result = state["final_summary"]
                    
                    # Store enhanced metrics
                    chunk_metrics = []
                    if "chunk_results" in state:
                        for i, result in enumerate(state["chunk_results"]):
                            chunk_info = {
                                "chunk_number": i + 1,
                                "success": not result.get("extracted_data", {}).get("error"),
                                "metrics_count": len(result.get("extracted_data", {}).get("metrics", [])),
                                "has_guidance": bool(result.get("extracted_data", {}).get("guidance")),
                                "drivers_count": len(result.get("extracted_data", {}).get("key_drivers", [])),
                                "risks_count": len(result.get("extracted_data", {}).get("risks", []))
                            }
                            chunk_metrics.append(chunk_info)
                    
                    st.session_state.transcript_analysis_metrics = {
                        "chunks_processed": len(state.get("chunks", [])),
                        "results_aggregated": len(state.get("chunk_results", [])),
                        "text_length": len(state.get("transcript_text", "")),
                        "summary_length": len(state.get("final_summary", "")),
                        "aggregated_data": state.get("aggregated_results", {}),
                        "chunk_details": chunk_metrics
                    }
          # Run the async analysis
        import asyncio
        asyncio.run(run_analysis())
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        chunk_progress_container.empty()
        
        return final_result
        
    except Exception as e:
        st.error(f"Error processing transcript: {str(e)}")
        return f"Error processing document: {str(e)}"

def show_transcript_analysis():
    """Main function to display the transcript analysis page"""
    st.title("📊 Transcript Analysis")
    st.markdown("Extract financial insights from earning calls and transcripts using AI-powered map-reduce analysis.")
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["📁 File Browser", "📤 Upload", "📊 Results"])
    
    with tab1:
        st.markdown("### 📁 Browse Available Documents")
        
        # Document browser
        docs_path = os.path.join(parent_dir, "docs")
        if os.path.exists(docs_path):
            # Walk through directory structure
            files_found = []
            for root, dirs, files in os.walk(docs_path):
                for file in files:
                    if file.lower().endswith(('.pdf', '.txt', '.docx', '.doc')):
                        rel_path = os.path.relpath(os.path.join(root, file), parent_dir)
                        files_found.append(rel_path)
            
            if files_found:
                st.info(f"Found {len(files_found)} documents in the docs folder")
                
                # Create a selectbox for file selection
                selected_file = st.selectbox(
                    "Select a document to analyze:",
                    [""] + files_found,
                    format_func=lambda x: "Select a file..." if x == "" else os.path.basename(x)
                )
                
                if selected_file:
                    file_path = os.path.join(parent_dir, selected_file)
                    
                    # Display file information
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📄 File Type", get_file_type(selected_file))
                    with col2:
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                            st.metric("📊 File Size", format_file_size(file_size))
                    with col3:
                        st.metric("📁 Location", os.path.dirname(selected_file))
                    
                    # Process button
                    if st.button("🚀 Analyze Transcript", type="primary", use_container_width=True):
                        with st.spinner("Processing transcript..."):
                            result = process_transcript_file(file_path)
                            if result and not result.startswith("Error"):
                                st.session_state.transcript_analysis_result = result
                                st.session_state.transcript_analysis_complete = True
                                st.session_state.last_processed_transcript = os.path.basename(selected_file)
                                st.success("✅ Transcript analysis completed!")
                                st.rerun()
                            else:
                                st.session_state.transcript_analysis_error = result
                                st.error(f"❌ {result}")
            else:
                st.warning("⚠️ No supported documents found in the docs folder.")
                st.info("💡 Supported formats: PDF, TXT, DOCX, DOC")
        else:
            st.error("❌ Documents folder not found. Please create a 'docs' folder in the project root.")
    
    with tab2:
        st.markdown("### 📤 Upload New Document")
        
        uploaded_file = st.file_uploader(
            "Choose a transcript file",
            type=['pdf', 'txt', 'docx', 'doc'],
            help="Upload earnings call transcripts or financial documents"
        )
        
        if uploaded_file is not None:
            # Display file information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 File Type", get_file_type(uploaded_file.name))
            with col2:
                st.metric("📊 File Size", format_file_size(uploaded_file.size))
            with col3:
                st.metric("📝 Filename", uploaded_file.name)
            
            # Save uploaded file temporarily
            if st.button("🚀 Analyze Uploaded Transcript", type="primary", use_container_width=True):
                # Create temp directory if it doesn't exist
                temp_dir = os.path.join(parent_dir, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                # Save uploaded file
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner("Processing uploaded transcript..."):
                    result = process_transcript_file(temp_path)
                    if result and not result.startswith("Error"):
                        st.session_state.transcript_analysis_result = result
                        st.session_state.transcript_analysis_complete = True
                        st.session_state.last_processed_transcript = uploaded_file.name
                        st.success("✅ Transcript analysis completed!")
                        st.rerun()
                    else:
                        st.session_state.transcript_analysis_error = result
                        st.error(f"❌ {result}")
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    with tab3:
        st.markdown("### 📊 Analysis Results")
        
        if st.session_state.transcript_analysis_complete and st.session_state.transcript_analysis_result:
            # Display metrics
            if st.session_state.transcript_analysis_metrics:
                metrics = st.session_state.transcript_analysis_metrics
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📝 Chunks Processed", metrics.get("chunks_processed", 0))
                with col2:
                    st.metric("🔍 Results Aggregated", metrics.get("results_aggregated", 0))
                with col3:
                    st.metric("📊 Text Length", f"{metrics.get('text_length', 0):,}")
                with col4:
                    st.metric("📋 Summary Length", f"{metrics.get('summary_length', 0):,}")
              # Display the analysis result
            st.markdown("#### 🎯 Financial Analysis Summary")
            st.markdown(st.session_state.transcript_analysis_result)
            
            # Display aggregated data if available
            if st.session_state.transcript_analysis_metrics.get("aggregated_data"):
                with st.expander("📊 Detailed Extracted Data", expanded=False):
                    aggregated_data = st.session_state.transcript_analysis_metrics["aggregated_data"]
                    
                    # Show different categories
                    for category, items in aggregated_data.items():
                        if items:
                            st.markdown(f"**{category.replace('_', ' ').title()}:**")
                            if isinstance(items, list):
                                for item in items:
                                    if isinstance(item, dict):
                                        st.json(item)
                                    else:
                                        st.write(f"- {item}")
                            else:
                                st.write(items)
                            st.markdown("---")
            
            # Display chunk processing details
            if st.session_state.transcript_analysis_metrics.get("chunk_details"):
                with st.expander("🔍 Chunk Processing Details", expanded=False):
                    chunk_details = st.session_state.transcript_analysis_metrics["chunk_details"]
                    
                    # Summary statistics
                    successful_chunks = sum(1 for chunk in chunk_details if chunk["success"])
                    failed_chunks = len(chunk_details) - successful_chunks
                    total_metrics = sum(chunk["metrics_count"] for chunk in chunk_details)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Successful Chunks", successful_chunks)
                    with col2:
                        st.metric("❌ Failed Chunks", failed_chunks)
                    with col3:
                        st.metric("📊 Total Metrics Found", total_metrics)
                    
                    # Detailed chunk breakdown
                    st.markdown("**Individual Chunk Results:**")
                    for chunk in chunk_details:
                        status_icon = "✅" if chunk["success"] else "❌"
                        st.markdown(f"""
                        **Chunk {chunk['chunk_number']}** {status_icon}
                        - 📊 Metrics: {chunk['metrics_count']}
                        - 🎯 Guidance: {"Yes" if chunk['has_guidance'] else "No"}
                        - 🚀 Drivers: {chunk['drivers_count']}
                        - ⚠️ Risks: {chunk['risks_count']}
                        """)
                    
                    # Show processing efficiency
                    if len(chunk_details) > 0:
                        efficiency = (successful_chunks / len(chunk_details)) * 100
                        st.metric("🎯 Processing Efficiency", f"{efficiency:.1f}%")
            
            # Download options
            st.markdown("#### 💾 Export Options")
            col1, col2 = st.columns(2)
            
            with col1:
                # Download as text
                if st.download_button(
                    label="📝 Download Summary",
                    data=st.session_state.transcript_analysis_result,
                    file_name=f"transcript_analysis_{int(time.time())}.txt",
                    mime="text/plain",
                    use_container_width=True
                ):
                    st.success("✅ Summary downloaded!")
            
            with col2:
                # Download as JSON
                if st.session_state.transcript_analysis_metrics.get("aggregated_data"):
                    json_data = json.dumps(st.session_state.transcript_analysis_metrics["aggregated_data"], indent=2)
                    if st.download_button(
                        label="📊 Download Data (JSON)",
                        data=json_data,
                        file_name=f"transcript_data_{int(time.time())}.json",
                        mime="application/json",
                        use_container_width=True
                    ):
                        st.success("✅ Data downloaded!")
        
        elif st.session_state.transcript_analysis_error:
            st.error(f"❌ {st.session_state.transcript_analysis_error}")
        
        else:
            st.info("🔍 No analysis results yet. Please analyze a transcript first.")
            
            # Show sample files if available
            st.markdown("#### 📋 Quick Start")
            st.markdown("To get started:")
            st.markdown("1. 📁 Browse available documents in the **File Browser** tab")
            st.markdown("2. 📤 Upload a new transcript in the **Upload** tab")
            st.markdown("3. 🚀 Click **Analyze Transcript** to process the document")
            st.markdown("4. 📊 View results in this **Results** tab")
