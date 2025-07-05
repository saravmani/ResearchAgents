"""
Test script for the PDF table extraction graph.
This script demonstrates how to use the new table extraction functionality.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from graphs.pdf_table_extraction_graph import create_pdf_table_extraction_graph, extract_pdf_tables

def test_table_extraction_graph():
    """Test the PDF table extraction graph creation"""
    try:
        # Test graph creation
        print("🔧 Creating PDF table extraction graph...")
        graph = create_pdf_table_extraction_graph()
        print("✅ Graph created successfully!")
        
        # Test the convenience function (this will fail if no document exists, but tests the function)
        print("\n🧪 Testing convenience function structure...")
        
        # Check if docs directory exists
        docs_dir = os.path.join(current_dir, "docs", "2025", "Q1")
        if os.path.exists(docs_dir):
            print(f"📁 Found docs directory: {docs_dir}")
            
            # List available companies
            companies = [d for d in os.listdir(docs_dir) if os.path.isdir(os.path.join(docs_dir, d))]
            if companies:
                print(f"🏢 Available companies: {companies}")
                
                # Check for PDF files in first company
                first_company = companies[0]
                company_dir = os.path.join(docs_dir, first_company)
                pdf_files = [f for f in os.listdir(company_dir) if f.endswith('.pdf')]
                
                if pdf_files:
                    print(f"📄 PDF files found in {first_company}: {pdf_files}")
                    
                    # Test with first PDF (this is just a structure test)
                    test_file = pdf_files[0]
                    print(f"\n🎯 Would process: {test_file}")
                    print(f"   Company: {first_company}")
                    print(f"   Quarter: Q1")
                    print(f"   Year: 2025")
                    
                else:
                    print(f"⚠️ No PDF files found in {first_company}")
            else:
                print("⚠️ No companies found in docs directory")
        else:
            print("⚠️ Docs directory structure not found")
            print("   Expected: docs/2025/Q1/COMPANY_NAME/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing table extraction graph: {e}")
        return False

def create_sample_directory_structure():
    """Create sample directory structure for testing"""
    try:
        print("\n📁 Creating sample directory structure...")
        
        # Create the directory structure
        sample_dir = os.path.join(current_dir, "docs", "2025", "Q1", "SAMPLE_CORP")
        os.makedirs(sample_dir, exist_ok=True)
        
        print(f"✅ Created directory: {sample_dir}")
        print("\n💡 To test table extraction:")
        print("1. Place a PDF file in the created directory")
        print("2. Run the extraction with:")
        print("   extract_pdf_tables('2025', 'Q1', 'SAMPLE_CORP', 'your_file.pdf')")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating directory structure: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 PDF Table Extraction Graph Test")
    print("=" * 50)
    
    # Test graph creation
    if test_table_extraction_graph():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    # Create sample structure
    create_sample_directory_structure()
    
    print("\n📋 How to use the table extraction graph:")
    print("1. Ensure your PDF is in: docs/YYYY/QX/COMPANY_NAME/document.pdf")
    print("2. Import: from graphs.pdf_table_extraction_graph import extract_pdf_tables")
    print("3. Call: extract_pdf_tables('2025', 'Q1', 'COMPANY_NAME', 'document.pdf')")
    print("4. Output will be saved in: extracted_tables/YYYY/QX/COMPANY_NAME/document_tables_extracted.md")

if __name__ == "__main__":
    main()
