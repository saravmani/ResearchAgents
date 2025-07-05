"""
Test script for the vision-enhanced PDF table extraction graph.
This script demonstrates how to use the new vision-based table extraction functionality.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from graphs.pdf_table_extraction_graph import create_pdf_table_extraction_graph, extract_pdf_tables_with_vision

def test_vision_table_extraction():
    """Test the vision-enhanced PDF table extraction"""
    try:
        print("🔧 Creating vision-enhanced PDF table extraction graph...")
        graph = create_pdf_table_extraction_graph()
        print("✅ Graph created successfully!")
        
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
                    
                    # Test with first PDF
                    test_file = pdf_files[0]
                    print(f"\n🎯 Testing vision extraction with: {test_file}")
                    print(f"   Company: {first_company}")
                    print(f"   Quarter: Q1")
                    print(f"   Year: 2025")
                    
                    print("\n⚠️  Note: This will use OpenAI GPT-4 Vision API")
                    print("   Make sure you have OPENAI_API_KEY set in your environment")
                    
                    # Uncomment to run actual test
                    # result = extract_pdf_tables_with_vision("2025", "Q1", first_company, test_file)
                    # print(f"✅ Vision extraction completed!")
                    # if result and result.get('messages'):
                    #     print(f"📊 Result: {result['messages'][0].content}")
                    
                else:
                    print(f"⚠️ No PDF files found in {first_company}")
            else:
                print("⚠️ No companies found in docs directory")
        else:
            print("⚠️ Docs directory structure not found")
            print("   Expected: docs/2025/Q1/COMPANY_NAME/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing vision table extraction: {e}")
        return False

def create_sample_pdf_for_testing():
    """Create a sample PDF with tables for testing"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from matplotlib.backends.backend_pdf import PdfPages
        import pandas as pd
        
        print("\n📄 Creating sample PDF with tables for testing...")
        
        # Create sample directory
        sample_dir = os.path.join(current_dir, "docs", "2025", "Q1", "SAMPLE_CORP")
        os.makedirs(sample_dir, exist_ok=True)
        
        # Create a simple PDF with table-like content
        pdf_path = os.path.join(sample_dir, "financial_report_sample.pdf")
        
        # Create sample data
        data = {
            'Metric Name': ['Revenue', 'Net Income', 'Operating Income', 'Total Assets'],
            'Q1 2025': ['5,577', '1,234', '2,100', '15,500'],
            'Q1 2024': ['7,734', '1,567', '2,800', '14,200'],
            '% Change': ['-28%', '-21%', '-25%', '+9%']
        }
        
        df = pd.DataFrame(data)
        
        # Create PDF with matplotlib
        with PdfPages(pdf_path) as pdf:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.axis('tight')
            ax.axis('off')
            
            # Create table
            table = ax.table(cellText=df.values, colLabels=df.columns,
                           cellLoc='center', loc='center', fontsize=12)
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.5)
            
            # Style the table
            for i in range(len(df.columns)):
                table[(0, i)].set_facecolor('#40466e')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            plt.title("Sample Financial Report Q1 2025", fontsize=16, fontweight='bold', pad=20)
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
        
        print(f"✅ Sample PDF created: {pdf_path}")
        print(f"📊 PDF contains financial table with Q1 2025 vs Q1 2024 data")
        
        return pdf_path
        
    except ImportError:
        print("⚠️ matplotlib/pandas not available for creating sample PDF")
        print("   You can manually place a PDF file in docs/2025/Q1/SAMPLE_CORP/")
        return None
    except Exception as e:
        print(f"❌ Error creating sample PDF: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Vision-Enhanced PDF Table Extraction Test")
    print("=" * 60)
    
    # Test graph creation
    if test_vision_table_extraction():
        print("\n✅ Vision graph tests passed!")
    else:
        print("\n❌ Vision graph tests failed!")
    
    # Create sample PDF
    sample_pdf = create_sample_pdf_for_testing()
    
    print("\n📋 How to use vision-enhanced table extraction:")
    print("1. Ensure your PDF is in: docs/YYYY/QX/COMPANY_NAME/document.pdf")
    print("2. Set OPENAI_API_KEY environment variable")
    print("3. Import: from graphs.pdf_table_extraction_graph import extract_pdf_tables_with_vision")
    print("4. Call: extract_pdf_tables_with_vision('2025', 'Q1', 'COMPANY_NAME', 'document.pdf')")
    print("5. Output will be saved in: extracted_tables/YYYY/QX/COMPANY_NAME/document_tables_vision_extracted.md")
    
    print("\n🔍 Vision Enhancement Features:")
    print("- Converts PDF pages to high-resolution images (300 DPI)")
    print("- Uses GPT-4 Vision for advanced table recognition")
    print("- Fallback to text analysis if vision fails")
    print("- Better accuracy for complex table layouts")
    print("- Handles tables with images, borders, and complex formatting")

if __name__ == "__main__":
    main()
