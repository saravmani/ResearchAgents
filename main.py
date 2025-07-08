from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import uvicorn
import json
import os
import asyncio
from graphs.reportgraph import create_research_graph
from graphs.financedatagraph import create_finance_data_graph
from utils.vector_store import initialize_vector_store
from utils.promptmanager import load_prompts_data, get_prompt_for_request
from models import ResearchRequest, ResearchResponse, FinanceDataRequest, FinanceDataResponse

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

  

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
