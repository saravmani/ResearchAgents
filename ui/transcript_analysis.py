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
    
    if 'transcript_analysis_needs_review' not in st.session_state:
        st.session_state.transcript_analysis_needs_review = False
    
    if 'transcript_analysis_pending_review' not in st.session_state:
        st.session_state.transcript_analysis_pending_review = {}
    
    if 'transcript_analysis_validation' not in st.session_state:
        st.session_state.transcript_analysis_validation = {}
    
    if 'transcript_analysis_rules' not in st.session_state:
        st.session_state.transcript_analysis_rules = """Rules for financial transcript analysis:
1. Revenue figures must be clearly stated with period
2. EPS data should include comparison to previous period
3. Guidance statements must be explicitly mentioned
4. Risk factors should be specific and actionable
5. Management tone assessment should be objective"""

def process_transcript_file(file_path: str, analysis_rules: str = "") -> str:
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
            
            async for state in analyze_transcript(file_path, "transcript_analysis_session", analysis_rules):
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
                  # Check for human review requirement
                if "human_review_required" in state and state["human_review_required"]:
                    status_text.text("👤 Human review required - please check below...")
                    progress_bar.progress(90)
                    
                    # Store the state for human review
                    st.session_state.transcript_analysis_pending_review = {
                        "validation_feedback": state["validation_feedback"],
                        "rules_validation": state.get("rules_validation", {}),
                        "summary": state.get("final_summary", ""),
                        "aggregated_data": state.get("aggregated_results", {}),
                        "full_state": state
                    }
                    
                    st.session_state.transcript_analysis_needs_review = True
                    final_result = "PENDING_REVIEW"
                    return
                
                # Check for rules validation
                if "rules_validation" in state and state["rules_validation"]:
                    rules_validation = state["rules_validation"]
                    if not rules_validation.get("overall_satisfaction", True):
                        status_text.text("⚠️ Rules validation failed - human review required...")
                        progress_bar.progress(85)
                        
                        # Store validation results for UI display
                        st.session_state.transcript_analysis_validation = rules_validation
                    else:
                        status_text.text("✅ Rules validation passed!")
                        progress_bar.progress(90)
                
                # Check for validation feedback without human review required
                if "validation_feedback" in state and state["validation_feedback"] and not state.get("human_review_required", False):
                    status_text.text("✅ Validation completed!")
                    progress_bar.progress(95)
                
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
                        "chunk_details": chunk_metrics,
                        "rules_validation": state.get("rules_validation", {}),
                        "validation_feedback": state.get("validation_feedback", "")
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
    # Initialize session state
    initialize_transcript_analysis_session()
    
    st.title("📊 Transcript Analysis")
    st.markdown("Extract financial insights from earning calls and transcripts using AI-powered map-reduce analysis.")    # Rules section
    st.markdown("### 📋 Analysis Rules")
    rules_text = st.text_area(
        "Define validation rules for the analysis (optional):",
        value=st.session_state.get('transcript_analysis_rules', """Rules for financial transcript analysis:
1. Revenue figures must be clearly stated with period
2. EPS data should include comparison to previous period
3. Guidance statements must be explicitly mentioned
4. Risk factors should be specific and actionable
5. Management tone assessment should be objective"""),
        height=150,
        help="Define rules that the analysis should follow. If these rules are not satisfied, you'll be prompted to review the results."
    )
    
    # Store rules in session state
    st.session_state.transcript_analysis_rules = rules_text
    
    # File browser section
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
                        # Get the analysis rules from session state
                        analysis_rules = st.session_state.get('transcript_analysis_rules', '')
                        result = process_transcript_file(file_path, analysis_rules)
                        
                        if result == "PENDING_REVIEW":
                            # Handle human review required case
                            st.session_state.transcript_analysis_result = "Analysis requires human review"
                            st.session_state.transcript_analysis_complete = False
                            st.session_state.transcript_analysis_needs_review = True
                            st.rerun()
                        elif result and not result.startswith("Error"):
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
    
    # Show human review section if needed
    if st.session_state.get('transcript_analysis_needs_review', False):
        st.markdown("---")
        st.markdown("## 👤 Human Review Required")
        
        pending_review = st.session_state.get('transcript_analysis_pending_review', {})
        if pending_review:
            st.warning("⚠️ The analysis did not satisfy all defined rules and requires human review.")
            
            # Show validation results
            rules_validation = pending_review.get('rules_validation', {})
            if 'rule_assessments' in rules_validation:
                st.markdown("### 📋 Rules Assessment")
                for assessment in rules_validation['rule_assessments']:
                    status = "✅" if assessment.get("satisfied", True) else "❌"
                    st.markdown(f"{status} **{assessment.get('rule', 'Unknown rule')}**: {assessment.get('feedback', 'No feedback')}")
            
            if 'recommendations' in rules_validation:
                st.markdown("### 💡 Recommendations")
                for rec in rules_validation['recommendations']:
                    st.markdown(f"• {rec}")
            
            # Show the analysis summary for review
            summary = pending_review.get('summary', '')
            if summary:
                st.markdown("### 📄 Analysis Summary for Review")
                st.markdown(summary)
              # Human approval buttons
            st.markdown("### 🎯 Your Decision")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Approve Analysis", type="primary", use_container_width=True):
                    # Approve the analysis and continue
                    with st.spinner("Finalizing approved analysis..."):
                        result = continue_analysis_with_approval(True, "Analysis approved by human reviewer")
                        if result and not result.startswith("Error") and not result.startswith("Analysis rejected"):
                            st.session_state.transcript_analysis_result = result
                            st.session_state.transcript_analysis_complete = True
                            st.session_state.transcript_analysis_needs_review = False
                            st.session_state.transcript_analysis_pending_review = {}
                            st.success("✅ Analysis approved and completed!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
            
            with col2:
                if st.button("❌ Reject Analysis", use_container_width=True):
                    # Reject the analysis
                    st.session_state.transcript_analysis_result = ""
                    st.session_state.transcript_analysis_complete = False
                    st.session_state.transcript_analysis_needs_review = False
                    st.session_state.transcript_analysis_pending_review = {}
                    st.session_state.transcript_analysis_error = "Analysis rejected by human reviewer"
                    st.error("❌ Analysis rejected. Please try again with different rules or document.")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Retry Analysis", use_container_width=True):
                    # Clear states to allow retry
                    st.session_state.transcript_analysis_result = ""
                    st.session_state.transcript_analysis_complete = False
                    st.session_state.transcript_analysis_needs_review = False
                    st.session_state.transcript_analysis_pending_review = {}
                    st.info("💡 Modify the rules above and click 'Analyze Transcript' to retry.")
                    st.rerun()

    # Show results at the bottom if analysis is complete
    if st.session_state.transcript_analysis_complete and st.session_state.transcript_analysis_result:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        
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
        
        # Show rules validation results if available
        if st.session_state.transcript_analysis_metrics.get("rules_validation"):
            rules_validation = st.session_state.transcript_analysis_metrics["rules_validation"]
            
            with st.expander("📋 Rules Validation Results", expanded=False):
                overall_satisfaction = rules_validation.get("overall_satisfaction", True)
                status_icon = "✅" if overall_satisfaction else "❌"
                st.markdown(f"**Overall Satisfaction:** {status_icon} {'Passed' if overall_satisfaction else 'Failed'}")
                
                if "rule_assessments" in rules_validation:
                    st.markdown("**Individual Rule Assessment:**")
                    for assessment in rules_validation["rule_assessments"]:
                        status = "✅" if assessment.get("satisfied", True) else "❌"
                        st.markdown(f"{status} **{assessment.get('rule', 'Unknown rule')}**")
                        st.markdown(f"   ➤ {assessment.get('feedback', 'No feedback')}")
                
                if "recommendations" in rules_validation:
                    st.markdown("**Recommendations:**")
                    for rec in rules_validation["recommendations"]:
                        st.markdown(f"• {rec}")
                
                if st.session_state.transcript_analysis_metrics.get("validation_feedback"):
                    st.markdown(f"**Validation Feedback:** {st.session_state.transcript_analysis_metrics['validation_feedback']}")
        
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
                    use_container_width=True                ):
                    st.success("✅ Data downloaded!")
    
    elif st.session_state.transcript_analysis_error:
        st.markdown("---")
        st.error(f"❌ {st.session_state.transcript_analysis_error}")
    
    elif not st.session_state.transcript_analysis_complete:
        st.markdown("---")
        st.info("🔍 Select a document above and click 'Analyze Transcript' to begin processing.")

def continue_analysis_with_approval(approval: bool, feedback: str = "") -> str:
    """Continue the analysis after human approval"""
    try:
        pending_review = st.session_state.get('transcript_analysis_pending_review', {})
        if not pending_review:
            return "Error: No pending review found"
        
        # Get the stored state
        current_state = pending_review.get('full_state', {})
        
        # Update the state with human approval
        current_state['human_approval'] = approval
        if feedback:
            current_state['validation_feedback'] = f"Human review: {feedback}"
        
        # Create progress indicators
        progress_bar = st.progress(90)
        status_text = st.empty()
        
        if approval:
            status_text.text("✅ Analysis approved by human reviewer!")
            progress_bar.progress(95)
            
            # Return the final summary
            final_result = current_state.get("final_summary", "")
            
            # Store enhanced metrics
            chunk_metrics = []
            if "chunk_results" in current_state:
                for i, result in enumerate(current_state["chunk_results"]):
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
                "chunks_processed": len(current_state.get("chunks", [])),
                "results_aggregated": len(current_state.get("chunk_results", [])),
                "text_length": len(current_state.get("transcript_text", "")),
                "summary_length": len(current_state.get("final_summary", "")),
                "aggregated_data": current_state.get("aggregated_results", {}),
                "chunk_details": chunk_metrics,
                "rules_validation": current_state.get("rules_validation", {}),
                "validation_feedback": current_state.get("validation_feedback", ""),
                "human_approval": True
            }
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis completed with human approval!")
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            return final_result
        else:
            status_text.text("❌ Analysis rejected by human reviewer")
            progress_bar.progress(100)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            return f"Analysis rejected: {feedback}"
            
    except Exception as e:
        st.error(f"Error continuing analysis: {str(e)}")
        return f"Error continuing analysis: {str(e)}"
