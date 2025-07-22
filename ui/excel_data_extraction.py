import streamlit as st
import os
import tempfile
from pathlib import Path
import pandas as pd
from graphs.excel_data_extraction_graph import run_excel_extraction_workflow
import json

def excel_data_extraction_ui():
    """
    Streamlit UI for Excel Data Extraction using Vision AI
    """
    st.title("🔍 Excel Vision Data Extraction")
    st.markdown("Upload an Excel file to extract table data using OpenAI GPT-4 Vision AI - no pre-processing required!")
    
    # Information about the Vision AI approach
    with st.expander("ℹ️ How Vision AI Extraction Works", expanded=False):
        st.markdown("""
        ### 🤖 Advanced Vision AI Processing
        
        This tool uses **OpenAI GPT-4 Vision** to directly analyze Excel spreadsheets:
        
        1. **📊 Sheet Visualization**: Each Excel sheet is converted to a high-resolution image
        2. **👁️ Vision Analysis**: GPT-4 Vision analyzes the images to identify table structures
        3. **📝 Direct Extraction**: Tables are extracted directly from visual patterns without pre-parsing
        4. **🧠 AI Analysis**: Comprehensive business insights are generated from the extracted data
        
        ### ✅ Benefits:
        - **No format limitations**: Works with complex layouts and merged cells
        - **Visual accuracy**: Preserves original table formatting and relationships
        - **Smart detection**: Identifies tables even in unconventional layouts
        - **Comprehensive analysis**: AI provides business insights beyond just extraction
        """)
    
    # File upload section
    st.header("1. Upload Excel File")
    uploaded_file = st.file_uploader(
        "Choose an Excel file (.xlsx, .xls)",
        type=['xlsx', 'xls'],
        help="Upload an Excel file for Vision AI analysis"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"File size: {uploaded_file.size / 1024:.1f} KB")
        
        # Preview section
        st.header("2. File Preview")
        
        try:
            # Read Excel file to show preview
            excel_data = pd.ExcelFile(uploaded_file)
            sheet_names = excel_data.sheet_names
            
            st.write(f"**📋 Sheets detected:** {len(sheet_names)}")
            
            # Show sheet names in a nice format
            col1, col2 = st.columns(2)
            for i, sheet_name in enumerate(sheet_names):
                target_col = col1 if i % 2 == 0 else col2
                target_col.write(f"📄 {i + 1}. {sheet_name}")
            
            # Show preview of first sheet
            if sheet_names:
                st.subheader(f"👀 Preview of '{sheet_names[0]}'")
                try:
                    df_preview = pd.read_excel(uploaded_file, sheet_name=sheet_names[0])
                    st.dataframe(df_preview.head(10), use_container_width=True)
                    st.caption(f"Showing first 10 rows of {len(df_preview)} total rows")
                except Exception as e:
                    st.warning(f"⚠️ Could not preview sheet: {str(e)}")
            
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {str(e)}")
            return
        
        # Vision AI Processing options
        st.header("3. Vision AI Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            thread_id = st.text_input(
                "Session ID (optional)",
                value=f"excel_vision_{uploaded_file.name.split('.')[0]}",
                help="Unique identifier for this Vision AI analysis session"
            )
        
        with col2:
            save_debug_images = st.checkbox(
                "Save debug images",
                value=False,
                help="Save sheet images to extracted_images folder for debugging"
            )
        
        # Processing info
        st.info("""
        🔍 **Vision AI Processing Steps:**
        1. Convert each Excel sheet to high-resolution images
        2. Send images to GPT-4 Vision for table detection and extraction
        3. Convert identified tables to structured Markdown format
        4. Generate comprehensive business analysis and insights
        """)
        
        # Analysis button
        st.header("4. Start Vision AI Analysis")
        
        if st.button("🚀 Analyze with Vision AI", type="primary", use_container_width=True):
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name
            
            try:
                with st.spinner("🔍 Running Vision AI analysis on Excel file..."):
                    # Create progress tracking
                    progress_container = st.container()
                    status_placeholder = st.empty()
                    progress_bar = st.progress(0)
                    
                    # Update status during processing
                    status_placeholder.info("📊 Converting Excel sheets to images...")
                    progress_bar.progress(0.2)
                    
                    # Run the extraction workflow
                    result = run_excel_extraction_workflow(
                        excel_file_path=temp_file_path,
                        thread_id=thread_id
                    )
                    
                    progress_bar.progress(1.0)
                    status_placeholder.success("✅ Vision AI analysis completed!")
                
                # Display results
                st.header("5. Vision AI Analysis Results")
                
                if result.get("error_message"):
                    st.error(f"❌ Error: {result.get('error_message')}")
                elif result.get("analysis_result"):
                    
                    # Show processing summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Sheets Processed", f"{result.get('processed_sheets', 0)}")
                    with col2:
                        st.metric("Total Sheets", f"{result.get('total_sheets', 0)}")
                    with col3:
                        processing_stage = result.get('processing_stage', 'unknown')
                        st.metric("Status", "✅ Complete" if processing_stage == "completed" else processing_stage)
                    
                    # Show Vision AI analysis result
                    st.subheader("🧠 AI Business Analysis")
                    with st.container():
                        st.markdown(result["analysis_result"])
                    
                    # Show extracted tables by sheet
                    if result.get("extracted_tables"):
                        st.subheader("📊 Extracted Table Data")
                        
                        # Create tabs for each sheet
                        sheet_tabs = st.tabs([f"Sheet: {table['sheet_name']}" for table in result["extracted_tables"]])
                        
                        for i, table_data in enumerate(result["extracted_tables"]):
                            with sheet_tabs[i]:
                                sheet_name = table_data.get("sheet_name", "Unknown")
                                content = table_data.get("extracted_content", "")
                                extraction_time = table_data.get("extraction_timestamp", "Unknown")
                                
                                st.caption(f"📅 Extracted: {extraction_time}")
                                
                                if "No tables detected" in content or "No clear tabular data" in content:
                                    st.warning(f"⚠️ {content}")
                                else:
                                    st.markdown(content)
                    
                    # Show save location
                    if result.get("output_path"):
                        st.success(f"💾 Results saved to: `{result['output_path']}`")
                        
                        # Show generated files
                        output_path = result["output_path"]
                        if os.path.exists(output_path):
                            st.subheader("📁 Generated Files")
                            files_info = []
                            
                            for file_name in os.listdir(output_path):
                                file_path = os.path.join(output_path, file_name)
                                if os.path.isfile(file_path):
                                    file_size = os.path.getsize(file_path)
                                    file_type = "Analysis Report" if "analysis" in file_name else "Extracted Data" if "extracted" in file_name or "sheet" in file_name else "Data"
                                    files_info.append({
                                        "File": file_name,
                                        "Type": file_type,
                                        "Size (KB)": f"{file_size / 1024:.1f}"
                                    })
                            
                            if files_info:
                                files_df = pd.DataFrame(files_info)
                                st.dataframe(files_df, use_container_width=True)
                
                else:
                    st.warning("⚠️ No analysis result received from Vision AI")
                
                # Processing statistics
                if result.get("processed_sheets", 0) > 0:
                    st.subheader("📊 Processing Statistics")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        success_rate = (result.get("processed_sheets", 0) / result.get("total_sheets", 1)) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    
                    with col2:
                        total_chars = sum(len(table.get("extracted_content", "")) for table in result.get("extracted_tables", []))
                        st.metric("Data Extracted", f"{total_chars:,} chars")
                    
                    with col3:
                        analysis_length = len(result.get("analysis_result", ""))
                        st.metric("Analysis Length", f"{analysis_length:,} chars")
                
            except Exception as e:
                st.error(f"❌ Error during Vision AI analysis: {str(e)}")
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
    
    else:
        # Instructions when no file is uploaded
        st.info("👆 Please upload an Excel file to begin Vision AI analysis.")
        
        

if __name__ == "__main__":
    excel_data_extraction_ui()