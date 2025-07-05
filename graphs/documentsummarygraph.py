from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated, Optional
import fitz  # PyMuPDF for PDF parsing
import docx  # python-docx for Word documents
import io
import os
import sqlite3

# State for the document summary workflow
class DocumentSummaryState(TypedDict):
    messages: Annotated[list, "The conversation messages"]
    file_content: bytes
    file_name: str
    file_type: str
    parsed_text: str
    summary: str
    processing_stage: str
    error_message: str

def initialize_document_processing(state):
    """Initialize the document processing workflow"""
    messages = state["messages"]
    file_content = state.get("file_content", b"")
    file_name = state.get("file_name", "")
    file_type = state.get("file_type", "")
    
    print(f"DEBUG: initialize_document_processing - File: {file_name}, Type: {file_type}")
    
    return {
        "messages": messages,
        "file_content": file_content,
        "file_name": file_name,
        "file_type": file_type,
        "parsed_text": "",
        "summary": "",
        "processing_stage": "initialized",
        "error_message": ""
    }

def document_parser_agent(state):
    """Agent that parses uploaded documents and extracts text content"""
    file_content = state.get("file_content", b"")
    file_name = state.get("file_name", "")
    file_type = state.get("file_type", "")
    
    print(f"DEBUG: Document Parser Agent - Processing {file_name} ({file_type})")
    
    parsed_text = ""
    error_message = ""
    
    try:
        if file_type.lower() == "pdf":
            # Parse PDF using PyMuPDF
            pdf_stream = io.BytesIO(file_content)
            pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
            
            text_chunks = []
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text_chunks.append(page.get_text())
            
            parsed_text = "\n".join(text_chunks)
            pdf_document.close()
            
        elif file_type.lower() in ["docx", "doc"]:
            # Parse Word document using python-docx
            doc_stream = io.BytesIO(file_content)
            doc = docx.Document(doc_stream)
            
            text_chunks = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_chunks.append(paragraph.text)
            
            parsed_text = "\n".join(text_chunks)
            
        elif file_type.lower() == "txt":
            # Parse plain text file
            parsed_text = file_content.decode('utf-8', errors='ignore')
            
        else:
            error_message = f"Unsupported file type: {file_type}"
            
        if parsed_text:
            print(f"DEBUG: Successfully parsed {len(parsed_text)} characters from {file_name}")
        else:
            error_message = "No text content found in the document"
            
    except Exception as e:
        error_message = f"Error parsing document: {str(e)}"
        print(f"DEBUG: Parsing error: {error_message}")
    
    return {
        "messages": state["messages"],
        "file_content": file_content,
        "file_name": file_name,
        "file_type": file_type,
        "parsed_text": parsed_text,
        "summary": "",
        "processing_stage": "parsed" if parsed_text else "parse_error",
        "error_message": error_message
    }

def document_summarizer_agent(state):
    """Agent that creates intelligent summaries of parsed document content"""
    parsed_text = state.get("parsed_text", "")
    file_name = state.get("file_name", "")
    messages = state["messages"]
    
    print(f"DEBUG: Document Summarizer Agent - Summarizing {len(parsed_text)} characters")
    
    if not parsed_text:
        return {
            **state,
            "processing_stage": "summary_error",
            "error_message": "No parsed text available for summarization"
        }
    
    # Extract user preferences from messages if any
    user_request = ""
    if messages and len(messages) > 0:
        if isinstance(messages[0], tuple):
            user_request = messages[0][1]  # For ("user", content) format
        else:
            user_request = messages[0].content if hasattr(messages[0], 'content') else ""
    
    system_content = f"""You are an Expert Document Summarizer Agent. Your task is to create a comprehensive, intelligent summary of the provided document content.

DOCUMENT: {file_name}
USER REQUEST: {user_request if user_request else "Create a comprehensive summary"}

DOCUMENT CONTENT:
=== DOCUMENT TEXT ===
{parsed_text}
=== END DOCUMENT ===

SUMMARIZATION GUIDELINES:
1. Create a well-structured summary with clear sections
2. Identify and highlight key themes, main points, and important details
3. Extract actionable insights and recommendations if present
4. Maintain logical flow and coherence
5. Use bullet points and subheadings for better readability
6. Include quantitative data, dates, and specific metrics when mentioned
7. Identify any conclusions, decisions, or next steps mentioned in the document

SUMMARY STRUCTURE:
1. **Executive Summary** - Brief overview of the document
2. **Key Points** - Main themes and important information
3. **Details & Data** - Specific metrics, dates, figures mentioned
4. **Insights & Recommendations** - Analysis and actionable items
5. **Conclusion** - Final thoughts and next steps

Please provide a professional, comprehensive summary that captures the essence and important details of the document.
"""
    
    try:
        system_message = SystemMessage(content=system_content)
        model = init_chat_model("groq:llama3-8b-8192", temperature=0.3)
        
        # Create proper message for the model
        user_message = HumanMessage(content=f"Please summarize the document: {file_name}")
        response = model.invoke([system_message, user_message])
        summary_content = response.content
        
        print(f"DEBUG: Generated summary of {len(summary_content)} characters")
        
        return {
            "messages": state["messages"],
            "file_content": state["file_content"],
            "file_name": file_name,
            "file_type": state["file_type"],
            "parsed_text": parsed_text,
            "summary": summary_content,
            "processing_stage": "completed",
            "error_message": ""
        }
        
    except Exception as e:
        error_message = f"Error generating summary: {str(e)}"
        print(f"DEBUG: Summarization error: {error_message}")
        
        return {
            **state,
            "processing_stage": "summary_error",
            "error_message": error_message
        }

def should_continue_to_summarizer(state):
    """Determine if we should proceed to summarization"""
    processing_stage = state.get("processing_stage", "")
    return "summarizer" if processing_stage == "parsed" else "finalize"

def finalize_document_processing(state):
    """Finalize the document processing and return results"""
    summary = state.get("summary", "")
    processing_stage = state.get("processing_stage", "")
    error_message = state.get("error_message", "")
    file_name = state.get("file_name", "")
    
    print(f"DEBUG: Finalizing document processing - Stage: {processing_stage}")
    
    if processing_stage == "completed" and summary:
        final_message = f"✅ **Document Summary for: {file_name}**\n\n{summary}"
    elif error_message:
        final_message = f"❌ **Error processing {file_name}**\n\n{error_message}"
    else:
        final_message = f"⚠️ **Processing incomplete for {file_name}**\n\nNo summary available."
    
    return {
        "messages": [AIMessage(content=final_message)]
    }

def create_document_summary_graph():
    """Create and return the document summary processing graph."""
    
    # Create the state graph with custom DocumentSummaryState
    workflow = StateGraph(DocumentSummaryState)
    
    # Add nodes for the workflow
    workflow.add_node("initialize", initialize_document_processing)
    workflow.add_node("parser", document_parser_agent)
    workflow.add_node("summarizer", document_summarizer_agent)
    workflow.add_node("finalize", finalize_document_processing)
    
    # Define the workflow edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "parser")
      # Conditional routing after parser
    workflow.add_conditional_edges(
        "parser",
        should_continue_to_summarizer,
        {
            "summarizer": "summarizer",
            "finalize": "finalize"
        }
    )
    
    # After summarizer, go to finalization
    workflow.add_edge("summarizer", "finalize")
    workflow.add_edge("finalize", END)
    
    # Add SQLite-based memory persistence
    # Create checkpoints directory if it doesn't exist
    checkpoint_dir = os.path.join(os.path.dirname(__file__), '..', 'checkpoints')
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # SQLite database path for checkpoints
    db_path = os.path.join(checkpoint_dir, 'document_summary_checkpoints.db')
    
    # Create SQLite connection and memory saver
    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)
    
    # Compile the graph
    app = workflow.compile(checkpointer=memory)
    
    return app
