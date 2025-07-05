#!/usr/bin/env python3
"""
Simple test to verify document indexing with full paths
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.document_index_helper import DocumentIndexHelper

def test_document_indexing():
    """Test the document indexing functionality with full paths"""
    
    print("🔍 Testing Document Indexing with Full Paths")
    print("=" * 50)
    
    # Create a simple test document
    test_content = """
# Test Document for Vector Search

## Introduction
This is a test document to demonstrate the document indexing functionality.
It contains various sections that can be searched and retrieved.

## Key Features
- Document parsing and chunking
- Vector storage with embeddings
- Similarity search capabilities
- Collection management

## Technical Details
The system uses ChromaDB for vector storage and sentence transformers for embeddings.
Documents are split into chunks using RecursiveCharacterTextSplitter.

## Sample Data
Here are some sample financial metrics:
- Revenue: $1.2 million
- Profit margin: 15%
- Growth rate: 8% annually
- Market cap: $50 million

## Conclusion
This document serves as a sample for testing the indexing and search functionality.
"""
    
    # Create test file with full path
    test_filename = "test_document.txt"
    test_file_path = os.path.abspath(test_filename)
    
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print(f"📄 Created test document at: {test_file_path}")
    
    # Initialize the helper
    helper = DocumentIndexHelper(persist_directory="./test_chroma_db")
    
    # Test collection name
    collection_name = "test_full_path_collection"
    
    # Check if collection exists before indexing
    exists_before = helper.collection_exists(collection_name)
    print(f"📊 Collection '{collection_name}' exists before indexing: {exists_before}")
    
    # Index the document using full path
    print(f"\n🔄 Indexing document using full path...")
    result = helper.index_document(test_file_path, collection_name)
    
    print(f"📋 Indexing result:")
    for key, value in result.items():
        print(f"   {key}: {value}")
    
    # Check if indexing was successful
    if result.get("success"):
        print(f"✅ Document indexed successfully!")
        
        # Check collection exists after indexing
        exists_after = helper.collection_exists(collection_name)
        print(f"📊 Collection '{collection_name}' exists after indexing: {exists_after}")
        
        # Get collection stats
        stats = helper.get_collection_stats(collection_name)
        print(f"📈 Collection stats:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Test searching
        print(f"\n🔍 Testing search functionality...")
        search_queries = [
            "financial metrics",
            "revenue profit",
            "technical details",
            "ChromaDB vector storage"
        ]
        
        for query in search_queries:
            print(f"\n🔎 Searching for: '{query}'")
            results = helper.search_data(query, collection_name, k=2)
            
            if results:
                for result in results:
                    print(f"   Rank {result['rank']}: {result['content'][:80]}...")
                    print(f"   Source: {result['source_file']}")
            else:
                print("   No results found")
        
        # Test adding the same document again (should work)
        print(f"\n🔄 Testing adding the same document again...")
        result2 = helper.index_document(test_file_path, collection_name)
        print(f"📋 Second indexing result:")
        for key, value in result2.items():
            print(f"   {key}: {value}")
        
        # Check updated stats
        updated_stats = helper.get_collection_stats(collection_name)
        print(f"📈 Updated collection stats:")
        for key, value in updated_stats.items():
            print(f"   {key}: {value}")
    
    else:
        print(f"❌ Document indexing failed: {result.get('error')}")
    
    # Test with a non-existent file
    print(f"\n🔄 Testing with non-existent file...")
    fake_path = os.path.abspath("non_existent_file.txt")
    result3 = helper.index_document(fake_path, collection_name)
    print(f"📋 Non-existent file result:")
    for key, value in result3.items():
        print(f"   {key}: {value}")
    
    # List all collections
    print(f"\n📚 All collections:")
    all_collections = helper.list_collections()
    for collection in all_collections:
        print(f"   - {collection['name']}: {collection['document_count']} documents")
    
    # Cleanup
    try:
        os.remove(test_file_path)
        print(f"\n🧹 Cleaned up test file: {test_filename}")
    except Exception as e:
        print(f"⚠️ Warning: Could not clean up test file: {e}")
    
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_document_indexing()
