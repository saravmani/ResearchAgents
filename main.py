from fastapi import FastAPI, HTTPException
from typing import Dict, Any
import uvicorn
import json
import os
from graph import create_research_graph
from vector_store import initialize_vector_store
from models import ResearchRequest, ResearchResponse

app = FastAPI(title="Equity Research Agent API with ChromaDB", version="1.0.0")

# Initialize vector store on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the vector store when the API starts"""
    print("🚀 Initializing Equity Research API with ChromaDB...")
    try:
        vectorstore = initialize_vector_store()
        stats = vectorstore.get_collection_stats()
        print(f"✅ Vector store initialized: {stats}")
    except Exception as e:
        print(f"❌ Error initializing vector store: {e}")

# Load prompts data
def load_prompts_data():
    """Load the prompts configuration from JSON file"""
    try:
        prompts_path = os.path.join(os.path.dirname(__file__), "Prompts.json")
        with open(prompts_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return []

PROMPTS_DATA = load_prompts_data()

def get_prompt_for_request(company_code: str, sector_code: str, report_type: str) -> str:
    """Get the specific prompt for the given parameters"""
    # Search for matching prompt in the data
    for prompt_config in PROMPTS_DATA:
        if (prompt_config.get("CompanyCode") == company_code and 
            prompt_config.get("SectorCode") == sector_code and 
            prompt_config.get("ReportType") == report_type):
            
            prompt = prompt_config.get("Prompt", "No specific prompt found")
            print(f"✅ Found matching prompt for {company_code}-{sector_code}-{report_type}")
            return prompt
    
    # If no exact match found, return a generic prompt
    generic_prompt = f"""You are an expert equity research analyst. Generate a comprehensive {report_type} 
    for {company_code} in the {sector_code} sector. Provide professional analysis including company overview, 
    financial performance, market position, risks, and investment recommendation."""
    
    print(f"⚠️ No specific prompt found, using generic prompt for {company_code}-{sector_code}-{report_type}")
    return generic_prompt

# Pydantic models for request/response - moved to models/ package

# Initialize the graph
research_graph = create_research_graph()

@app.get("/")
async def root():
    return {"message": "Research Agent API is running!"}

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
            request.report_type
        )
          # Run the graph with the specific prompt and request parameters
        final_result = None
        
        # Use stream_mode="values" to get the final state values
        for state in research_graph.stream(
            {
                "messages": [("user", specific_prompt)],
                "company_code": request.company_code,
                "sector_code": request.sector_code,
                "report_type": request.report_type
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

  

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
