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
