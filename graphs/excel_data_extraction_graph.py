from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, Optional, List, Dict
import pandas as pd
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
import os
import sqlite3
import base64
import io
from datetime import datetime
from pathlib import Path
import tempfile
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# State for the Excel data extraction workflow
class ExcelDataExtractionState(TypedDict):
    messages: Annotated[list, "The conversation messages"]
    excel_file_path: str
    sheet_names: Annotated[List[str], "List of sheet names in the Excel file"]
    current_sheet_index: int
    current_sheet_name: str
    sheet_images: Annotated[Dict, "Base64 images of each sheet"]
    extracted_tables: Annotated[List[Dict], "Tables extracted from all sheets"]
    analysis_result: str
    processing_stage: str
    error_message: str
    output_path: str
    total_sheets: int
    processed_sheets: int

def initialize_excel_extraction(state):
    """Initialize the Excel data extraction workflow"""
    excel_file_path = state.get("excel_file_path", "")
    
    print(f"DEBUG: initialize_excel_extraction - Processing {excel_file_path}")
    
    if not excel_file_path or not os.path.exists(excel_file_path):
        return {
            **state,
            "processing_stage": "initialization_error",
            "error_message": f"Excel file not found: {excel_file_path}"
        }
    
    return {
        "messages": state.get("messages", []),
        "excel_file_path": excel_file_path,
        "sheet_names": [],
        "current_sheet_index": 0,
        "current_sheet_name": "",
        "sheet_images": {},
        "extracted_tables": [],
        "analysis_result": "",
        "processing_stage": "initialized",
        "error_message": "",
        "output_path": "",
        "total_sheets": 0,
        "processed_sheets": 0
    }

def load_excel_sheets(state):
    """Load Excel file and get sheet information"""
    excel_file_path = state.get("excel_file_path", "")
    
    print(f"DEBUG: load_excel_sheets - Loading {excel_file_path}")
    
    try:
        # Load workbook to get sheet names
        workbook = openpyxl.load_workbook(excel_file_path, data_only=True)
        sheet_names = workbook.sheetnames
        workbook.close()
        
        print(f"DEBUG: Found {len(sheet_names)} sheets: {sheet_names}")
        
        return {
            **state,
            "sheet_names": sheet_names,
            "total_sheets": len(sheet_names),
            "current_sheet_index": 0,
            "processed_sheets": 0,
            "processing_stage": "loaded"
        }
        
    except Exception as e:
        error_message = f"Error loading Excel file: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "load_error",
            "error_message": error_message
        }

def excel_sheet_to_image(excel_file_path: str, sheet_name: str, output_path: str = None) -> str:
    """Convert an Excel sheet to an image and return base64 encoded string"""
    try:
        # Read the Excel sheet using pandas
        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        
        if df.empty:
            print(f"DEBUG: Sheet '{sheet_name}' is empty")
            return ""
        
        # Create a figure with matplotlib
        fig, ax = plt.subplots(figsize=(16, 12))  # Large figure for better readability
        ax.axis('tight')
        ax.axis('off')
        
        # Create table from dataframe
        # Replace NaN values with empty strings for better visualization
        df_clean = df.fillna('')
        
        # Create the table
        table = ax.table(
            cellText=df_clean.values,
            colLabels=df_clean.columns,
            cellLoc='center',
            loc='center'
        )
        
        # Style the table for better visibility
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 2)
        
        # Style header row
        for i in range(len(df_clean.columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Style data rows with alternating colors
        for i in range(1, len(df_clean) + 1):
            for j in range(len(df_clean.columns)):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F2F2F2')
                else:
                    table[(i, j)].set_facecolor('white')
        
        # Add title
        plt.title(f'Sheet: {sheet_name}', fontsize=14, fontweight='bold', pad=20)
        
        # Save to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buf.seek(0)
        
        # Convert to base64
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)
        
        # Optionally save to file for debugging
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(image_base64))
            print(f"DEBUG: Sheet image saved to {output_path}")
        
        return image_base64
        
    except Exception as e:
        print(f"DEBUG: Error converting sheet '{sheet_name}' to image: {str(e)}")
        return ""

def convert_current_sheet_to_image(state):
    """Convert the current sheet to an image for vision model analysis"""
    excel_file_path = state.get("excel_file_path", "")
    sheet_names = state.get("sheet_names", [])
    current_sheet_index = state.get("current_sheet_index", 0)
    
    if current_sheet_index >= len(sheet_names):
        # All sheets processed, move to analysis
        return {
            **state,
            "processing_stage": "all_sheets_converted"
        }
    
    current_sheet_name = sheet_names[current_sheet_index]
    print(f"DEBUG: convert_current_sheet_to_image - Processing sheet {current_sheet_index + 1}/{len(sheet_names)}: {current_sheet_name}")
    
    try:
        # Create output path for debugging
        debug_image_path = os.path.join("extracted_images", f"sheet_{current_sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        # Convert sheet to base64 image
        base64_image = excel_sheet_to_image(excel_file_path, current_sheet_name, debug_image_path)
        
        if not base64_image:
            print(f"DEBUG: Failed to convert sheet '{current_sheet_name}' to image")
            # Move to next sheet
            return {
                **state,
                "current_sheet_index": current_sheet_index + 1,
                "processing_stage": "converting_sheets"
            }
        
        # Update sheet images
        updated_sheet_images = state.get("sheet_images", {})
        updated_sheet_images[current_sheet_name] = base64_image
        
        return {
            **state,
            "current_sheet_name": current_sheet_name,
            "sheet_images": updated_sheet_images,
            "current_sheet_index": current_sheet_index + 1,
            "processing_stage": "converting_sheets"
        }
        
    except Exception as e:
        error_message = f"Error converting sheet '{current_sheet_name}' to image: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "conversion_error",
            "error_message": error_message
        }

def extract_tables_from_current_sheet(state):
    """Extract tables from the current sheet using vision model"""
    sheet_images = state.get("sheet_images", {})
    sheet_names = state.get("sheet_names", [])
    processed_sheets = state.get("processed_sheets", 0)
    
    if processed_sheets >= len(sheet_names):
        return {
            **state,
            "processing_stage": "extraction_completed"
        }
    
    current_sheet_name = sheet_names[processed_sheets]
    base64_image = sheet_images.get(current_sheet_name, "")
    
    if not base64_image:
        # No image for this sheet, skip to next
        return {
            **state,
            "processed_sheets": processed_sheets + 1,
            "processing_stage": "extracting_tables"
        }
    
    print(f"DEBUG: extract_tables_from_current_sheet - Analyzing sheet: {current_sheet_name}")
    
    try:
        # Initialize vision-capable model (GPT-4 Vision)
        model = init_chat_model("openai:gpt-4o", temperature=0.1)
        
        # Create system message for table extraction
        system_content = f"""You are an Expert Excel Table Extraction Agent with advanced vision capabilities.

Your task is to analyze the provided Excel sheet image and extract ALL tables present, converting them to clean, well-formatted Markdown tables.

EXCEL SHEET CONTEXT:
- Sheet Name: {current_sheet_name}
- Source: Excel file upload for data analysis

VISION ANALYSIS INSTRUCTIONS:
1. Carefully examine the entire sheet image for any tabular data
2. Look for visual patterns that indicate tables:
   - Column headers and row labels
   - Grid lines or cell borders
   - Aligned data in rows and columns
   - Repeated data patterns
3. Extract ALL tables found on this sheet
4. Pay special attention to:
   - Financial data and metrics
   - Numerical values with proper formatting
   - Date columns and time series data
   - Percentage values and calculations

TABLE EXTRACTION REQUIREMENTS:
- Convert each identified table to proper Markdown format
- Include all headers (both column and row headers if present)
- Preserve numerical data exactly as shown
- Maintain proper alignment and spacing
- Handle merged cells appropriately
- If data spans multiple sections, create separate tables

SPECIFIC FOCUS AREAS:
- Financial metrics (Revenue, Profit, etc.)
- Quarterly/yearly data comparisons
- Key performance indicators
- Any calculated fields or totals

OUTPUT FORMAT:
- If tables are found, provide them in clean Markdown format
- Separate multiple tables with descriptive headers
- If no clear tables are detected, respond with: "No clear tabular data detected in this sheet"

EXAMPLE OUTPUT FORMAT:
```markdown
## Table 1: Financial Performance

| Metric | Q1 2025 | Q1 2024 | Change |
|--------|---------|---------|--------|
| Revenue | $1,234M | $1,100M | +12.2% |
| Net Income | $234M | $200M | +17% |

## Table 2: Regional Breakdown

| Region | Sales | Percentage |
|--------|-------|------------|
| North America | $500M | 40% |
| Europe | $375M | 30% |
```

Please analyze the sheet image and extract all tables in the specified format."""

        # Create message with image
        user_message = HumanMessage(content=[
            {
                "type": "text", 
                "text": f"Analyze this Excel sheet image (Sheet: {current_sheet_name}) and extract all tables. Convert them to Markdown format focusing on preserving all data structure and relationships."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"  # Use high detail for better table recognition
                }
            }
        ])
        
        # Get LLM response
        system_message = SystemMessage(content=system_content)
        response = model.invoke([system_message, user_message])
        extracted_markdown = response.content
        
        # Clean up the response
        if extracted_markdown and extracted_markdown.strip():
            # Remove any code block markers if present
            if "```markdown" in extracted_markdown:
                extracted_markdown = extracted_markdown.replace("```markdown", "").replace("```", "")
            
            print(f"DEBUG: Successfully extracted {len(extracted_markdown)} characters of table data from sheet '{current_sheet_name}'")
        else:
            extracted_markdown = f"No tables detected in sheet: {current_sheet_name}"
            print(f"DEBUG: No tables detected in sheet '{current_sheet_name}'")
        
        # Store extracted table data
        table_data = {
            "sheet_name": current_sheet_name,
            "extracted_content": extracted_markdown.strip(),
            "has_image": True,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        # Update extracted tables list
        updated_extracted_tables = state.get("extracted_tables", []) + [table_data]
        
        return {
            **state,
            "extracted_tables": updated_extracted_tables,
            "processed_sheets": processed_sheets + 1,
            "processing_stage": "extracting_tables"
        }
        
    except Exception as e:
        error_message = f"Error extracting tables from sheet '{current_sheet_name}': {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "extraction_error",
            "error_message": error_message
        }

def analyze_extracted_data_with_llm(state):
    """Analyze all extracted tables with LLM for comprehensive insights"""
    extracted_tables = state.get("extracted_tables", [])
    messages = state.get("messages", [])
    
    print(f"DEBUG: analyze_extracted_data_with_llm - Analyzing {len(extracted_tables)} sheets")
    
    if not extracted_tables:
        return {
            **state,
            "processing_stage": "analysis_error",
            "error_message": "No extracted tables to analyze"
        }
    
    try:
        # Initialize the chat model
        llm = init_chat_model("openai:gpt-4o", temperature=0)
        
        # Combine all extracted content
        all_tables_content = []
        for table_data in extracted_tables:
            sheet_name = table_data.get("sheet_name", "Unknown")
            content = table_data.get("extracted_content", "")
            if content and "No tables detected" not in content:
                all_tables_content.append(f"# Sheet: {sheet_name}\n\n{content}")
        
        if not all_tables_content:
            combined_content = "No tables were successfully extracted from any sheets."
        else:
            combined_content = "\n\n---\n\n".join(all_tables_content)
        
        # Create comprehensive analysis prompt
        system_message = SystemMessage(content="""You are an expert Excel data analyst specializing in comprehensive data analysis and business insights.

Your task is to analyze the provided Excel table data that was extracted using vision AI and provide comprehensive insights.

Please analyze the data and provide:
1. **Data Overview**: Summary of what data is contained in each sheet and table
2. **Key Findings**: Important patterns, trends, or notable data points across all sheets
3. **Financial Analysis** (if applicable): Revenue trends, profitability, key performance metrics
4. **Data Quality Assessment**: Any issues with data completeness, consistency, or format
5. **Business Insights**: Strategic insights and recommendations based on the data patterns
6. **Summary**: High-level summary of the most important findings

Focus on:
- Quantitative analysis of numerical data
- Trend identification across time periods
- Comparative analysis between different categories/periods
- Actionable business recommendations
- Data reliability and completeness assessment

Be thorough but concise. Prioritize actionable insights over descriptive summaries.""")
        
        human_message = HumanMessage(content=f"""Please analyze this Excel data that was extracted from multiple sheets:

**Extracted Excel Data:**
{combined_content}

Please provide a comprehensive analysis following the requested structure. Focus on delivering actionable insights and identifying key business patterns in the data.""")
        
        # Get LLM analysis
        response = llm.invoke([system_message, human_message])
        analysis_result = response.content
        
        # Update messages
        updated_messages = messages + [system_message, human_message, AIMessage(content=analysis_result)]
        
        print("DEBUG: LLM analysis completed successfully")
        
        return {
            **state,
            "messages": updated_messages,
            "analysis_result": analysis_result,
            "processing_stage": "analyzed"
        }
        
    except Exception as e:
        error_message = f"Error in LLM analysis: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "analysis_error",
            "error_message": error_message
        }

def save_extraction_results(state):
    """Save the extraction results and analysis"""
    excel_file_path = state.get("excel_file_path", "")
    analysis_result = state.get("analysis_result", "")
    extracted_tables = state.get("extracted_tables", [])
    
    print("DEBUG: save_extraction_results - Saving analysis and extracted data")
    
    try:
        # Create output directory
        base_name = os.path.splitext(os.path.basename(excel_file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("extracted_tables", f"{base_name}_excel_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save analysis result
        analysis_path = os.path.join(output_dir, "excel_analysis_result.md")
        with open(analysis_path, "w", encoding="utf-8") as f:
            f.write(f"# Excel Data Analysis Results\n\n")
            f.write(f"**Source File:** {excel_file_path}\n")
            f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Sheets Processed:** {len(extracted_tables)}\n\n")
            f.write("## Comprehensive Analysis\n\n")
            f.write(analysis_result)
        
        # Save extracted tables by sheet
        all_tables_path = os.path.join(output_dir, "extracted_tables_all_sheets.md")
        with open(all_tables_path, "w", encoding="utf-8") as f:
            f.write(f"# Extracted Excel Tables\n\n")
            f.write(f"**Source File:** {excel_file_path}\n")
            f.write(f"**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Processing Method:** OpenAI GPT-4 Vision\n\n")
            
            for table_data in extracted_tables:
                sheet_name = table_data.get("sheet_name", "Unknown")
                content = table_data.get("extracted_content", "")
                f.write(f"# Sheet: {sheet_name}\n\n")
                f.write(content)
                f.write("\n\n---\n\n")
        
        # Save individual sheet files
        for table_data in extracted_tables:
            sheet_name = table_data.get("sheet_name", "Unknown")
            content = table_data.get("extracted_content", "")
            
            # Clean sheet name for filename
            safe_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            sheet_path = os.path.join(output_dir, f"sheet_{safe_sheet_name}.md")
            
            with open(sheet_path, "w", encoding="utf-8") as f:
                f.write(f"# Sheet: {sheet_name}\n\n")
                f.write(f"**Extraction Method:** OpenAI GPT-4 Vision\n")
                f.write(f"**Extraction Date:** {table_data.get('extraction_timestamp', 'Unknown')}\n\n")
                f.write(content)
        
        print(f"DEBUG: Results saved to {output_dir}")
        
        return {
            **state,
            "output_path": output_dir,
            "processing_stage": "completed"
        }
        
    except Exception as e:
        error_message = f"Error saving results: {str(e)}"
        print(f"DEBUG: {error_message}")
        return {
            **state,
            "processing_stage": "save_error",
            "error_message": error_message
        }

def should_continue_processing(state):
    """Determine the next step in processing"""
    processing_stage = state.get("processing_stage", "")
    current_sheet_index = state.get("current_sheet_index", 0)
    total_sheets = state.get("total_sheets", 0)
    processed_sheets = state.get("processed_sheets", 0)
    
    if processing_stage in ["initialization_error", "load_error", "conversion_error", "extraction_error", "analysis_error", "save_error"]:
        return "error"
    elif processing_stage == "completed":
        return "end"
    elif processing_stage == "converting_sheets":
        if current_sheet_index < total_sheets:
            return "convert_sheet"
        else:
            return "extract_tables"
    elif processing_stage == "extracting_tables":
        if processed_sheets < total_sheets:
            return "extract_tables"
        else:
            return "analyze"
    else:
        return "continue"

def create_excel_data_extraction_graph():
    """Create and return the Excel data extraction graph"""
    print("Creating Excel Data Extraction Graph with Vision AI...")
    
    # Create the workflow
    workflow = StateGraph(ExcelDataExtractionState)
    
    # Add nodes
    workflow.add_node("initialize", initialize_excel_extraction)
    workflow.add_node("load_sheets", load_excel_sheets)
    workflow.add_node("convert_sheet", convert_current_sheet_to_image)
    workflow.add_node("extract_tables", extract_tables_from_current_sheet)
    workflow.add_node("analyze_data", analyze_extracted_data_with_llm)
    workflow.add_node("save_results", save_extraction_results)
    workflow.add_node("handle_error", lambda state: {
        **state, 
        "processing_stage": "error_handled",
        "messages": state.get("messages", []) + [
            AIMessage(content=f"An error occurred during processing: {state.get('error_message', 'Unknown error')}")
        ]
    })
    
    # Set entry point
    workflow.set_entry_point("initialize")
    
    # Add basic flow edges
    workflow.add_edge("initialize", "load_sheets")
    workflow.add_edge("load_sheets", "convert_sheet")
    
    # Add conditional edges for processing flow
    workflow.add_conditional_edges(
        "convert_sheet",
        should_continue_processing,
        {
            "convert_sheet": "convert_sheet",
            "extract_tables": "extract_tables",
            "error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "extract_tables",
        should_continue_processing,
        {
            "extract_tables": "extract_tables",
            "analyze": "analyze_data",
            "error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_edge("analyze_data", "save_results")
    workflow.add_edge("save_results", END)
    workflow.add_edge("handle_error", END)
    
    return workflow

def run_excel_extraction_workflow(excel_file_path: str, thread_id: str = "excel_extraction"):
    """
    Run the Excel data extraction workflow with vision AI
    
    Args:
        excel_file_path (str): Path to the Excel file to process
        thread_id (str): Thread ID for checkpointing
    """
    print(f"Starting Excel data extraction with Vision AI for: {excel_file_path}")
    
    # Create checkpoints directory
    checkpoints_dir = "checkpoints"
    os.makedirs(checkpoints_dir, exist_ok=True)
    
    # Initialize SQLite checkpointer with proper connection
    checkpointer_path = os.path.join(checkpoints_dir, "excel_vision_extraction_checkpoints.db")
    
    # Create SQLite connection
    conn = sqlite3.connect(checkpointer_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # Create and compile the graph
    graph = create_excel_data_extraction_graph()
    app = graph.compile(checkpointer=memory)
    
    # Initial state
    initial_state = {
        "excel_file_path": excel_file_path,
        "messages": [],
    }
      # Configuration for the run
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Run the workflow
        print(f"DEBUG: Starting workflow execution with thread_id: {thread_id}")
        result = app.invoke(initial_state, config)
        
        print(f"Excel extraction workflow completed!")
        print(f"Processing stage: {result.get('processing_stage', 'unknown')}")
        print(f"Sheets processed: {result.get('processed_sheets', 0)}/{result.get('total_sheets', 0)}")
        
        if result.get("error_message"):
            print(f"Error: {result.get('error_message')}")
        
        if result.get("output_path"):
            print(f"Results saved to: {result.get('output_path')}")
        
        # Ensure we return the analysis_result even if it's empty
        if not result.get("analysis_result"):
            print("DEBUG: No analysis_result found, checking extracted_tables...")
            if result.get("extracted_tables"):
                print(f"DEBUG: Found {len(result['extracted_tables'])} extracted tables")
                # Generate a basic analysis if the main analysis failed
                result["analysis_result"] = f"**Processing Summary:**\n\nSuccessfully processed {result.get('processed_sheets', 0)} out of {result.get('total_sheets', 0)} sheets.\n\nExtracted data from the following sheets:\n" + "\n".join([f"- {table.get('sheet_name', 'Unknown')}" for table in result.get("extracted_tables", [])])
            else:
                print("DEBUG: No extracted_tables found either")
        
        return result
        
    except Exception as e:
        print(f"Error running Excel extraction workflow: {e}")
        return {"error": str(e), "processing_stage": "workflow_error"}

if __name__ == "__main__":
    # Example usage
    excel_file = "sample_excel_data.xlsx"
    if os.path.exists(excel_file):
        result = run_excel_extraction_workflow(excel_file)
        print(f"Final result: {result}")
    else:
        print(f"Excel file not found: {excel_file}")
        print("Please provide a valid Excel file path.")