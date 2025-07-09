"""
Response models for the Equity Research Agent API
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ResearchResponse(BaseModel):
    """
    Response model for equity research report generation
    
    Attributes:
        result (str): The generated research report content
        company_code (str): The company ticker symbol that was analyzed
        sector_code (str): The sector code for the company
        report_type (str): The type of report that was generated
        thread_id (str): The conversation thread identifier
        status (str): The status of the request processing
        pdf_path (Optional[str]): Path to the generated PDF file (if applicable)
    """
    
    result: str = Field(
        ..., 
        description="Generated research report content"
    )
    
    company_code: str = Field(
        ..., 
        description="Company ticker symbol that was analyzed"
    )
    
    sector_code: str = Field(
        ..., 
        description="Sector code for the company"
    )
    
    report_type: str = Field(
        ..., 
        description="Type of report that was generated"
    )
    
    thread_id: str = Field(
        ..., 
        description="Conversation thread identifier"
    )
    
    status: str = Field(
        ..., 
        description="Status of the request processing",
        example="success"
    )
    
    pdf_path: Optional[str] = Field(
        default=None,
        description="Path to the generated PDF file"
    )

    class Config:
        schema_extra = {
            "example": {
                "result": "Apple Inc. (AAPL) - BUY Recommendation\n\nExecutive Summary:\nApple Inc. continues to demonstrate strong fundamentals...",
                "company_code": "AAPL",
                "sector_code": "TECH", 
                "report_type": "BUY_SELL_HOLD",
                "thread_id": "user_session_123",
                "status": "success",
                "pdf_path": "/reports/AAPL_TECH_BUY_SELL_HOLD_20241201.pdf"
            }
        }


class FinancialMetric(BaseModel):
    """A single financial metric with name and value"""
    metricName: str = Field(..., description="The name of the financial metric")
    metricValue: float = Field(..., description="The numeric value of the metric")


class FinanceDataResponse(BaseModel):
    """
    Response model for financial data extraction
    
    Attributes:
        metrics (List[Dict[str, Any]]): List of extracted financial metrics in JSON format
        thread_id (str): The conversation thread identifier
        status (str): The status of the request processing
        raw_extraction (Optional[str]): Raw extraction result for debugging
    """
    
    metrics: List[Dict[str, Any]] = Field(
        ..., 
        description="List of extracted financial metrics",
        example=[
            {"metricName": "PERatio", "metricValue": 22.34},
            {"metricName": "currentSellingPrice", "metricValue": 201.45}
        ]
    )
    
    thread_id: str = Field(
        ..., 
        description="The conversation thread identifier"
    )
    
    status: str = Field(
        ..., 
        description="Status of the request processing",
        example="success"
    )
    
    raw_extraction: Optional[str] = Field(
        None, 
        description="Raw extraction result for debugging purposes"
    )

    class Config:
        schema_extra = {
            "example": {
                "metrics": [
                    {"metricName": "PERatio", "metricValue": 22.34},
                    {"metricName": "currentSellingPrice", "metricValue": 201.45},
                    {"metricName": "revenueGrowth", "metricValue": 12.5}
                ],
                "thread_id": "finance_session_123",
                "status": "success",
                "raw_extraction": "[{\"metricName\": \"PERatio\", \"metricValue\": 22.34}]"
            }
        }


class TranscriptAnalysisResponse(BaseModel):
    """
    Response model for transcript analysis results
    
    Attributes:
        file_path (str): The path to the analyzed file
        final_summary (str): The final summary of the analyzed transcript
        aggregated_results (Dict[str, Any]): Structured aggregated results from the analysis
        thread_id (str): The conversation thread identifier
        status (str): The status of the request processing
        error (Optional[str]): Error message if processing failed
    """
    
    file_path: str = Field(
        ..., 
        description="The path to the analyzed file"
    )
    
    final_summary: str = Field(
        ..., 
        description="The final summary of the analyzed transcript"
    )
    
    aggregated_results: Dict[str, Any] = Field(
        ..., 
        description="Structured aggregated results from the analysis"
    )
    
    thread_id: str = Field(
        ..., 
        description="The conversation thread identifier"
    )
    
    status: str = Field(
        ..., 
        description="Status of the request processing",
        example="success"
    )
    
    error: Optional[str] = Field(
        None, 
        description="Error message if processing failed"
    )

    class Config:
        schema_extra = {
            "example": {
                "file_path": "docs/2025/Q1/SHELL/QRAReport/q1-2025-qra-document.pdf",
                "final_summary": "Shell PLC Q1 2025 Financial Summary...",
                "aggregated_results": {
                    "metrics": [{"name": "Revenue", "value": "$10.2B", "period": "Q1 2025"}],
                    "guidance": ["Expected growth in renewable energy segment"],
                    "key_drivers": ["Higher oil prices", "Increased production"],
                    "risks": ["Regulatory changes", "Market volatility"]
                },
                "thread_id": "transcript_session_123",
                "status": "success",
                "error": None
            }
        }
