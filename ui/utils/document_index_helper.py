import os
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIndexHelper:
    """
    A utility class for indexing documents and performing similarity search using ChromaDB.
    Provides simple methods to index documents, search content, and manage collections.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the DocumentIndexHelper.
        
        Args:
            persist_directory (str): Directory to persist the ChromaDB database
        """
        self.persist_directory = persist_directory
        
        # Initialize embeddings using SentenceTransformers
        self.embeddings = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info(f"DocumentIndexHelper initialized with persist directory: {persist_directory}")
    
    def _load_document(self, document_path: str) -> List[Document]:
        """
        Load a document based on its file extension.
        
        Args:
            document_path (str): Path to the document file
            
        Returns:
            List[Document]: List of loaded documents
        """
        if not os.path.exists(document_path):
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        file_extension = os.path.splitext(document_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                loader = PyMuPDFLoader(document_path)
            elif file_extension == '.txt':
                loader = TextLoader(document_path, encoding='utf-8')
            elif file_extension in ['.docx', '.doc']:
                loader = UnstructuredWordDocumentLoader(document_path)
            else:
                # Try to load as text file for other extensions
                loader = TextLoader(document_path, encoding='utf-8')
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} document(s) from {document_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading document {document_path}: {str(e)}")
            raise
    def _get_or_create_vectorstore(self, collection_name: str) -> Chroma:
        """
        Get or create a vectorstore for the given collection name.
        
        Note: Chroma automatically connects to existing collections or creates new ones
        when instantiated with a collection name.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Chroma: Vectorstore instance connected to the collection
        """
        # Check if collection already exists
        collection_exists = False
        document_count = 0
        
        try:
            existing_collection = self.client.get_collection(collection_name)
            collection_exists = True
            document_count = existing_collection.count()
            logger.info(f"Using existing collection '{collection_name}' with {document_count} documents")
        except Exception:
            logger.info(f"Creating new collection '{collection_name}'")
        
        # Create vectorstore instance (connects to existing or creates new collection)
        vectorstore = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
        
        return vectorstore
    def index_document(self, document_path: str, collection_name: str) -> Dict[str, Any]:
        """
        Chunk the given document and store it into the vector database.
        If collection doesn't exist, create it. If collection exists, use it.
        
        Args:
            document_path (str): Full path to the document to index (single document)
            collection_name (str): Name of the collection to store documents
            
        Returns:
            Dict[str, Any]: Status information about the indexing operation
        """
        try:
            # Ensure we have an absolute path
            document_path = os.path.abspath(document_path)
             
            
            # Load the document
            documents = self._load_document(document_path)
            
            if not documents:
                return {
                    "success": False,
                    "error": f"No content could be loaded from {document_path}",
                    "chunks_created": 0,
                    "collection_name": collection_name
                }
            
            # Add metadata to documents
            filename = os.path.basename(document_path)
            for doc in documents:
                doc.metadata.update({
                    "source_file": filename,
                    "source_path": document_path,
                    "collection": collection_name,
                    "file_type": os.path.splitext(filename)[1].lower()
                })
            
            # Split documents into chunks
            document_chunks = self.text_splitter.split_documents(documents)
            
            if not document_chunks:
                return {
                    "success": False,
                    "error": f"No chunks could be created from {document_path}",
                    "chunks_created": 0,
                    "collection_name": collection_name
                }
            
            logger.info(f"Created {len(document_chunks)} chunks from document")
            
            # Get or create vectorstore for the collection
            vectorstore = self._get_or_create_vectorstore(collection_name)
            
            # Add documents to vector store
            vectorstore.add_documents(document_chunks)
            logger.info(f"Successfully indexed {len(document_chunks)} chunks into collection '{collection_name}'")
            
            return {
                "success": True,
                "message": f"Successfully indexed document {filename}",
                "chunks_created": len(document_chunks),
                "collection_name": collection_name,
                "source_file": filename,
                "source_path": document_path
            }
            
        except Exception as e:
            error_msg = f"Error indexing document {document_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "chunks_created": 0,
                "collection_name": collection_name
            }
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists in the vector database.
        
        Args:
            collection_name (str): Name of the collection to check
            
        Returns:
            bool: True if collection exists, False otherwise
        """
        try:
            self.client.get_collection(collection_name)
            return True
        except Exception:
            return False
    
    def search_data(self, query: str, collection_name: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the context and return the list of relevant content chunks.
        
        Args:
            query (str): Search query
            collection_name (str): Name of the collection to search in
            k (int): Number of top results to return (default: 5)
            
        Returns:
            List[Dict[str, Any]]: List of relevant content chunks with metadata
        """
        try:
            logger.info(f"Searching in collection '{collection_name}' for query: {query[:50]}...")
            
            # Check if collection exists
            try:
                self.client.get_collection(collection_name)
            except Exception:
                logger.warning(f"Collection '{collection_name}' not found")
                return []
            
            # Get vectorstore for the collection
            vectorstore = self._get_or_create_vectorstore(collection_name)
            
            # Perform similarity search
            search_results = vectorstore.similarity_search(query, k=k)
            
            if not search_results:
                logger.info(f"No results found for query in collection '{collection_name}'")
                return []
            
            # Format results
            formatted_results = []
            for i, doc in enumerate(search_results):
                result = {
                    "rank": i + 1,
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source_file": doc.metadata.get("source_file", "unknown"),
                    "chunk_length": len(doc.page_content)
                }
                formatted_results.append(result)
            
            logger.info(f"Found {len(formatted_results)} relevant chunks")
            return formatted_results
            
        except Exception as e:
            error_msg = f"Error searching in collection '{collection_name}': {str(e)}"
            logger.error(error_msg)
            return []
    
    def delete_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Delete a collection from the vector database.
        
        Args:
            collection_name (str): Name of the collection to delete
            
        Returns:
            Dict[str, Any]: Status information about the deletion operation
        """
        try:
            logger.info(f"Attempting to delete collection: {collection_name}")
            
            # Check if collection exists
            try:
                collection = self.client.get_collection(collection_name)
                document_count = collection.count()
            except Exception:
                return {
                    "success": False,
                    "error": f"Collection '{collection_name}' not found",
                    "collection_name": collection_name
                }
            
            # Delete the collection
            self.client.delete_collection(collection_name)
            
            logger.info(f"Successfully deleted collection '{collection_name}' with {document_count} documents")
            
            return {
                "success": True,
                "message": f"Successfully deleted collection '{collection_name}'",
                "documents_deleted": document_count,
                "collection_name": collection_name
            }
            
        except Exception as e:
            error_msg = f"Error deleting collection '{collection_name}': {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "collection_name": collection_name
            }
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections in the vector database.
        
        Returns:
            List[Dict[str, Any]]: List of collections with their statistics
        """
        try:
            collections = self.client.list_collections()
            
            collection_info = []
            for collection in collections:
                try:
                    col_obj = self.client.get_collection(collection.name)
                    collection_info.append({
                        "name": collection.name,
                        "document_count": col_obj.count(),
                        "metadata": collection.metadata
                    })
                except Exception as e:
                    logger.warning(f"Error getting info for collection {collection.name}: {e}")
                    collection_info.append({
                        "name": collection.name,
                        "document_count": "unknown",
                        "metadata": {}
                    })
            
            logger.info(f"Found {len(collection_info)} collections")
            return collection_info
            
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            Dict[str, Any]: Collection statistics
        """
        try:
            collection = self.client.get_collection(collection_name)
            
            return {
                "collection_name": collection_name,
                "document_count": collection.count(),
                "metadata": collection.metadata,
                "persist_directory": self.persist_directory
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for collection '{collection_name}': {str(e)}")
            return {
                "collection_name": collection_name,
                "error": str(e)
            }


# Convenience functions for easy usage
_helper_instance = None

def get_document_helper(persist_directory: str = "./chroma_db") -> DocumentIndexHelper:
    """
    Get a global instance of DocumentIndexHelper.
    
    Args:
        persist_directory (str): Directory to persist the ChromaDB database
        
    Returns:
        DocumentIndexHelper: Global helper instance
    """
    global _helper_instance
    if _helper_instance is None:
        _helper_instance = DocumentIndexHelper(persist_directory)
    return _helper_instance

def index_document(document_path: str, collection_name: str, persist_directory: str = "./chroma_db") -> Dict[str, Any]:
    """
    Convenience function to index a document.
    
    Args:
        document_path (str): Path to the document to index
        collection_name (str): Name of the collection to store documents
        persist_directory (str): Directory to persist the ChromaDB database
        
    Returns:
        Dict[str, Any]: Status information about the indexing operation
    """
    helper = get_document_helper(persist_directory)
    return helper.index_document(document_path, collection_name)

def search_data(query: str, collection_name: str, k: int = 5, persist_directory: str = "./chroma_db") -> List[Dict[str, Any]]:
    """
    Convenience function to search for data.
    
    Args:
        query (str): Search query
        collection_name (str): Name of the collection to search in
        k (int): Number of top results to return
        persist_directory (str): Directory to persist the ChromaDB database
        
    Returns:
        List[Dict[str, Any]]: List of relevant content chunks with metadata
    """
    helper = get_document_helper(persist_directory)
    return helper.search_data(query, collection_name, k)

def delete_collection(collection_name: str, persist_directory: str = "./chroma_db") -> Dict[str, Any]:
    """
    Convenience function to delete a collection.
    
    Args:
        collection_name (str): Name of the collection to delete
        persist_directory (str): Directory to persist the ChromaDB database
        
    Returns:
        Dict[str, Any]: Status information about the deletion operation
    """
    helper = get_document_helper(persist_directory)
    return helper.delete_collection(collection_name)


if __name__ == "__main__":
    # Example usage
    helper = DocumentIndexHelper()
    
    # Example: Index a document
    # result = helper.index_document("path/to/document.pdf", "my_collection")
    # print(f"Indexing result: {result}")
    
    # Example: Search for content
    # results = helper.search_data("search query", "my_collection", k=3)
    # print(f"Search results: {results}")
    
    # Example: List all collections
    collections = helper.list_collections()
    print(f"Available collections: {collections}")
