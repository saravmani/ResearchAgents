import streamlit as st
import time
import io
import json
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import from graphs and utils
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from utils.document_index_helper import DocumentIndexHelper

helper = DocumentIndexHelper(persist_directory="./chroma_db")

try:
    from graphs.documentsummarygraph import create_document_summary_graph
    
    # Import document index helper directly from utils directory
    utils_dir = os.path.join(parent_dir, 'utils')
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)   
   
    
except ImportError as e:
    st.error(f"Could not import required modules: {e}")
    st.error("Please ensure all required dependencies are installed.")
    st.stop()

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

def save_uploaded_file(uploaded_file, company_name: str, quarter: str = "Q1", year: int = 2025) -> str:
    """
    Save uploaded file to the docs directory structure and return the full path.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        company_name: Name of the company
        quarter: Quarter (Q1, Q2, Q3, Q4)
        year: Year
        
    Returns:
        str: Full path to the saved file
    """
    try:
        # Create the directory structure: docs/YYYY/QX/CompanyName/
        docs_base = os.path.join(parent_dir, "docs")
        company_dir = os.path.join(docs_base, str(year), quarter, company_name.upper())
        
        # Create directories if they don't exist
        os.makedirs(company_dir, exist_ok=True)
        
        # Generate unique filename if file already exists
        original_filename = uploaded_file.name
        file_path = os.path.join(company_dir, original_filename)
        
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_filename)
            new_filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(company_dir, new_filename)
            counter += 1
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"📁 File saved to: {os.path.relpath(file_path, parent_dir)}")
        return file_path
        
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def index_document_in_vectordb(file_path: str, collection_name: str = "company_documents") -> dict:
    """
    Index the document in the vector database.
    
    Args:
        file_path: Full path to the document
        collection_name: Name of the collection to store in
        
    Returns:
        dict: Indexing result
    """
    try:
        # Initialize document helper
        
        
        # Index the document
        result = helper.index_document(file_path, collection_name)
        
        if result.get("success"):
            st.success(f"✅ Document indexed successfully! Created {result.get('chunks_created', 0)} chunks.")
        else:
            st.error(f"❌ Failed to index document: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        error_msg = f"Error indexing document: {str(e)}"
        st.error(error_msg)
        return {"success": False, "error": error_msg}

def search_documents(query: str, collection_name: str = "company_documents", k: int = 5) -> list:
    """
    Search for documents in the vector database.
    
    Args:
        query: Search query
        collection_name: Collection to search in
        k: Number of results to return
        
    Returns:
        list: Search results
    """
    try:
        results = helper.search_data(query, collection_name, k)
        return results
    except Exception as e:
        st.error(f"Error searching documents: {str(e)}")
        return []

def process_document_with_query(uploaded_file, user_query: str, company_name: str, quarter: str = "Q1", year: int = 2025):
    """Process document by saving, indexing, and answering user query"""
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Save the uploaded file
        status_text.text("💾 Saving document to company folder...")
        progress_bar.progress(20)
        
        file_path = save_uploaded_file(uploaded_file, company_name, quarter, year)
        if not file_path:
            return "Failed to save document"
        
        # Step 2: Index the document
        status_text.text("🔍 Indexing document in vector database...")
        progress_bar.progress(40)
        
        collection_name = f"{company_name.upper()}_{quarter}_{year}"
        index_result = index_document_in_vectordb(file_path, collection_name)
        
        if not index_result.get("success"):
            return f"Failed to index document: {index_result.get('error', 'Unknown error')}"
        
        # Step 3: Search for relevant context
        status_text.text("🔎 Searching for relevant content...")
        progress_bar.progress(60)
        
        search_results = search_documents(user_query, collection_name, k=5)
        
        if not search_results:
            return f"Document indexed successfully, but no relevant content found for query: '{user_query}'"
        
        # Step 4: Generate answer using context
        status_text.text("🤖 Generating answer based on document content...")
        progress_bar.progress(80)
        
        # Combine search results into context
        context_parts = []
        for result in search_results:
            context_parts.append(f"**From {result['source_file']}:**\n{result['content']}")
        
        combined_context = "\n\n".join(context_parts)
        
        # Create a simple answer format
        answer = f"""# Query Answer

**Question:** {user_query}

**Document:** {os.path.basename(file_path)}

**Answer based on document content:**

{combined_context}

---
*Answer generated from {len(search_results)} relevant document sections.*
"""
        
        # Step 5: Complete
        status_text.text("✅ Document processed and query answered!")
        progress_bar.progress(100)
        time.sleep(0.5)
        
        # Store results in session state
        st.session_state.last_processed_file = os.path.basename(file_path)
        st.session_state.last_query = user_query
        st.session_state.last_answer = answer
        st.session_state.processing_complete = True
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return answer
        
    except Exception as e:
        status_text.text(f"❌ Error: {str(e)}")
        progress_bar.progress(100)
        return f"Error processing document: {str(e)}"

def initialize_document_summarizer_session():
    """Initialize session state for document summarizer"""
    if 'document_graph' not in st.session_state:
        try:
            st.session_state.document_graph = create_document_summary_graph()
        except Exception as e:
            st.error(f"Failed to initialize document processing graph: {e}")
    
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if 'last_processed_file' not in st.session_state:
        st.session_state.last_processed_file = None
    
    if 'last_query' not in st.session_state:
        st.session_state.last_query = None
    
    if 'last_answer' not in st.session_state:
        st.session_state.last_answer = None

def show_document_summarizer():
    """Enhanced Document Summarizer with Upload, Save, and Search functionality"""
    
    st.header("📄 Document Q&A System")
    st.markdown("Upload documents, ask questions, and get AI-powered answers based on your content.")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📁 Document Upload & Query")
        
        # Company information input
        with st.expander("🏢 Company Information", expanded=True):
            company_col1, company_col2, company_col3 = st.columns(3)
            
            with company_col1:
                company_name = st.text_input(
                    "Company Name",
                    value="ACME_CORP",
                    help="Enter the company name (will be used for folder organization)"
                )
            
            with company_col2:
                quarter = st.selectbox(
                    "Quarter",
                    ["Q1", "Q2", "Q3", "Q4"],
                    index=0,
                    help="Select the quarter"
                )
            
            with company_col3:
                year = st.number_input(
                    "Year",
                    min_value=2020,
                    max_value=2030,
                    value=2025,
                    help="Select the year"
                )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a document to upload",
            type=['pdf', 'txt', 'docx', 'doc'],
            help="Supported formats: PDF, TXT, DOCX, DOC"
        )
        
        # User query input
        user_query = st.text_area(
            "Ask a question about the document",
            value="What are the key points in this document?",
            height=100,
            help="Enter your question about the document content"
        )
        
        # Process button
        process_button = st.button(
            "🚀 Upload & Answer Query",
            type="primary",
            disabled=not uploaded_file or not user_query.strip() or not company_name.strip()
        )
        
        # Processing
        if process_button and uploaded_file and user_query and company_name:
            with st.spinner("Processing document..."):
                result = process_document_with_query(
                    uploaded_file, 
                    user_query, 
                    company_name, 
                    quarter, 
                    year
                )
                
                if result:
                    st.markdown("### 🎯 Answer")
                    st.markdown(result)
                    
                    # Add download button for the answer
                    st.download_button(
                        label="📥 Download Answer",
                        data=result,
                        file_name=f"answer_{company_name}_{quarter}_{year}.md",
                        mime="text/markdown"
                    )
    
    with col2:
        st.subheader("📊 Document Search")
        
        # Search existing documents
        with st.expander("🔍 Search Existing Documents", expanded=False):
            search_collection = st.text_input(
                "Collection Name",
                value=f"{company_name.upper()}_{quarter}_{year}" if company_name else "company_documents",
                help="Enter collection name to search"
            )
            
            search_query = st.text_input(
                "Search Query",
                placeholder="Enter search terms...",
                help="Search in existing documents"
            )
            
            search_k = st.slider("Number of results", 1, 10, 3)
            
            if st.button("🔎 Search Documents") and search_query:
                search_results = search_documents(search_query, search_collection, search_k)
                
                if search_results:
                    st.success(f"Found {len(search_results)} results:")
                    
                    for i, result in enumerate(search_results, 1):
                        with st.expander(f"Result {i}: {result['source_file']}", expanded=False):
                            st.write(f"**Rank:** {result['rank']}")
                            st.write(f"**Length:** {result['chunk_length']} chars")
                            st.write(f"**Content:**")
                            st.write(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
                else:
                    st.warning("No results found")
        
        # Collection management
        with st.expander("📚 Collection Management", expanded=False):
            try:
                collections = helper.list_collections()
                
                if collections:
                    st.write("**Available Collections:**")
                    for collection in collections:
                        st.write(f"• {collection['name']}: {collection['document_count']} docs")
                else:
                    st.info("No collections found")
                    
            except Exception as e:
                st.error(f"Error loading collections: {e}")
        
        # Session info
        if st.session_state.processing_complete:
            with st.expander("📈 Session Info", expanded=True):
                if st.session_state.last_processed_file:
                    st.metric("Last File", st.session_state.last_processed_file)
                if st.session_state.last_query:
                    st.write(f"**Last Query:** {st.session_state.last_query}")
    
    # File structure preview
    with st.expander("📁 Document Storage Structure", expanded=False):
        st.code(f"""
docs/
├── {year}/
│   ├── {quarter}/
│   │   ├── {company_name.upper() if company_name else 'COMPANY_NAME'}/
│   │   │   ├── document1.pdf
│   │   │   ├── document2.docx
│   │   │   └── ...
│   │   └── OTHER_COMPANIES/
│   └── OTHER_QUARTERS/
└── OTHER_YEARS/
        """)

if __name__ == "__main__":
    # For testing
    initialize_document_summarizer_session()
    show_document_summarizer()
