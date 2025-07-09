"""
Request models for the Equity Research Agent API
"""

from pydantic import BaseModel, Field
from typing import Optional


class ResearchRequest(BaseModel):
    """
    Request model for equity research report generation
    
    Attributes:
        company_code (str): The company ticker symbol (e.g., 'AAPL', 'MSFT')
        sector_code (str): The sector code for the company (e.g., 'TECH', 'FINANCE')
        report_type (str): The type of report to generate (e.g., 'BUY_SELL_HOLD')
        quarter (str): Quarter for the report (Q1, Q2, Q3, Q4)
        year (int): Year for the report (2020-2030)
        thread_id (str): Unique identifier for the conversation thread (default: 'default')
    """
    
    company_code: str = Field(
        ..., 
        description="Company ticker symbol",
        example="AAPL"
    )
    
    sector_code: str = Field(
        ..., 
        description="Sector code for the company",
        example="TECH"
    )
    
    report_type: str = Field(
        ..., 
        description="Type of report to generate",
        example="BUY_SELL_HOLD"
    )
    
    quarter: str = Field(
        ...,
        description="Quarter for the report (Q1, Q2, Q3, Q4)",
        example="Q1" 
    )
    
    year: int = Field(
        ...,
        description="Year for the report",
        example=2025,
        ge=2020,
        le=2030
    )
    thread_id: str = Field(
        default="default", 
        description="Unique identifier for the conversation thread"
    )

    class Config:
        schema_extra = {
            "example": {
                "company_code": "AAPL",
                "sector_code": "TECH",
                "report_type": "BUY_SELL_HOLD",
                "quarter": "Q1",
                "year": 2025,
                "thread_id": "user_session_123"
            }
        }


class FinanceDataRequest(BaseModel):
    """
    Request model for financial data extraction from text
    
    Attributes:
        text (str): The text content containing financial metrics to extract
        thread_id (str): Unique identifier for the conversation thread (default: 'default')
    """
    
    text: str = Field(
        ..., 
        description="Text content containing financial metrics to extract",
        example="The company has a PE ratio of 22.34 and current selling price is $201.45. Market cap stands at $1.2B."
    )
    
    thread_id: str = Field(
        default="default", 
        description="Unique identifier for the conversation thread"
    )

    class Config:
        schema_extra = {
            "example": {
                "text": "The company reported strong results with PE ratio of 15.2, current selling price of $145.67, and revenue growth of 12.5%.",
                "thread_id": "finance_session_123"
            }
        }


class TranscriptAnalysisRequest(BaseModel):
    """
    Request model for analyzing a transcript from a file path.
    
    Attributes:
        file_path (str): The local path to the transcript file (e.g., PDF).
        thread_id (str): Unique identifier for the conversation thread.
    """
    file_path: str = Field(
        ...,
        description="The local path to the transcript file to be analyzed.",
        example="docs/2025/Q1/SHELL/QRAReport/q1-2025-qra-document.pdf"
    )
    thread_id: str = Field(
        default="default-transcript",
        description="Unique identifier for the transcript analysis thread."
    )
