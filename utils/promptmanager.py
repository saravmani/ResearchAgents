"""
Prompt Manager utility for handling prompt loading and retrieval.

This module provides functionality to load prompts from configuration files
and retrieve specific prompts based on company, sector, and report type.
"""

import json
import os
from typing import Dict, Any, List


def load_prompts_data() -> List[Dict[str, Any]]:
    """Load the prompts configuration from JSON file"""
    try:
        # Get the path relative to the project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # Go up one level from utils/
        prompts_path = os.path.join(project_root, "Prompts.json")
        
        with open(prompts_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading prompts: {e}")
        return []


def get_prompt_for_request(company_code: str, sector_code: str, report_type: str, prompts_data: List[Dict[str, Any]]) -> str:
    """Get the specific prompt for the given parameters"""
    # Search for matching prompt in the data
    for prompt_config in prompts_data:
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
