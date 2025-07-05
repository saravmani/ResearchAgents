#!/usr/bin/env python3
"""
Test script for document_index_helper.py

This script demonstrates how to use the DocumentIndexHelper for:
1. Indexing documents
2. Searching for content
3. Managing collections
"""

import os
import sys

# Add the parent directory to the Python path to import our utils
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils.document_index_helper import DocumentIndexHelper, index_document, search_data, delete_collection

def test_document_indexing():
    """Test document indexing functionality"""
    print("=" * 60)
    print("Testing Document Index Helper")
    print("=" * 60)
    
    # Initialize the helper
    helper = DocumentIndexHelper(persist_directory="./test_chroma_db")
    
    # Test 1: List existing collections
    print("\n1. Listing existing collections:")
    collections = helper.list_collections()
    print(f"Found {len(collections)} collections:")
    for col in collections:
        print(f"  - {col['name']}: {col['document_count']} documents")
    
    # Test 2: Create a sample text file for testing
    test_file_path = "test_sample_document.txt"
    sample_content = """
# Sample Document for Testing

This is a sample document created for testing the DocumentIndexHelper.

## Introduction
The DocumentIndexHelper is a utility class that provides simple methods for:
- Indexing documents into a vector database
- Searching for relevant content using similarity search
- Managing collections in the vector database

## Features
1. **Document Loading**: Supports PDF, TXT, DOCX, and DOC files
2. **Text Chunking**: Automatically splits documents into manageable chunks
3. **Vector Storage**: Uses ChromaDB for persistent vector storage
4. **Similarity Search**: Performs semantic search using embeddings
5. **Collection Management**: Create, search, and delete collections

## Benefits
- Easy to use API
- Persistent storage
- High-quality embeddings using SentenceTransformers
- Flexible document support

This document contains enough content to demonstrate the chunking and search capabilities.
"""
    
    # Create the test file
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(sample_content)
    
    print(f"\n2. Created test document: {test_file_path}")
    
    # Test 3: Index the document
    print("\n3. Indexing the test document:")
    collection_name = "test_collection"
    result = helper.index_document(test_file_path, collection_name)
    print(f"Indexing result: {result}")
    
    # Test 4: Search for content
    print("\n4. Searching for content:")
    search_queries = [
        "document indexing and vector database",
        "similarity search features",
        "ChromaDB and embeddings",
        "benefits and advantages"
    ]
    
    for query in search_queries:
        print(f"\nQuery: '{query}'")
        results = helper.search_data(query, collection_name, k=2)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"  Result {i} (rank {result['rank']}):")
                print(f"    Content: {result['content'][:100]}...")
                print(f"    Source: {result['source_file']}")
                print(f"    Length: {result['chunk_length']} chars")
        else:
            print("  No results found")
    
    # Test 5: Get collection statistics
    print(f"\n5. Collection statistics for '{collection_name}':")
    stats = helper.get_collection_stats(collection_name)
    print(f"Stats: {stats}")
    
    # Test 6: List collections again to see the new one
    print("\n6. Updated collections list:")
    collections = helper.list_collections()
    for col in collections:
        print(f"  - {col['name']}: {col['document_count']} documents")
    
    # Test 7: Test convenience functions
    print("\n7. Testing convenience functions:")
    
    # Create another test file
    test_file_2 = "test_sample_document_2.txt"
    sample_content_2 = """
# Advanced Features Documentation

This document covers advanced features of the system.

## Vector Search Capabilities
The system uses advanced vector search to find semantically similar content.
This allows for more intelligent search results compared to traditional keyword matching.

## Machine Learning Integration
The system integrates with state-of-the-art machine learning models for:
- Text embedding generation
- Semantic similarity computation
- Content ranking and relevance scoring

## Performance Optimization
- Efficient chunk storage and retrieval
- Optimized embedding models
- Persistent database storage for fast access
"""
    
    with open(test_file_2, 'w', encoding='utf-8') as f:
        f.write(sample_content_2)
    
    # Test convenience function for indexing
    collection_name_2 = "advanced_features"
    result = index_document(test_file_2, collection_name_2)
    print(f"Convenience indexing result: {result}")
    
    # Test convenience function for searching
    results = search_data("machine learning and vector search", collection_name_2, k=2)
    print(f"Convenience search found {len(results)} results")
    
    # Test 8: Clean up (optional)
    cleanup = input("\n8. Do you want to clean up test collections? (y/n): ").lower() == 'y'
    if cleanup:
        print("\nCleaning up test collections:")
        
        # Delete test collections
        delete_result_1 = helper.delete_collection(collection_name)
        print(f"Delete result for '{collection_name}': {delete_result_1}")
        
        delete_result_2 = delete_collection(collection_name_2)
        print(f"Delete result for '{collection_name_2}': {delete_result_2}")
        
        # Remove test files
        for test_file in [test_file_path, test_file_2]:
            if os.path.exists(test_file):
                os.remove(test_file)
                print(f"Removed test file: {test_file}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    helper = DocumentIndexHelper(persist_directory="./test_chroma_db")
    
    # Test 1: Try to index non-existent file
    print("\n1. Testing non-existent file:")
    result = helper.index_document("non_existent_file.pdf", "test_collection")
    print(f"Result: {result}")
    
    # Test 2: Try to search in non-existent collection
    print("\n2. Testing search in non-existent collection:")
    results = helper.search_data("test query", "non_existent_collection")
    print(f"Results: {results}")
    
    # Test 3: Try to delete non-existent collection
    print("\n3. Testing delete non-existent collection:")
    result = helper.delete_collection("non_existent_collection")
    print(f"Result: {result}")
    
    # Test 4: Try to get stats for non-existent collection
    print("\n4. Testing stats for non-existent collection:")
    stats = helper.get_collection_stats("non_existent_collection")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    try:
        test_document_indexing()
        test_error_handling()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
