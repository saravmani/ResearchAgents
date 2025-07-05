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
    """Enhanced Document Summarizer with separate Upload and Search functionality"""
    
    st.header("📄 Document Q&A System")
    st.markdown("Upload documents, index them in the vector database, and search through your document collection.")
    
    # Create tabs for different operations
    upload_tab, search_tab, manage_tab = st.tabs(["📁 Upload Documents", "🔍 Search Documents", "📚 Manage Collections"])
    
    # Tab 1: Document Upload
    with upload_tab:
        st.subheader("📁 Document Upload & Indexing")
        
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
        
        # Collection name for indexing
        collection_name = st.text_input(
            "Collection Name (optional)",
            value=f"{company_name.upper()}_{quarter}_{year}" if company_name else "company_documents",
            help="Documents will be indexed in this collection"
        )
        
        # Upload button
        col_upload1, col_upload2 = st.columns(2)
        
        with col_upload1:
            upload_button = st.button(
                "📤 Upload Document",
                type="secondary",
                disabled=not uploaded_file or not company_name.strip(),
                help="Save document to structured folder"
            )
        
        with col_upload2:
            index_button = st.button(
                "🗂️ Upload & Index",
                type="primary",
                disabled=not uploaded_file or not company_name.strip(),
                help="Save document and add to vector database"
            )
        
        # Process upload only
        if upload_button and uploaded_file and company_name:
            with st.spinner("Uploading document..."):
                file_path = save_uploaded_file(uploaded_file, company_name, quarter, year)
                if file_path:
                    st.success(f"✅ Document uploaded successfully!")
                    st.session_state.last_uploaded_file = file_path
                    st.session_state.last_collection = collection_name
        
        # Process upload and indexing
        if index_button and uploaded_file and company_name:
            with st.spinner("Uploading and indexing document..."):
                # First save the file
                file_path = save_uploaded_file(uploaded_file, company_name, quarter, year)
                if file_path:
                    # Then index it
                    result = index_document_in_vectordb(file_path, collection_name)
                    if result.get("success"):
                        st.success(f"✅ Document uploaded and indexed successfully!")
                        st.session_state.last_uploaded_file = file_path
                        st.session_state.last_collection = collection_name
                        st.session_state.last_index_result = result
        
        # Show upload results
        if 'last_uploaded_file' in st.session_state and st.session_state.last_uploaded_file:
            with st.expander("📄 Last Upload Details", expanded=False):
                st.write(f"**File:** {os.path.basename(st.session_state.last_uploaded_file)}")
                st.write(f"**Path:** {os.path.relpath(st.session_state.last_uploaded_file, parent_dir)}")
                if 'last_index_result' in st.session_state:
                    result = st.session_state.last_index_result
                    st.write(f"**Indexed:** Yes ({result.get('chunks_created', 0)} chunks)")
                    st.write(f"**Collection:** {st.session_state.get('last_collection', 'Unknown')}")
    
    # Tab 2: Document Search & Q&A
    with search_tab:
        st.subheader("🔍 Search & Ask Questions")
        
        # Collection selection
        available_collections = []
        try:
            collections = helper.list_collections()
            available_collections = [col['name'] for col in collections] if collections else []
        except:
            available_collections = ["company_documents"]
        
        if not available_collections:
            st.warning("No collections found. Please upload and index some documents first.")
            return
        
        search_collection = st.selectbox(
            "Select Collection",
            available_collections,
            help="Choose which collection to search"
        )
        
        # Search options
        col_search1, col_search2 = st.columns([3, 1])
        
        with col_search1:
            search_query = st.text_input(
                "Search Query / Ask a Question",
                placeholder="What are the key financial metrics?",
                help="Enter your search query or question"
            )
        
        with col_search2:
            search_k = st.slider("Results", 1, 10, 3, help="Number of results to return")
        
        # Search button
        search_button = st.button(
            "🔎 Search & Answer",
            type="primary",
            disabled=not search_query.strip()
        )
        
        # Process search
        if search_button and search_query:
            with st.spinner("Searching documents..."):
                search_results = search_documents(search_query, search_collection, search_k)
                
                if search_results:
                    # Generate answer from search results
                    context_parts = [result['content'] for result in search_results]
                    combined_context = "\n\n".join(context_parts)
                    
                    # Display answer
                    st.markdown("### 🎯 Answer")
                    answer = f"""**Question:** {search_query}

**Answer based on document collection '{search_collection}':**

{combined_context}

---
*Answer generated from {len(search_results)} relevant document sections.*
"""
                    st.markdown(answer)
                    
                    # Download button for answer
                    st.download_button(
                        label="📥 Download Answer",
                        data=answer,
                        file_name=f"answer_{search_collection}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                    
                    # Show detailed results
                    with st.expander("📋 Detailed Search Results", expanded=False):
                        for i, result in enumerate(search_results, 1):
                            st.markdown(f"**Result {i}:** {result['source_file']}")
                            st.markdown(f"*Length: {result['chunk_length']} chars*")
                            st.markdown("**Content:**")
                            content_preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                            st.text_area(f"Content {i}", content_preview, height=100, disabled=True)
                            st.divider()
                else:
                    st.warning("No results found for your query.")
    
    # Tab 3: Collection Management
    
    with manage_tab:
        st.subheader("📚 Collection Management")
        
        # Collection statistics
        try:
            collections = helper.list_collections()
            
            if collections:
                st.write("**Available Collections:**")
                
                for collection in collections:
                    col_name, col_docs, col_delete = st.columns([2, 1, 1])
                    
                    with col_name:
                        st.write(f"📁 **{collection['name']}**")
                    
                    with col_docs:
                        st.metric("Documents", collection['document_count'])
                    
                    with col_delete:
                        if st.button(f"🗑️ Delete", key=f"delete_{collection['name']}"):
                            try:
                                helper.delete_collection(collection['name'])
                                st.success(f"Deleted collection: {collection['name']}")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting collection: {e}")
                    
                    st.divider()
            else:
                st.info("No collections found. Upload and index documents to create collections.")
                
        except Exception as e:
            st.error(f"Error loading collections: {e}")
        
        # Collection creation
        with st.expander("➕ Create New Collection", expanded=False):
            new_collection_name = st.text_input("Collection Name")
            if st.button("Create Collection") and new_collection_name:
                st.info("Collections are created automatically when you index documents.")
    
    # File structure preview (outside tabs)
    with st.expander("📁 Document Storage Structure Preview", expanded=False):
        st.code(f"""
docs/
├── 2025/
│   ├── Q1/
│   │   ├── ACME_CORP/
│   │   │   ├── document1.pdf
│   │   │   ├── document2.docx
│   │   │   └── ...
│   │   └── OTHER_COMPANIES/
│   └── OTHER_QUARTERS/
└── OTHER_YEARS/
        """)

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
    
    if 'last_uploaded_file' not in st.session_state:
        st.session_state.last_uploaded_file = None
    
    if 'last_collection' not in st.session_state:
        st.session_state.last_collection = None
    
    if 'last_index_result' not in st.session_state:
        st.session_state.last_index_result = None

if __name__ == "__main__":
    # For testing
    initialize_document_summarizer_session()
    show_document_summarizer()
