from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, Optional, List, Dict
import fitz  # PyMuPDF for PDF parsing
import io
import os
import sqlite3
import base64
from datetime import datetime
from pathlib import Path

# State for the PDF table extraction workflow
class PDFTableExtractionState(TypedDict):
    messages: Annotated[list, "The conversation messages"]
    year: str
    quarter: str
    company_name: str
    document_name: str
    document_type: str
    document_path: str
    pdf_content: bytes
    total_pages: int
    current_page: int
    page_tables: Annotated[List[Dict], "Tables extracted from each page"]
    accumulated_markdown: str
    processing_stage: str
    error_message: str
    output_path: str

def initialize_table_extraction(state):
    """Initialize the PDF table extraction workflow"""
    year = state.get("year", "")
    quarter = state.get("quarter", "")
    company_name = state.get("company_name", "")
    document_name = state.get("document_name", "")
    document_type = state.get("document_type", "General")
    
    print(f"DEBUG: initialize_table_extraction - {company_name} {quarter} {year} - {document_type} - {document_name}")
    
    # Construct document path based on the directory structure: docs/YYYY/QX/CompanyName/DocumentType/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    docs_dir = os.path.join(parent_dir, "docs")
    
    document_path = os.path.join(docs_dir, year, quarter, company_name.upper(), document_type, document_name)
    
    return {
        "messages": state.get("messages", []),
        "year": year,
        "quarter": quarter,
        "company_name": company_name,
        "document_name": document_name,
        "document_type": document_type,
        "document_path": document_path,
        "pdf_content": b"",
        "total_pages": 0,
        "current_page": 0,
        "page_tables": [],
        "accumulated_markdown": "",
        "processing_stage": "initialized",
        "error_message": "",
        "output_path": ""
    }

def load_pdf_document(state):
    """Load the PDF document and extract basic information"""
    document_path = state.get("document_path", "")
    
    print(f"DEBUG: load_pdf_document - Loading {document_path}")
    
    try:
        if not os.path.exists(document_path):
            error_message = f"Document not found: {document_path}"
            print(f"DEBUG: {error_message}")
            return {
                **state,
                "processing_stage": "load_error",
                "error_message": error_message
            }
        
        # Read PDF content
        with open(document_path, "rb") as f:
            pdf_content = f.read()
        
        # Open PDF to get page count
        pdf_stream = io.BytesIO(pdf_content)
        pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
        total_pages = pdf_document.page_count
        pdf_document.close()
        
        print(f"DEBUG: Successfully loaded PDF with {total_pages} pages")
        
        return {
            **state,
            "pdf_content": pdf_content,
            "total_pages": total_pages,
            "current_page": 0,
            "processing_stage": "loaded"
        }
        
    except Exception as e:
        error_message = f"Error loading PDF document: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "load_error",
            "error_message": error_message
        }

def pdf_page_to_base64_image(pdf_content: bytes, page_number: int, dpi: int = 300) -> str:
    """Convert a PDF page to base64 encoded image for vision model"""
    try:
        pdf_stream = io.BytesIO(pdf_content)
        pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
        
        # Get the page
        page = pdf_document[page_number]
        
        # Create a matrix for higher resolution
        matrix = fitz.Matrix(dpi/72, dpi/72)  # 72 DPI is default, scale up for better quality
        
        # Render page as image
        pix = page.get_pixmap(matrix=matrix)
        img_data = pix.tobytes("png")
        
        # Save the image to local path (optional, for debugging)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        images_dir = os.path.join(parent_dir, "extracted_images")
        os.makedirs(images_dir, exist_ok=True)

        # Create filename for the image
        image_filename = f"page_{page_number + 1}.png"
        image_path = os.path.join(images_dir, image_filename)

        # Save the image
        with open(image_path, "wb") as img_file:
            img_file.write(img_data)

        print(f"DEBUG: Saved page {page_number + 1} image to {image_path}")
        
        pdf_document.close()
        
        # Convert to base64
        base64_image = base64.b64encode(img_data).decode('utf-8')
        return base64_image
        
    except Exception as e:
        print(f"Error converting PDF page to image: {str(e)}")
        return ""

def extract_page_tables(state):
    """Extract tables from the current page using vision model with page image"""
    pdf_content = state.get("pdf_content", b"")
    current_page = state.get("current_page", 0)
    total_pages = state.get("total_pages", 0)
    company_name = state.get("company_name", "")
    document_name = state.get("document_name", "")
    
    print(f"DEBUG: extract_page_tables - Processing page {current_page + 1}/{total_pages}")
    
    if current_page >= total_pages:
        return {
            **state,
            "processing_stage": "completed"
        }
    
    try:
        # Convert PDF page to base64 image
        base64_image = pdf_page_to_base64_image(pdf_content, current_page, dpi=300)
        
        if not base64_image:
            print(f"DEBUG: Failed to convert page {current_page + 1} to image")
            # Move to next page
            return {
                **state,
                "current_page": current_page + 1,
                "processing_stage": "processing"
            }
        
        # Also extract text for context (backup)
        pdf_stream = io.BytesIO(pdf_content)
        pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
        page = pdf_document[current_page]
        page_text = page.get_text()
        pdf_document.close()
        
        # Create system message for vision-based table extraction
        system_content = f"""You are an Expert PDF Table Extraction Agent with advanced vision capabilities.

Your task is to analyze the provided page image and extract ALL tables present, converting them to clean, well-formatted Markdown tables.

You are also an expert in Financial data analysis and identifying metric names and numeric values from tables.

DOCUMENT CONTEXT:
- Company: {company_name}
- Document: {document_name}  
- Page: {current_page + 1} of {total_pages}

VISION ANALYSIS INSTRUCTIONS:
1. Carefully examine the entire page image for any tabular data
2. Look for visual patterns that indicate tables:
   - Grid lines, borders, or cell separators
   - Aligned columns and rows
   - Headers and data cells
   - Repeated structure patterns
3. Extract ALL tables found on this page
4. Pay special attention to financial data, metrics, and numerical values
5. Maintain the original structure and alignment

TABLE EXTRACTION REQUIREMENTS:
- Focus on extracting financial metrics with quarterly/yearly comparisons
- Look for patterns like: Q1 2025, Q1 2024, metric names, percentage changes
- Convert each identified table to proper Markdown format
- Include all headers (column and row headers)
- Preserve numerical data exactly as shown
- Maintain proper alignment and spacing

SPECIFIC DATA TO EXTRACT:
Focus on extracting tables with this structure:
- Metric Name | Q1 2025 | Q1 2024 | % Change (or similar)
- Revenue data, earnings data, financial performance metrics
- Any comparative quarterly or yearly data

OUTPUT FORMAT:
- If tables are found, provide them in clean Markdown format
- Separate multiple tables with descriptive headers
- If no tables are detected, respond with empty string ""


!! Important Note:
I need only Metric Name , Q1 2025 and Q1 2024


EXAMPLE OUTPUT FORMAT:
```markdown
## Financial Performance

| Metric Name | Q1 2025 | Q1 2024 |
|-------------|---------|---------|
| Revenue     | 5,577   | 7,734   |
| Net Income  | 1,234   | 1,567   |
```

Please analyze the page image and extract all tables in the specified format."""

        # Use vision model to extract tables
        system_message = SystemMessage(content=system_content)
        
        # Initialize vision-capable model (GPT-4 Vision)
        model = init_chat_model("openai:gpt-4o", temperature=0.1)
        # model = init_chat_model("groq:llama3-8b-8192", temperature=0.1)
        
        # Create message with image
        user_message = HumanMessage(content=[
            {
                "type": "text", 
                "text": f"Analyze this page image (page {current_page + 1}) and extract all tables. Convert them to Markdown format focusing on financial metrics and quarterly comparisons."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"  # Use high detail for better table recognition
                }
            }
        ])
        
        # Try vision model first, fallback to text if needed
        try:
            response = model.invoke([system_message, user_message])
            extracted_markdown = response.content
            
            # Clean up the response
            if extracted_markdown and extracted_markdown.strip():
                # Remove any code block markers if present
                if extracted_markdown.startswith("```markdown"):
                    extracted_markdown = extracted_markdown.replace("```markdown", "").replace("```", "")
                elif extracted_markdown.startswith("```"):
                    extracted_markdown = extracted_markdown.replace("```", "")
                
                extracted_markdown = extracted_markdown.strip()
            
        except Exception as vision_error:
            print(f"Vision model failed, falling back to text analysis: {vision_error}")
            # Fallback to text-based extraction with simpler prompt
            fallback_system = SystemMessage(content=f"""Extract any tables from this text and convert to markdown format. Focus on financial metrics and quarterly data.

Text from page {current_page + 1}:
{page_text}

Output format:
| Metric Name | Q1 2025 | Q1 2024 |
|-------------|---------|---------|
| Value1      | Data1   | Data2   |
""")
            user_message_text = HumanMessage(content="Extract tables from the provided text content.")
            response = model.invoke([fallback_system, user_message_text])
            extracted_markdown = response.content
        
        print(f"DEBUG: Extracted {len(extracted_markdown)} characters of table data from page {current_page + 1}")
        
        # Store page table data
        page_table_data = {
            "page_number": current_page + 1,
            "extracted_content": extracted_markdown,
            "has_image": bool(base64_image),
            "original_text_length": len(page_text) if page_text else 0
        }
        
        # Update state
        updated_page_tables = state.get("page_tables", []) + [page_table_data]
        
        return {
            **state,
            "current_page": current_page + 1,
            "page_tables": updated_page_tables,
            "processing_stage": "processing"
        }
        
    except Exception as e:
        error_message = f"Error extracting tables from page {current_page + 1}: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "extraction_error",
            "error_message": error_message
        }

def should_continue_extraction(state):
    """Determine if we should continue processing more pages"""
    current_page = state.get("current_page", 0)
    total_pages = state.get("total_pages", 0)
    processing_stage = state.get("processing_stage", "")
    
    if processing_stage in ["extraction_error", "load_error"]:
        return "finalize"
    elif current_page < total_pages:
        return "extract_page"
    else:
        return "accumulate"

def accumulate_markdown_tables(state):
    """Accumulate all extracted tables into a single markdown document"""
    page_tables = state.get("page_tables", [])
    company_name = state.get("company_name", "")
    document_name = state.get("document_name", "")
    year = state.get("year", "")
    quarter = state.get("quarter", "")
    
    print(f"DEBUG: accumulate_markdown_tables - Processing {len(page_tables)} pages")
    
    try:        # Create markdown document header
        markdown_content = f"""# Table Extraction Report (Vision-Enhanced)

**Company:** {company_name}  
**Document:** {document_name}  
**Period:** {quarter} {year}  
**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Pages Processed:** {len(page_tables)}  
**Extraction Method:** Vision Model + Text Analysis

---

"""
        
        # Process each page's tables
        tables_found = 0
        vision_processed = 0
        
        for page_data in page_tables:
            page_num = page_data["page_number"]
            extracted_content = page_data["extracted_content"]
            has_image = page_data.get("has_image", False)
            
            if has_image:
                vision_processed += 1
                
            markdown_content += f"\n## Page {page_num} {'📷 (Vision Analysis)' if has_image else '📝 (Text Analysis)'}\n\n"
            
            # Check if tables were found on this page
            if ("no tables found" in extracted_content.lower() or 
                "no table" in extracted_content.lower() or
                extracted_content.strip() == ""):
                markdown_content += "*No tables found on this page.*\n\n"
            else:
                markdown_content += extracted_content + "\n\n"
                tables_found += 1
        
        # Add summary
        markdown_content += f"\n---\n\n**Extraction Summary:**\n"
        markdown_content += f"- Total pages processed: {len(page_tables)}\n"
        markdown_content += f"- Pages with vision analysis: {vision_processed}\n"
        markdown_content += f"- Pages with tables detected: {tables_found}\n"
        markdown_content += f"- Pages without tables: {len(page_tables) - tables_found}\n"
        markdown_content += f"- Success rate: {(tables_found/len(page_tables)*100):.1f}%\n"
        
        print(f"DEBUG: Generated markdown document with {len(markdown_content)} characters")
        
        return {
            **state,
            "accumulated_markdown": markdown_content,
            "processing_stage": "accumulated"
        }
        
    except Exception as e:
        error_message = f"Error accumulating markdown tables: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "accumulation_error",
            "error_message": error_message
        }

def save_markdown_output(state):
    """Save the accumulated markdown to a file"""
    accumulated_markdown = state.get("accumulated_markdown", "")
    company_name = state.get("company_name", "")
    document_name = state.get("document_name", "")
    year = state.get("year", "")
    quarter = state.get("quarter", "")
    
    print(f"DEBUG: save_markdown_output - Saving extracted tables")
    
    try:
        # Create output directory structure
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        output_base = os.path.join(parent_dir, "extracted_tables")
        output_dir = os.path.join(output_base, year, quarter, company_name.upper())
        
        os.makedirs(output_dir, exist_ok=True)
          # Generate output filename
        base_name = os.path.splitext(document_name)[0]
        output_filename = f"{base_name}_tables_vision_extracted.md"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the markdown content
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(accumulated_markdown)
        
        print(f"DEBUG: Successfully saved markdown to {output_path}")
        
        return {
            **state,
            "output_path": output_path,
            "processing_stage": "completed"
        }
        
    except Exception as e:
        error_message = f"Error saving markdown output: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "save_error",
            "error_message": error_message
        }

def finalize_table_extraction(state):
    """Finalize the table extraction process and return results"""
    processing_stage = state.get("processing_stage", "")
    error_message = state.get("error_message", "")
    output_path = state.get("output_path", "")
    company_name = state.get("company_name", "")
    document_name = state.get("document_name", "")
    page_tables = state.get("page_tables", [])
    print(f"DEBUG: finalize_table_extraction - Stage: {processing_stage}")
    
    if processing_stage == "completed" and output_path:
        tables_count = sum(1 for page in page_tables 
                          if not ("no tables found" in page.get("extracted_content", "").lower()))
        vision_count = sum(1 for page in page_tables 
                          if page.get("has_image", False))
        
        final_message = f"""✅ **PDF Table Extraction Completed (Vision-Enhanced)**

**Document:** {document_name}  
**Company:** {company_name}  
**Pages Processed:** {len(page_tables)}  
**Vision Analysis:** {vision_count}/{len(page_tables)} pages  
**Tables Found:** {tables_count}  
**Output Saved:** {os.path.relpath(output_path, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))}

The extracted tables have been saved in Markdown format using advanced vision analysis for improved accuracy.
"""
    
    elif error_message:
        final_message = f"""❌ **Error in PDF Table Extraction**

**Document:** {document_name}  
**Company:** {company_name}  
**Error:** {error_message}

Please check the document path and try again.
"""
    
    else:
        final_message = f"""⚠️ **PDF Table Extraction Incomplete**

**Document:** {document_name}  
**Company:** {company_name}  
**Stage:** {processing_stage}

The extraction process did not complete successfully.
"""
    
    return {
        "messages": [AIMessage(content=final_message)]
    }

def create_pdf_table_extraction_graph():
    """Create and return the PDF table extraction processing graph."""
    
    # Create the state graph
    workflow = StateGraph(PDFTableExtractionState)
    
    # Add nodes for the workflow
    workflow.add_node("initialize", initialize_table_extraction)
    workflow.add_node("load_pdf", load_pdf_document)
    workflow.add_node("extract_page", extract_page_tables)
    workflow.add_node("accumulate", accumulate_markdown_tables)
    workflow.add_node("save_output", save_markdown_output)
    workflow.add_node("finalize", finalize_table_extraction)
    
    # Define the workflow edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "load_pdf")
    
    # After loading PDF, start extracting from first page
    workflow.add_edge("load_pdf", "extract_page")
    
    # Conditional routing after page extraction
    workflow.add_conditional_edges(
        "extract_page",
        should_continue_extraction,
        {
            "extract_page": "extract_page",  # Continue to next page
            "accumulate": "accumulate",      # All pages done, accumulate results
            "finalize": "finalize"           # Error occurred, finalize
        }
    )
    
    # After accumulation, save output
    workflow.add_edge("accumulate", "save_output")
    workflow.add_edge("save_output", "finalize")
    workflow.add_edge("finalize", END)
    
    # Add SQLite-based memory persistence
    checkpoint_dir = os.path.join(os.path.dirname(__file__), '..', 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # SQLite database path for checkpoints
    db_path = os.path.join(checkpoint_dir, 'table_extraction_checkpoints.db')
    
    # Create SQLite connection and memory saver
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app

# Convenience function for easy usage
def extract_pdf_tables_with_vision(year: str, quarter: str, company_name: str, document_name: str, document_type: str = "General"):
    """
    Convenience function to extract tables from a PDF document using vision models.
    
    Args:
        year (str): Year (e.g., "2025")
        quarter (str): Quarter (e.g., "Q1")
        company_name (str): Company name (e.g., "SHELL")
        document_name (str): Document filename (e.g., "financial_report.pdf")
        document_type (str): Document type (e.g., "QRAReport", "FirstCutModel", "BalanceSheet")
    
    Returns:
        dict: Result of the table extraction process
    """
    graph = create_pdf_table_extraction_graph()
    
    initial_state = {
        "messages": [],
        "year": year,
        "quarter": quarter,
        "company_name": company_name,
        "document_name": document_name,
        "document_type": document_type
    }
    
    config = {"configurable": {"thread_id": f"vision_table_extract_{company_name}_{document_type}_{quarter}_{year}_{document_name}"}}
    
    # Run the graph
    result = graph.invoke(initial_state, config)
    
    return result

# Keep original function name for compatibility
def extract_pdf_tables(year: str, quarter: str, company_name: str, document_name: str, document_type: str = "General"):
    """Legacy function name - now uses vision-enhanced extraction"""
    return extract_pdf_tables_with_vision(year, quarter, company_name, document_name, document_type)

if __name__ == "__main__":
    # Example usage
    print("PDF Table Extraction Graph created successfully!")
    
    # Test with example parameters
    # result = extract_pdf_tables("2025", "Q1", "ACME_CORP", "sample_report.pdf")
    # print(f"Extraction result: {result}")
