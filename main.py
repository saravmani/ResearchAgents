from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import uvicorn
import json
import os
import asyncio
from graphs.reportgraph import create_research_graph
from graphs.financedatagraph import create_finance_data_graph
from graphs.mapreduce_graph import create_transcript_mapreduce_graph, analyze_transcript
from utils.vector_store import initialize_vector_store
from utils.promptmanager import load_prompts_data, get_prompt_for_request
from models import ResearchRequest, ResearchResponse, FinanceDataRequest, FinanceDataResponse, TranscriptAnalysisRequest, TranscriptAnalysisResponse

app = FastAPI(title="Equity Research Agent API with ChromaDB", version="1.0.0")

# Initialize vector store on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the vector store when the API starts"""
    print("🚀 Initializing Equity Research API with ChromaDB...")
    try:
        # Initialize default vector store
        vectorstore = initialize_vector_store()
        stats = vectorstore.get_collection_stats()
        print(f"✅ Default vector store initialized: {stats}")
    except Exception as e:
        print(f"❌ Error initializing vector store: {e}")

# Load prompts data
PROMPTS_DATA = load_prompts_data()

# Initialize the graphs
research_graph = create_research_graph()
finance_data_graph = create_finance_data_graph()
# transcript_mapreduce_graph = create_transcript_mapreduce_graph()

async def stream_finance_data_results(request: FinanceDataRequest):
    """
    An async generator that streams the finance data extraction graph's output.
    """
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # Use the async version of the stream: astream()
    async for state in finance_data_graph.astream(
        {
            "messages": [("user", request.text)],
        }, 
        config,
        stream_mode="values"
    ):
        print(f"DEBUG API: Finance extraction state keys: {list(state.keys())}")
        
        # Prepare the streaming data
        stream_data = {
            "type": "finance_data_update",
            "thread_id": request.thread_id,
            "status": "processing"
        }
        
        # Get structured output from the state
        if "structured_output" in state:
            structured_metrics = state["structured_output"]
            stream_data["metrics"] = structured_metrics
            stream_data["metrics_count"] = len(structured_metrics)
            print(f"DEBUG API: Found {len(structured_metrics)} structured metrics")
        
        # Get raw extraction for debugging
        if "extracted_metrics" in state:
            raw_extraction = state["extracted_metrics"]
            stream_data["raw_extraction"] = raw_extraction
        
        # Get the final AI message
        if "messages" in state:
            messages = state["messages"]
            for msg in reversed(messages):
                if (hasattr(msg, 'content') and 
                    msg.content and 
                    hasattr(msg, 'type') and 
                    msg.type == 'ai'):
                    stream_data["ai_message"] = msg.content
                    stream_data["processing_stage"] = state.get("processing_stage", "unknown")
                    print(f"DEBUG API: Found AI message with finance data")
                    break
        
        # Only stream if we have meaningful data
        if "metrics" in stream_data or "ai_message" in stream_data:
            data_to_send = json.dumps(stream_data)
            yield f"data: {data_to_send}\n\n"
            await asyncio.sleep(0.1)
    
    # Send final completion event
    final_data = json.dumps({
        "type": "finance_data_complete",
        "thread_id": request.thread_id,
        "status": "completed"
    })
    yield f"data: {final_data}\n\n"


async def stream_transcript_analysis_results(request: TranscriptAnalysisRequest):
    """
    An async generator that streams the transcript analysis graph's output.
    """
    # Use the analyze_transcript function which is already an async generator
    async for state in analyze_transcript(request.file_path, request.thread_id):
        print(f"DEBUG API: Transcript analysis state keys: {list(state.keys())}")
        
        # Prepare the streaming data
        stream_data = {
            "type": "transcript_analysis_update",
            "thread_id": request.thread_id,
            "status": "processing",
            "file_path": request.file_path
        }
        
        # Add current step information
        if "error" in state and state["error"]:
            stream_data["error"] = state["error"]
            stream_data["status"] = "error"
        
        # Add PDF text extraction progress
        if "transcript_text" in state and state["transcript_text"]:
            text_length = len(state["transcript_text"])
            stream_data["pdf_text_length"] = text_length
            stream_data["processing_stage"] = "PDF text extracted"
        
        # Add chunking progress
        if "chunks" in state and state["chunks"]:
            chunks_count = len(state["chunks"])
            stream_data["chunks_count"] = chunks_count
            stream_data["processing_stage"] = "Document chunked"
        
        # Add map phase progress
        if "chunk_results" in state and state["chunk_results"]:
            chunk_results_count = len(state["chunk_results"])
            stream_data["chunk_results_count"] = chunk_results_count
            stream_data["processing_stage"] = "Map phase complete"
        
        # Add reduce phase progress
        if "aggregated_results" in state and state["aggregated_results"]:
            aggregated_results = state["aggregated_results"]
            stream_data["aggregated_results"] = aggregated_results
            stream_data["processing_stage"] = "Reduce phase complete"
            
            # Count metrics
            metrics_count = len(aggregated_results.get("metrics", []))
            stream_data["metrics_count"] = metrics_count
        
        # Add final summary
        if "final_summary" in state and state["final_summary"]:
            stream_data["final_summary"] = state["final_summary"]
            stream_data["processing_stage"] = "Analysis complete"
            stream_data["status"] = "completed"
        
        # Only stream if we have meaningful data
        if "processing_stage" in stream_data:
            data_to_send = json.dumps(stream_data)
            yield f"data: {data_to_send}\n\n"
            await asyncio.sleep(0.1)
    
    # Send final completion event
    final_data = json.dumps({
        "type": "transcript_analysis_complete",
        "thread_id": request.thread_id,
        "status": "completed",
        "file_path": request.file_path
    })
    yield f"data: {final_data}\n\n"


@app.post("/research", response_model=ResearchResponse)
async def research_query(request: ResearchRequest):
    """
    Generate equity research report based on company, sector, and report type
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
          # Get the specific prompt for this request
        specific_prompt = get_prompt_for_request(
            request.company_code, 
            request.sector_code, 
            request.report_type,
            PROMPTS_DATA
        )
          # Run the graph with the specific prompt and request parameters
        final_result = None
          # Use stream_mode="values" to get the final state values
        for state in research_graph.stream(
            {
                "messages": [("user", specific_prompt)],
                "company_code": request.company_code,
                "sector_code": request.sector_code,
                "report_type": request.report_type,
                "quarter": request.quarter,
                "year": request.year
            }, 
            config,
            stream_mode="values"
        ):
            print(f"DEBUG API: State keys: {list(state.keys())}")
            if "messages" in state:
                messages = state["messages"]
                print(f"DEBUG API: Found {len(messages)} total messages")
                
                # Get the last AI message
                for msg in reversed(messages):
                    if (hasattr(msg, 'content') and 
                        msg.content and 
                        hasattr(msg, 'type') and 
                        msg.type == 'ai'):
                        final_result = msg.content
                        print(f"DEBUG API: Found AI message: {msg.content[:100]}...")
                        break
        return ResearchResponse(
            result=final_result or "No result generated",
            company_code=request.company_code,
            sector_code=request.sector_code,
            report_type=request.report_type,
            thread_id=request.thread_id,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
 

@app.post("/extract-finance-data", response_model=None)
async def extract_finance_data(request: FinanceDataRequest):
    """
    Extract financial metrics from text and return structured JSON output.
    This endpoint now streams the results using Server-Sent Events.
    """
    try:
        return StreamingResponse(
            stream_finance_data_results(request), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing finance data extraction: {str(e)}")


@app.post("/analyze-transcript")
async def analyze_transcript_endpoint(request: TranscriptAnalysisRequest):
    """
    Analyze a transcript file using map-reduce pattern and return streaming results.
    This endpoint streams the results using Server-Sent Events.
    """
    try:
        # Validate file path exists
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        return StreamingResponse(
            stream_transcript_analysis_results(request), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing transcript analysis: {str(e)}")


@app.post("/extract-finance-data-sync", response_model=FinanceDataResponse)
async def extract_finance_data_sync(request: FinanceDataRequest):
    """
    Non-streaming version of finance data extraction (for backward compatibility)
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        
        # Run the finance data extraction graph
        final_result = None
        structured_metrics = []
        raw_extraction = ""
        
        # Use stream_mode="values" to get the final state values
        for state in finance_data_graph.stream(
            {
                "messages": [("user", request.text)],
            }, 
            config,
            stream_mode="values"
        ):
            print(f"DEBUG API: Finance extraction state keys: {list(state.keys())}")
            
            # Get structured output from the state
            if "structured_output" in state:
                structured_metrics = state["structured_output"]
                print(f"DEBUG API: Found {len(structured_metrics)} structured metrics")
            
            # Get raw extraction for debugging
            if "extracted_metrics" in state:
                raw_extraction = state["extracted_metrics"]
            
            # Get the final AI message
            if "messages" in state:
                messages = state["messages"]
                for msg in reversed(messages):
                    if (hasattr(msg, 'content') and 
                        msg.content and 
                        hasattr(msg, 'type') and 
                        msg.type == 'ai'):
                        final_result = msg.content
                        print(f"DEBUG API: Found AI message with finance data")
                        break
        
        return FinanceDataResponse(
            metrics=structured_metrics or [],
            thread_id=request.thread_id,
            status="success",
            raw_extraction=raw_extraction
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing finance data extraction: {str(e)}")
    

@app.post("/analyze-transcript-sync", response_model=TranscriptAnalysisResponse)
async def analyze_transcript_sync(request: TranscriptAnalysisRequest):
    """
    Non-streaming version of transcript analysis (for backward compatibility)
    """
    try:
        # Validate file path exists
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        # Process the transcript analysis
        final_summary = ""
        aggregated_results = {}
        error = None
        
        # Use the analyze_transcript async generator and collect final results
        async for state in analyze_transcript(request.file_path, request.thread_id):
            print(f"DEBUG API: Transcript analysis state keys: {list(state.keys())}")
            
            # Check for errors
            if "error" in state and state["error"]:
                error = state["error"]
                break
            
            # Collect final results
            if "final_summary" in state and state["final_summary"]:
                final_summary = state["final_summary"]
            
            if "aggregated_results" in state and state["aggregated_results"]:
                aggregated_results = state["aggregated_results"]
        
        # Check if we have an error
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return TranscriptAnalysisResponse(
            file_path=request.file_path,
            final_summary=final_summary or "No summary generated",
            aggregated_results=aggregated_results or {},
            thread_id=request.thread_id,
            status="success",
            error=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing transcript analysis: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
