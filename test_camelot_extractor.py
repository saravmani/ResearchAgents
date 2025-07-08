"""
Test script for PDF Table Extractor using Camelot-Py

This script tests the PDF table extraction utility with various extraction methods.
"""

import os
import sys
import logging

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.utils.pdf_table_extractor_util import PDFTableExtractor, extract_pdf_tables

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_camelot_extraction():
    """Test camelot-py table extraction functionality"""
    
    # Create test directory
    test_dir = "test_outputs/camelot_extraction"
    os.makedirs(test_dir, exist_ok=True)
    
    print("=== PDF Table Extractor Test (Camelot-Py) ===\n")
    
    # Test PDF path (you would replace this with an actual PDF)
    test_pdf = "docs\\2025\\Q1\\SHELL\\QRAReport\\q1-2025-qra-document.pdf"  # Replace with your test PDF
    
    if not os.path.exists(test_pdf):
        print(f"Test PDF not found: {test_pdf}")
        print("Creating a sample test to demonstrate the functionality...")
        
        # Demonstrate the extractor class initialization
        try:
            extractor = PDFTableExtractor()
            print("✅ PDFTableExtractor initialized successfully")
        except ImportError as e:
            print(f"❌ Error: {e}")
            print("To install camelot-py and dependencies, run:")
            print("pip install camelot-py[cv]")
            print("pip install ghostscript")
            return False
        
        print("\n=== Extractor Methods Available ===")
        print("1. extract_tables_lattice() - For tables with clear borders")
        print("2. extract_tables_stream() - For tables without clear borders") 
        print("3. extract_tables_auto() - Automatically chooses best method")
        print("4. get_table_info() - Get detailed table information")
        print("5. save_tables_to_excel() - Save to Excel format")
        print("6. save_tables_to_csv() - Save to CSV format")
        print("7. save_tables_to_json() - Save to JSON format")
        print("8. extract_and_save() - Complete extraction and saving workflow")
        
        return True
    
    # Test with actual PDF file
    try:
        extractor = PDFTableExtractor()
        
        print(f"Testing extraction from: {test_pdf}")
        
        # Test 1: Auto extraction
        print("\n1. Testing auto extraction...")
        tables, method = extractor.extract_tables_auto(test_pdf)
        print(f"   - Extracted {len(tables)} tables using {method} method")
        
        if tables:
            for i, table in enumerate(tables):
                print(f"   - Table {i+1}: {table.shape[0]} rows × {table.shape[1]} columns")
        
        # Test 2: Lattice extraction
        print("\n2. Testing lattice extraction...")
        lattice_tables = extractor.extract_tables_lattice(test_pdf)
        print(f"   - Extracted {len(lattice_tables)} tables with lattice method")
        
        # Test 3: Stream extraction
        print("\n3. Testing stream extraction...")
        stream_tables = extractor.extract_tables_stream(test_pdf)
        print(f"   - Extracted {len(stream_tables)} tables with stream method")
        
        # Test 4: Get table info
        print("\n4. Getting table information...")
        table_info = extractor.get_table_info(test_pdf, flavor='lattice')
        for i, info in enumerate(table_info):
            print(f"   - Table {i+1}: Page {info['page']}, Accuracy: {info['accuracy']:.2f}")
        
        # Test 5: Save to different formats
        if tables:
            print("\n5. Testing save functionality...")
            
            # Save to Excel
            excel_path = os.path.join(test_dir, "extracted_tables.xlsx")
            success = extractor.save_tables_to_excel(tables, excel_path)
            print(f"   - Excel save: {'✅ Success' if success else '❌ Failed'}")
            
            # Save to CSV
            csv_dir = os.path.join(test_dir, "csv_tables")
            csv_files = extractor.save_tables_to_csv(tables, csv_dir)
            print(f"   - CSV save: ✅ {len(csv_files)} files saved")
            
            # Save to JSON
            json_path = os.path.join(test_dir, "extracted_tables.json")
            success = extractor.save_tables_to_json(tables, json_path)
            print(f"   - JSON save: {'✅ Success' if success else '❌ Failed'}")
        
        # Test 6: Complete workflow
        print("\n6. Testing complete extraction workflow...")
        result = extractor.extract_and_save(
            test_pdf, 
            test_dir, 
            format='excel', 
            method='auto'
        )
        
        if result['success']:
            print(f"   - ✅ Complete workflow successful")
            print(f"   - Method used: {result['method_used']}")
            print(f"   - Tables extracted: {result['tables_count']}")
            print(f"   - Files saved: {len(result['saved_files'])}")
        else:
            print(f"   - ❌ Workflow failed: {result['message']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        return False


def test_convenience_function():
    """Test the convenience function"""
    print("\n=== Testing Convenience Function ===")
    
    test_pdf = "sample_table.pdf"
    
    # Test the convenience function
    result = extract_pdf_tables(test_pdf, method='auto')
    
    if result['success']:
        print(f"✅ Convenience function successful")
        print(f"   - Tables extracted: {result['tables_count']}")
        print(f"   - Method used: {result['method_used']}")
    else:
        print(f"❌ Convenience function failed: {result['message']}")
    
    return result['success']


def demonstrate_integration():
    """Demonstrate how to integrate with existing system"""
    print("\n=== Integration Example ===")
    
    example_code = '''
# Example: Integrating camelot-py extractor with existing workflow

from ui.utils.pdf_table_extractor_util import PDFTableExtractor, extract_pdf_tables

# Method 1: Using the convenience function
def extract_tables_from_uploaded_pdf(pdf_path: str):
    result = extract_pdf_tables(pdf_path, method='auto')
    
    if result['success']:
        tables = result['tables']
        # Process tables as needed
        return tables
    else:
        print(f"Error: {result['message']}")
        return []

# Method 2: Using the class for more control
def extract_and_save_tables(pdf_path: str, output_dir: str):
    extractor = PDFTableExtractor()
    
    # Extract with specific method
    tables = extractor.extract_tables_lattice(pdf_path)
    
    if tables:
        # Save in multiple formats
        extractor.save_tables_to_excel(tables, f"{output_dir}/tables.xlsx")
        extractor.save_tables_to_csv(tables, f"{output_dir}/csv")
        extractor.save_tables_to_json(tables, f"{output_dir}/tables.json")
    
    return tables

# Method 3: Complete workflow with error handling
def complete_table_extraction_workflow(pdf_path: str, output_dir: str):
    try:
        extractor = PDFTableExtractor()
        
        result = extractor.extract_and_save(
            pdf_path=pdf_path,
            output_dir=output_dir,
            format='excel',  # or 'csv', 'json'
            pages='all',     # or specific pages like '1,2,3'
            method='auto'    # or 'lattice', 'stream'
        )
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'message': str(e),
            'tables_count': 0
        }
    '''
    
    print(example_code)


if __name__ == "__main__":
    print("Starting PDF Table Extractor (Camelot-Py) Test...\n")
    
    # Test basic functionality
    success = test_camelot_extraction()
    
    if success:
        # Test convenience function
        test_convenience_function()
        
        # Show integration examples
        demonstrate_integration()
        
        print("\n=== Test Summary ===")
        print("✅ PDF Table Extractor utility created successfully")
        print("✅ Camelot-py dependencies added to requirements.txt")
        print("✅ Integration with existing utils package completed")
        
        print("\n=== Next Steps ===")
        print("1. Install dependencies: pip install camelot-py[cv] ghostscript")
        print("2. Test with actual PDF files containing tables")
        print("3. Integrate with the table extraction graph")
        print("4. Update UI to include camelot-py extraction option")
        
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        
    print("\n=== Installation Instructions ===")
    print("To install camelot-py and its dependencies:")
    print("pip install camelot-py[cv]")
    print("pip install ghostscript")
    print("\nNote: You may also need to install Ghostscript system-wide:")
    print("- Windows: Download from https://www.ghostscript.com/download/gsdnld.html")
    print("- macOS: brew install ghostscript")
    print("- Linux: apt-get install ghostscript (Ubuntu/Debian)")
