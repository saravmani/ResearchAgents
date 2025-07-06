import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import from graphs
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from graphs.pdf_table_extraction_graph import create_pdf_table_extraction_graph, extract_pdf_tables
except ImportError as e:
    st.error(f"Could not import table extraction graph: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

def list_available_documents():
    """List all available PDF documents in the docs directory"""
    docs_dir = os.path.join(parent_dir, "docs")
    available_docs = []
    
    if not os.path.exists(docs_dir):
        return available_docs
    
    try:
        # Walk through the directory structure: docs/YYYY/QX/Company/DocumentType/
        for year_dir in os.listdir(docs_dir):
            year_path = os.path.join(docs_dir, year_dir)
            if not os.path.isdir(year_path):
                continue
                
            for quarter_dir in os.listdir(year_path):
                quarter_path = os.path.join(year_path, quarter_dir)
                if not os.path.isdir(quarter_path):
                    continue
                    
                for company_dir in os.listdir(quarter_path):
                    company_path = os.path.join(quarter_path, company_dir)
                    if not os.path.isdir(company_path):
                        continue
                    
                    for doc_type_dir in os.listdir(company_path):
                        doc_type_path = os.path.join(company_path, doc_type_dir)
                        if not os.path.isdir(doc_type_path):
                            continue
                        
                        # Find PDF files in document type folder
                        for file_name in os.listdir(doc_type_path):
                            if file_name.lower().endswith('.pdf'):
                                available_docs.append({
                                    'year': year_dir,
                                    'quarter': quarter_dir,
                                    'company': company_dir,
                                    'document_type': doc_type_dir,
                                    'document': file_name,
                                    'full_path': os.path.join(doc_type_path, file_name),
                                    'relative_path': os.path.join('docs', year_dir, quarter_dir, company_dir, doc_type_dir, file_name)
                                })
    except Exception as e:
        st.error(f"Error scanning documents: {e}")
    
    return available_docs

def initialize_table_extraction_session():
    """Initialize session state for table extraction"""
    if 'table_extraction_graph' not in st.session_state:
        try:
            st.session_state.table_extraction_graph = create_pdf_table_extraction_graph()
        except Exception as e:
            st.error(f"Failed to initialize table extraction graph: {e}")
    
    if 'last_extraction_result' not in st.session_state:
        st.session_state.last_extraction_result = None
    
    if 'extraction_in_progress' not in st.session_state:
        st.session_state.extraction_in_progress = False

def show_table_extraction():
    """Main UI for PDF table extraction"""
    
    st.header("📊 PDF Table Extraction")
    st.markdown("Extract tables from PDF documents and convert them to Markdown format.")
    
    # Create tabs for different input methods
    manual_tab, browse_tab, results_tab = st.tabs(["📝 Manual Input", "📁 Browse Documents", "📊 Results"])
    
    # Tab 1: Manual Input
    with manual_tab:
        st.subheader("🎯 Extract Tables from Specific Document")
          # Input fields
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year = st.selectbox(
                "Year",
                ["2025", "2024", "2023", "2022", "2021"],
                index=0,
                help="Select the year"
            )
            
            quarter = st.selectbox(
                "Quarter",
                ["Q1", "Q2", "Q3", "Q4"],
                index=0,
                help="Select the quarter"
            )
        
        with col2:
            company_name = st.selectbox(
                "Company Name",
                ["SHELL", "AAPL"],
                index=0,
                help="Select the company"
            )
            
            document_type = st.selectbox(
                "Document Type",
                ["QRAReport", "FirstCutModel", "BalanceSheet"],
                index=0,
                help="Select the document type"
            )
        
        with col3:
            document_name = st.text_input(
                "Document Name",
                value="q1-2025-qra.pdf",
                help="Enter the exact PDF filename"
            )
        
        # Validate document path (updated to include document type)
        if company_name and document_name:
            document_path = os.path.join(parent_dir, "docs", year, quarter, company_name.upper(), document_type, document_name)
            
            if os.path.exists(document_path):
                st.success(f"✅ Document found: {os.path.relpath(document_path, parent_dir)}")
                
                # File info
                file_size = os.path.getsize(document_path)
                file_size_mb = file_size / (1024 * 1024)
                st.info(f"📄 File size: {file_size_mb:.2f} MB")
                
            else:
                st.warning(f"⚠️ Document not found: {os.path.relpath(document_path, parent_dir)}")
                st.info("Expected path structure: docs/YYYY/QX/COMPANY/DOCUMENT_TYPE/filename.pdf")
          # Extract button
        extract_button = st.button(
            "🚀 Extract Tables",
            type="primary",
            disabled=not (company_name and document_name and year and quarter and document_type) or st.session_state.get('extraction_in_progress', False)
        )
        
        # Process extraction
        if extract_button:
            process_table_extraction(year, quarter, company_name, document_name, document_type)
    
    # Tab 2: Browse Documents
    with browse_tab:
        st.subheader("📁 Browse Available Documents")
        
        available_docs = list_available_documents()
        
        if available_docs:
            st.write(f"Found **{len(available_docs)}** PDF documents:")
              # Create a selection interface
            for i, doc in enumerate(available_docs):
                with st.expander(f"📄 {doc['company']} - {doc['document_type']} - {doc['document']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Path:** {doc['relative_path']}")
                        st.write(f"**Period:** {doc['quarter']} {doc['year']}")
                        st.write(f"**Type:** {doc['document_type']}")
                    
                    with col2:
                        file_size = os.path.getsize(doc['full_path'])
                        file_size_mb = file_size / (1024 * 1024)
                        st.metric("Size", f"{file_size_mb:.2f} MB")
                    
                    with col3:
                        if st.button(f"Extract Tables", key=f"extract_{i}", 
                                   disabled=st.session_state.get('extraction_in_progress', False)):
                            process_table_extraction(
                                doc['year'], 
                                doc['quarter'], 
                                doc['company'], 
                                doc['document'],
                                doc['document_type']
                            )
        else:
            st.info("No PDF documents found in the docs directory.")
            st.markdown("**Expected directory structure:**")
            st.code("""
docs/
├── 2025/
│   ├── Q1/
│   │   ├── COMPANY_NAME/
│   │   │   ├── document1.pdf
│   │   │   └── document2.pdf
│   │   └── OTHER_COMPANIES/
│   └── OTHER_QUARTERS/
└── OTHER_YEARS/
            """)
    
    # Tab 3: Results
    with results_tab:
        st.subheader("📊 Extraction Results")
        
        if st.session_state.get('last_extraction_result'):
            result = st.session_state.last_extraction_result
            
            st.success("✅ Last extraction completed successfully!")
            
            # Display result details
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Company", result.get('company', 'Unknown'))
                st.metric("Document", result.get('document', 'Unknown'))
            
            with col2:
                st.metric("Period", f"{result.get('quarter', 'Unknown')} {result.get('year', 'Unknown')}")
                st.metric("Pages Processed", result.get('pages_processed', 0))
            
            # Show output path
            if result.get('output_path'):
                st.write(f"**Output File:** {os.path.relpath(result['output_path'], parent_dir)}")
                
                # Download button
                if os.path.exists(result['output_path']):
                    with open(result['output_path'], 'r', encoding='utf-8') as f:
                        markdown_content = f.read()
                    
                    st.download_button(
                        label="📥 Download Extracted Tables",
                        data=markdown_content,
                        file_name=os.path.basename(result['output_path']),
                        mime="text/markdown"
                    )
                    
                    # Preview
                    with st.expander("👀 Preview Extracted Content", expanded=False):
                        preview_content = markdown_content[:2000] + "..." if len(markdown_content) > 2000 else markdown_content
                        st.markdown(preview_content)
        else:
            st.info("No extraction results available yet. Run a table extraction to see results here.")
        
        # List previously extracted files
        extracted_dir = os.path.join(parent_dir, "extracted_tables")
        if os.path.exists(extracted_dir):
            st.markdown("### 📚 Previously Extracted Files")
            
            extracted_files = []
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if file.endswith('.md'):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, extracted_dir)
                        extracted_files.append({
                            'name': file,
                            'path': rel_path,
                            'full_path': full_path,
                            'modified': datetime.fromtimestamp(os.path.getmtime(full_path))
                        })
            
            if extracted_files:
                # Sort by modification time (newest first)
                extracted_files.sort(key=lambda x: x['modified'], reverse=True)
                
                for file_info in extracted_files[:10]:  # Show last 10 files
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"📄 **{file_info['name']}**")
                        st.caption(file_info['path'])
                    
                    with col2:
                        st.caption(f"Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M')}")
                    
                    with col3:
                        # Download button for each file
                        with open(file_info['full_path'], 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        st.download_button(
                            label="📥",
                            data=content,
                            file_name=file_info['name'],
                            mime="text/markdown",
                            key=f"download_{file_info['name']}"
                        )

def process_table_extraction(year: str, quarter: str, company_name: str, document_name: str, document_type: str = "General"):
    """Process the table extraction with progress indicators"""
    
    # Set extraction in progress
    st.session_state.extraction_in_progress = True
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Initialize
        status_text.text("🔧 Initializing table extraction...")
        progress_bar.progress(10)
        
        # Step 2: Load document
        status_text.text("📄 Loading PDF document...")
        progress_bar.progress(20)
        
        # Step 3: Process extraction
        status_text.text("🔍 Extracting tables from pages...")
        progress_bar.progress(30)
        
        # Call the extraction function
        result = extract_pdf_tables(year, quarter, company_name, document_name)
        
        progress_bar.progress(80)
        status_text.text("💾 Saving results...")
        
        # Step 4: Complete
        progress_bar.progress(100)
        status_text.text("✅ Table extraction completed!")
        
        # Store results in session state
        if result and result.get('messages'):
            # Extract information from the result message
            message_content = result['messages'][0].content
            
            if "✅" in message_content:
                # Success case
                st.session_state.last_extraction_result = {
                    'year': year,
                    'quarter': quarter,
                    'company': company_name,
                    'document': document_name,
                    'document_type': document_type,
                    'success': True,
                    'message': message_content,
                    'output_path': extract_output_path_from_message(message_content),
                    'pages_processed': extract_pages_from_message(message_content)
                }
                
                st.success("🎉 Table extraction completed successfully!")
                st.markdown(message_content)
                
            else:
                # Error case
                st.error("❌ Table extraction failed!")
                st.error(message_content)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        error_msg = f"Error during table extraction: {str(e)}"
        st.error(error_msg)
        progress_bar.empty()
        status_text.empty()
    
    finally:
        # Reset extraction in progress
        st.session_state.extraction_in_progress = False

def extract_output_path_from_message(message: str) -> str:
    """Extract output path from result message"""
    try:
        if "Output Saved:" in message:
            lines = message.split('\n')
            for line in lines:
                if "Output Saved:" in line:
                    path = line.split("Output Saved:", 1)[1].strip()
                    # Convert relative path to absolute
                    return os.path.join(parent_dir, path)
    except:
        pass
    return ""

def extract_pages_from_message(message: str) -> int:
    """Extract pages processed count from result message"""
    try:
        if "Pages Processed:" in message:
            lines = message.split('\n')
            for line in lines:
                if "Pages Processed:" in line:
                    pages_str = line.split("Pages Processed:", 1)[1].strip()
                    return int(pages_str)
    except:
        pass
    return 0

if __name__ == "__main__":
    # For testing
    initialize_table_extraction_session()
    show_table_extraction()
