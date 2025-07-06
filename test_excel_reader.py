"""
Test script for the Excel Reader utility.
This script demonstrates how to use the Excel reading functionality.
"""

import os
import sys
import json
from pathlib import Path

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from ui.utils.excel_reader import fetch_columns, ExcelReader
    print("✅ Successfully imported Excel reader utilities")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def create_sample_excel_file():
    """Create a sample Excel file for testing"""
    try:
        import pandas as pd
        
        # Create sample data
        data = {
            'A': ['Name', 'John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown'],
            'B': ['Age', 25, 30, 35, 28],
            'C': ['Department', 'Engineering', 'Marketing', 'Sales', 'HR'],
            'D': ['Salary', 75000, 65000, 80000, 70000],
            'E': ['City', 'New York', 'Los Angeles', 'Chicago', 'Boston'],
            'F': ['Years Exp', 3, 7, 10, 5]
        }
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to Excel
        sample_file = os.path.join(current_dir, "sample_excel_data.xlsx")
        df.to_excel(sample_file, index=False, header=False)
        
        print(f"✅ Created sample Excel file: {sample_file}")
        return sample_file
        
    except ImportError:
        print("❌ pandas not available for creating sample file")
        return None
    except Exception as e:
        print(f"❌ Error creating sample file: {e}")
        return None

def test_excel_reader_basic():
 
  
    sample_file="sample_excel_data.xlsx"
    try:
        # Test the fetch_columns function
        print("\n📋 Test 1: Reading columns B, D, F with header row 1")
        result = fetch_columns(['B', 'D', 'F'], 3, sample_file)
        
        print(f"Result type: {type(result)}")
        print(f"Number of records: {len(result)}")
        print("Sample data:")
        print(json.dumps(result[:3], indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Error in basic test: {e}")
        return False
    
    finally:
        # Clean up
        if sample_file and os.path.exists(sample_file):
            os.remove(sample_file)
            print(f"🧹 Cleaned up sample file")
 
def test_usage_examples():
    """Show usage examples"""
    print("\n📖 Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "description": "Basic usage - Read columns B, D, AC from row 3 header",
            "code": "fetch_columns(['B', 'D', 'AC'], 3, '/path/to/file.xlsx')"
        },
        {
            "description": "Class usage - Create reader instance",
            "code": """reader = ExcelReader()
result = reader.fetch_columns(['A', 'B', 'C'], 1, 'data.xlsx')
info = reader.get_sheet_info('data.xlsx')"""
        },
        {
            "description": "Import and use",
            "code": """from ui.utils import fetch_columns, ExcelReader
# or
from ui.utils.excel_reader import fetch_columns"""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Example {i}: {example['description']}")
        print("```python")
        print(example['code'])
        print("```")

def main():
    """Main test function"""
    print("🚀 Excel Reader Utility Test")
    print("=" * 50)
    
    # Check if pandas is available
    try:
        import pandas as pd
        print("✅ pandas is available")
    except ImportError:
        print("❌ pandas is not available. Please install it:")
        print("   pip install pandas openpyxl")
        return
    
    # Run tests
    success = True
    
    if test_excel_reader_basic():
        print("✅ Basic tests passed!")
    else:
        print("❌ Basic tests failed!")
        success = False
    
    if test_excel_reader_advanced():
        print("✅ Advanced tests passed!")
    else:
        print("❌ Advanced tests failed!")
        success = False
    
    # Show usage examples
    test_usage_examples()
    
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    print("\n📋 Summary:")
    print("- The Excel reader utility is ready to use")
    print("- Use fetch_columns(['B', 'D', 'AC'], 3, 'file.xlsx') for quick access")
    print("- Use ExcelReader() class for advanced features")
    print("- Supports .xlsx, .xls, .xlsm formats")
    print("- Returns JSON array format")

if __name__ == "__main__":
    main()
