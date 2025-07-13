import streamlit as st
import asyncio
from datetime import datetime
import os
import sys

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from graphs.map_reduce_analysis_graph import run_map_reduce_analysis
except ImportError as e:
    st.error(f"Could not import the graph: {e}")
    st.stop()

# --- Session State Initialization ---
def initialize_session_state():
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = f"map_reduce_{int(datetime.now().timestamp())}"
    if "mapped_results" not in st.session_state:
        st.session_state.mapped_results = []
    if "final_summary" not in st.session_state:
        st.session_state.final_summary = ""
    if "error" not in st.session_state:
        st.session_state.error = ""

# --- Main UI ---
def main():
    st.set_page_config(page_title="Map-Reduce Document Analysis", layout="wide")
    st.title("🗺️ Map-Reduce Document Analysis")
    st.markdown("Analyzes a document by running multiple prompts and aggregating the results.")

    initialize_session_state()

    # --- Sidebar for controls ---
    with st.sidebar:
        st.header("Controls")
        doc_path = st.text_input("Document Path", "docs/financial_report_2025_q2.md")

        if st.button("Start Analysis", type="primary"):
            st.session_state.analysis_started = True
            st.session_state.analysis_complete = False
            st.session_state.mapped_results = []
            st.session_state.final_summary = ""
            st.session_state.error = ""
            
            # --- Run Analysis ---
            async def run_analysis():
                progress_bar = st.progress(0, "Starting analysis...")
                try:
                    i = 0
                    async for state in run_map_reduce_analysis(doc_path, st.session_state.thread_id):
                        if "error" in state and state["error"]:
                            st.session_state.error = state["error"]
                            break
                        if "mapped_results" in state:
                            st.session_state.mapped_results.extend(state["mapped_results"])
                            progress = int((i + 1) / 3 * 80)
                            progress_bar.progress(progress, f"Mapping prompt {i+1}/3...")
                            i += 1
                        if "final_summary" in state and state["final_summary"]:
                            st.session_state.final_summary = state["final_summary"]
                            progress_bar.progress(100, "Analysis complete!")
                    st.session_state.analysis_complete = True
                except Exception as e:
                    st.session_state.error = str(e)
                
            asyncio.run(run_analysis())
            st.rerun()

        if st.button("Reset"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    # --- Main Content Area ---
    if st.session_state.error:
        st.error(f"An error occurred: {st.session_state.error}")

    if not st.session_state.analysis_started:
        st.info("Click 'Start Analysis' in the sidebar to begin.")
    else:
        st.header("Analysis Results")
        
        # Display mapped results as they come in
        if st.session_state.mapped_results:
            st.subheader("Intermediate Mapped Results")
            for i, result in enumerate(st.session_state.mapped_results):
                with st.expander(f"Result from Prompt {i+1}", expanded=True):
                    st.markdown(result)
        
        # Display final summary when available
        if st.session_state.final_summary:
            st.subheader("Final Aggregated Summary")
            st.markdown(st.session_state.final_summary)
        elif not st.session_state.analysis_complete:
            st.info("Analysis in progress...")

if __name__ == "__main__":
    main()
