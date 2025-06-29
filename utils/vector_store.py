import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchVectorStore:
    """
    Manages the vector store for equity research documents using ChromaDB
    Supports quarter-wise collections for different companies
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", company_code: str = None, quarter: str = None, year: int = None):
        self.persist_directory = persist_directory
        self.company_code = company_code
        self.quarter = quarter
        self.year = year
        
        # Generate collection name based on company, quarter, and year
        if company_code and quarter and year:
            self.collection_name = f"{company_code}_{quarter}_{year}"
        else:
            self.collection_name = "equity_research_default"
        
        # Initialize embeddings using SentenceTransformers (compatible with LangChain)
        self.embeddings = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Initialize Chroma vector store with LangChain-compatible embedding function
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        
        logger.info(f"ChromaDB initialized at {persist_directory} with collection: {self.collection_name}")
    def load_documents_from_directory(self, docs_path: str) -> List[Document]:
        """Load and split documents from the structured directory (year/quarter/company)"""
        try:
            # If specific company/quarter/year is set, load from that specific path
            if self.company_code and self.quarter and self.year:
                specific_path = os.path.join(docs_path, str(self.year), self.quarter, self.company_code)
                if os.path.exists(specific_path):
                    docs_path = specific_path
                    logger.info(f"Loading documents from specific path: {specific_path}")
                else:
                    logger.warning(f"Specific path not found: {specific_path}")
                    return []
            
            # Load markdown files recursively
            loader = DirectoryLoader(
                docs_path, 
                glob="**/*.md",  # Recursive search
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""]
            )
            
            split_docs = text_splitter.split_documents(documents)
            
            # Add metadata extracted from folder structure
            for doc in split_docs:
                source_path = doc.metadata.get('source', '')
                
                # Extract year, quarter, and company from path structure
                # Expected structure: docs/YYYY/QX/COMPANY/filename.md
                path_parts = source_path.replace('\\', '/').split('/')
                
                # Find the position of 'docs' folder and extract from there
                try:
                    docs_index = next(i for i, part in enumerate(path_parts) if part == 'docs')
                    
                    if len(path_parts) > docs_index + 3:
                        year_from_path = path_parts[docs_index + 1]
                        quarter_from_path = path_parts[docs_index + 2]
                        company_from_path = path_parts[docs_index + 3]
                        
                        # Use extracted values or fallback to instance values
                        doc.metadata['year'] = int(year_from_path) if year_from_path.isdigit() else self.year
                        doc.metadata['quarter'] = quarter_from_path if quarter_from_path.startswith('Q') else self.quarter
                        doc.metadata['company_code'] = company_from_path.upper() if company_from_path else self.company_code
                    else:
                        # Fallback: extract from filename if folder structure not as expected
                        filename = os.path.basename(source_path)
                        company_code = filename.split('_')[0] if '_' in filename else 'UNKNOWN'
                        doc.metadata['company_code'] = self.company_code or company_code.upper()
                        doc.metadata['quarter'] = self.quarter
                        doc.metadata['year'] = self.year
                        
                except (StopIteration, ValueError, IndexError):
                    # Fallback to instance values or filename extraction
                    filename = os.path.basename(source_path)
                    company_code = filename.split('_')[0] if '_' in filename else 'UNKNOWN'
                    doc.metadata['company_code'] = self.company_code or company_code.upper()
                    doc.metadata['quarter'] = self.quarter
                    doc.metadata['year'] = self.year
                
                # Add additional metadata
                doc.metadata['document_type'] = 'research_report'
                doc.metadata['source_file'] = os.path.basename(source_path)
                
                logger.debug(f"Processed document: {doc.metadata}")
            
            logger.info(f"Loaded {len(split_docs)} document chunks from {docs_path}")
            return split_docs
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def add_documents_to_store(self, documents: List[Document]):
        """Add documents to the vector store"""
        try:
            if documents:
                self.vectorstore.add_documents(documents)
                logger.info(f"Added {len(documents)} documents to vector store")
            else:
                logger.warning("No documents to add to vector store")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
    
    def setup_vector_store(self, docs_path: str = "./docs"):
        """Initialize the vector store with research documents"""
        try:
            # Check if vector store already has documents
            collection = self.client.get_collection(self.collection_name)
            if collection.count() > 0:
                logger.info(f"Vector store already contains {collection.count()} documents")
                return
        except:
            # Collection doesn't exist yet, that's fine
            pass
          # Load and add documents
        docs_directory = os.path.join(os.path.dirname(__file__), "..", docs_path)
        if os.path.exists(docs_directory):
            documents = self.load_documents_from_directory(docs_directory)
            if documents:
                self.add_documents_to_store(documents)
            else:
                logger.warning(f"No documents found in {docs_directory}")
        else:
            logger.error(f"Docs directory not found: {docs_directory}")
    
    # private
    def __search_similar_documents(self, query: str, company_code: str = None, k: int = 5) -> List[Document]:
        """Search for similar documents in the vector store"""
        try:
            # Build filter if company code is specified
            filter_dict = None
            if company_code:
                filter_dict = {"company_code": company_code}
            
            # Search similar documents
            results = self.vectorstore.similarity_search(
                query, 
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_context_for_company(self, company_code: str, query: str = "", k: int = 10) -> str:
        """Get relevant context for a specific company"""
        try:
            # If no specific query, get general company information
            search_query = query if query else f"{company_code} financial performance business overview"
            
            # Search for relevant documents
            docs = self.__search_similar_documents(search_query, company_code, k)
            
            if not docs:
                return f"No research context found for {company_code}"
            
            # Combine the content from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs):
                content = doc.page_content.strip()
                if content:
                    context_parts.append(f"Context {i+1}:\n{content}")
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"Retrieved {len(docs)} context documents for {company_code}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for {company_code}: {e}")
            return f"Error retrieving context for {company_code}: {str(e)}"
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            collection = self.client.get_collection(self.collection_name)
            return {
                "total_documents": collection.count(),
                "collection_name": self.collection_name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

# Global instances dictionary for different collections
research_vectorstores = {}

def get_research_vectorstore(company_code: str = None, quarter: str = None, year: int = None) -> ResearchVectorStore:
    """Get or create a research vector store instance for specific company/quarter/year"""
    global research_vectorstores
    
    # Create a key for the specific collection
    if company_code and quarter and year:
        key = f"{company_code}_{quarter}_{year}"
    else:
        key = "default"
    
    # Return existing instance or create new one
    if key not in research_vectorstores:
        research_vectorstores[key] = ResearchVectorStore(
            company_code=company_code,
            quarter=quarter,
            year=year
        )
        research_vectorstores[key].setup_vector_store()
    
    return research_vectorstores[key]

def discover_and_initialize_all_vectorstores(docs_base_path: str = "./docs"):
    """Discover all company/quarter/year combinations and initialize vector stores for each"""
    logger.info("🔍 Discovering all company/quarter/year combinations in docs folder...")
    
    # Get absolute path to docs directory
    docs_directory = os.path.join(os.path.dirname(__file__), "..", docs_base_path)
    if not os.path.exists(docs_directory):
        logger.error(f"Docs directory not found: {docs_directory}")
        return []
    
    initialized_stores = []
    
    try:
        # Walk through year folders
        for year_folder in os.listdir(docs_directory):
            year_path = os.path.join(docs_directory, year_folder)
            
            # Skip if not a directory or not a year (4 digits)
            if not os.path.isdir(year_path) or not year_folder.isdigit() or len(year_folder) != 4:
                continue
            
            year = int(year_folder)
            logger.info(f"📅 Found year: {year}")
            
            # Walk through quarter folders
            for quarter_folder in os.listdir(year_path):
                quarter_path = os.path.join(year_path, quarter_folder)
                
                # Skip if not a directory or not a quarter (Q1, Q2, Q3, Q4)
                if not os.path.isdir(quarter_path) or not quarter_folder.startswith('Q'):
                    continue
                
                quarter = quarter_folder
                logger.info(f"📊 Found quarter: {quarter}")
                
                # Walk through company folders
                for company_folder in os.listdir(quarter_path):
                    company_path = os.path.join(quarter_path, company_folder)
                    
                    # Skip if not a directory
                    if not os.path.isdir(company_path):
                        continue
                    
                    company_code = company_folder.upper()
                    
                    # Check if there are any .md files in this company folder
                    md_files = [f for f in os.listdir(company_path) if f.endswith('.md')]
                    if not md_files:
                        logger.warning(f"⚠️ No .md files found in {company_path}")
                        continue
                    
                    logger.info(f"🏢 Found company: {company_code} with {len(md_files)} documents")
                    
                    # Initialize vector store for this combination
                    try:
                        vectorstore = get_research_vectorstore(company_code, quarter, year)
                        stats = vectorstore.get_collection_stats()
                        
                        initialized_stores.append({
                            "company_code": company_code,
                            "quarter": quarter,
                            "year": year,
                            "collection_name": vectorstore.collection_name,
                            "document_count": stats.get("total_documents", 0),
                            "md_files": md_files
                        })
                        
                        logger.info(f"✅ Initialized {company_code}_{quarter}_{year}: {stats}")
                        
                    except Exception as e:
                        logger.error(f"❌ Error initializing {company_code}_{quarter}_{year}: {e}")
    
    except Exception as e:
        logger.error(f"Error discovering folders: {e}")
    
    logger.info(f"🎉 Successfully initialized {len(initialized_stores)} vector store collections")
    return initialized_stores

def initialize_vector_store(company_code: str = None, quarter: str = None, year: int = None):
    """Initialize the vector store for specific company/quarter/year - call this on startup"""
    if company_code and quarter and year:
        # Initialize specific vector store
        logger.info(f"Initializing specific research vector store for {company_code}_{quarter}_{year}...")
        vectorstore = get_research_vectorstore(company_code, quarter, year)
        stats = vectorstore.get_collection_stats()
        logger.info(f"Vector store stats: {stats}")
        return vectorstore
    else:
        # Auto-discover and initialize all vector stores
        return discover_and_initialize_all_vectorstores()
