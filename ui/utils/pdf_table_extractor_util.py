"""
PDF Table Extractor Utility using Camelot-Py

This utility provides functions to extract tables from PDF documents using camelot-py,
which offers both lattice and stream parsing methods for accurate table extraction.
"""

import os
import json
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

try:
    import camelot
except ImportError:
    print("Warning: camelot-py not installed. Please install it using: pip install camelot-py[cv]")
    camelot = None

logger = logging.getLogger(__name__)


class PDFTableExtractor:
    """
    A class to extract tables from PDF documents using camelot-py
    """
    
    def __init__(self):
        """Initialize the PDF table extractor"""
        if camelot is None:
            raise ImportError("camelot-py is required but not installed. Install with: pip install camelot-py[cv]")
    
    def extract_tables_lattice(self, pdf_path: str, pages: str = 'all', **kwargs) -> List[pd.DataFrame]:
        """
        Extract tables using lattice parsing (for tables with clear borders)
        
        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Page numbers to process (e.g., '1', '1,2,3', 'all')
            **kwargs: Additional camelot parameters
        
        Returns:
            List[pd.DataFrame]: List of extracted tables as DataFrames
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor='lattice', **kwargs)
            logger.info(f"Extracted {len(tables)} tables using lattice method from {pdf_path}")
            return [table.df for table in tables]
        except Exception as e:
            logger.error(f"Error extracting tables with lattice method: {str(e)}")
            return []
    
    def extract_tables_stream(self, pdf_path: str, pages: str = 'all', **kwargs) -> List[pd.DataFrame]:
        """
        Extract tables using stream parsing (for tables without clear borders)
        
        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Page numbers to process (e.g., '1', '1,2,3', 'all')
            **kwargs: Additional camelot parameters
        
        Returns:
            List[pd.DataFrame]: List of extracted tables as DataFrames
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor='stream', **kwargs)
            logger.info(f"Extracted {len(tables)} tables using stream method from {pdf_path}")
            return [table.df for table in tables]
        except Exception as e:
            logger.error(f"Error extracting tables with stream method: {str(e)}")
            return []
    
    def extract_tables_auto(self, pdf_path: str, pages: str = 'all') -> Tuple[List[pd.DataFrame], str]:
        """
        Automatically choose the best extraction method by trying both lattice and stream
        
        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Page numbers to process
        
        Returns:
            Tuple[List[pd.DataFrame], str]: (List of extracted tables, method used)
        """
        # Try lattice first (usually better for structured tables)
        lattice_tables = self.extract_tables_lattice(pdf_path, pages)
        
        if lattice_tables and any(not df.empty for df in lattice_tables):
            return lattice_tables, "lattice"
        
        # Fall back to stream if lattice didn't work well
        stream_tables = self.extract_tables_stream(pdf_path, pages)
        return stream_tables, "stream"
    
    def get_table_info(self, pdf_path: str, pages: str = 'all', flavor: str = 'lattice') -> List[Dict]:
        """
        Get detailed information about tables in the PDF
        
        Args:
            pdf_path (str): Path to the PDF file
            pages (str): Page numbers to process
            flavor (str): Extraction method ('lattice' or 'stream')
        
        Returns:
            List[Dict]: List of table information dictionaries
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages=pages, flavor=flavor)
            table_info = []
            
            for i, table in enumerate(tables):
                info = {
                    'table_index': i,
                    'page': table.page,
                    'dimensions': table.shape,
                    'accuracy': table.accuracy,
                    'whitespace': table.whitespace,
                    'order': table.order,
                    'area': table._bbox if hasattr(table, '_bbox') else None
                }
                table_info.append(info)
            
            return table_info
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            return []
    
    def save_tables_to_excel(self, tables: List[pd.DataFrame], output_path: str, 
                           sheet_names: Optional[List[str]] = None) -> bool:
        """
        Save extracted tables to an Excel file with multiple sheets
        
        Args:
            tables (List[pd.DataFrame]): List of tables to save
            output_path (str): Path to save the Excel file
            sheet_names (Optional[List[str]]): Custom sheet names
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not tables:
                logger.warning("No tables to save")
                return False
            
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, table in enumerate(tables):
                    sheet_name = sheet_names[i] if sheet_names and i < len(sheet_names) else f'Table_{i+1}'
                    table.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Saved {len(tables)} tables to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tables to Excel: {str(e)}")
            return False
    
    def save_tables_to_csv(self, tables: List[pd.DataFrame], output_dir: str) -> List[str]:
        """
        Save extracted tables to separate CSV files
        
        Args:
            tables (List[pd.DataFrame]): List of tables to save
            output_dir (str): Directory to save CSV files
        
        Returns:
            List[str]: List of saved file paths
        """
        saved_files = []
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            for i, table in enumerate(tables):
                filename = f"table_{i+1}.csv"
                file_path = os.path.join(output_dir, filename)
                table.to_csv(file_path, index=False)
                saved_files.append(file_path)
            
            logger.info(f"Saved {len(tables)} tables to {output_dir}")
            return saved_files
        except Exception as e:
            logger.error(f"Error saving tables to CSV: {str(e)}")
            return []
    
    def save_tables_to_json(self, tables: List[pd.DataFrame], output_path: str) -> bool:
        """
        Save extracted tables to JSON format
        
        Args:
            tables (List[pd.DataFrame]): List of tables to save
            output_path (str): Path to save the JSON file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            tables_json = {
                f"table_{i+1}": table.to_dict('records') 
                for i, table in enumerate(tables)
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tables_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(tables)} tables to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tables to JSON: {str(e)}")
            return False
    
    def extract_and_save(self, pdf_path: str, output_dir: str, 
                        format: str = 'excel', pages: str = 'all', 
                        method: str = 'auto') -> Dict[str, any]:
        """
        Extract tables and save in specified format
        
        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Directory to save extracted tables
            format (str): Output format ('excel', 'csv', 'json')
            pages (str): Page numbers to process
            method (str): Extraction method ('lattice', 'stream', 'auto')
        
        Returns:
            Dict: Results including extracted tables and save status
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract tables
        if method == 'auto':
            tables, used_method = self.extract_tables_auto(pdf_path, pages)
        elif method == 'lattice':
            tables = self.extract_tables_lattice(pdf_path, pages)
            used_method = 'lattice'
        elif method == 'stream':
            tables = self.extract_tables_stream(pdf_path, pages)
            used_method = 'stream'
        else:
            raise ValueError("Method must be 'lattice', 'stream', or 'auto'")
        
        if not tables:
            return {
                'success': False,
                'message': 'No tables extracted',
                'tables_count': 0,
                'method_used': used_method
            }
        
        # Save in requested format
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        if format == 'excel':
            output_path = os.path.join(output_dir, f"{pdf_name}_tables.xlsx")
            success = self.save_tables_to_excel(tables, output_path)
            saved_files = [output_path] if success else []
        elif format == 'csv':
            csv_dir = os.path.join(output_dir, f"{pdf_name}_tables")
            saved_files = self.save_tables_to_csv(tables, csv_dir)
            success = len(saved_files) > 0
        elif format == 'json':
            output_path = os.path.join(output_dir, f"{pdf_name}_tables.json")
            success = self.save_tables_to_json(tables, output_path)
            saved_files = [output_path] if success else []
        else:
            raise ValueError("Format must be 'excel', 'csv', or 'json'")
        
        return {
            'success': success,
            'tables_count': len(tables),
            'method_used': used_method,
            'saved_files': saved_files,
            'tables': tables
        }


def extract_pdf_tables(pdf_path: str, method: str = 'auto', pages: str = 'all') -> Dict[str, any]:
    """
    Convenience function to extract tables from a PDF
    
    Args:
        pdf_path (str): Path to the PDF file
        method (str): Extraction method ('lattice', 'stream', 'auto')
        pages (str): Page numbers to process
    
    Returns:
        Dict: Extraction results
    """
    if not os.path.exists(pdf_path):
        return {
            'success': False,
            'message': f'PDF file not found: {pdf_path}',
            'tables': []
        }
    
    try:
        extractor = PDFTableExtractor()
        
        if method == 'auto':
            tables, used_method = extractor.extract_tables_auto(pdf_path, pages)
        elif method == 'lattice':
            tables = extractor.extract_tables_lattice(pdf_path, pages)
            used_method = 'lattice'
        elif method == 'stream':
            tables = extractor.extract_tables_stream(pdf_path, pages)
            used_method = 'stream'
        else:
            return {
                'success': False,
                'message': f'Invalid method: {method}',
                'tables': []
            }
        
        return {
            'success': True,
            'tables_count': len(tables),
            'method_used': used_method,
            'tables': tables
        }
    
    except Exception as e:
        logger.error(f"Error in extract_pdf_tables: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'tables': []
        }


if __name__ == "__main__":
    # Example usage
    pdf_path = "sample.pdf"  # Replace with your PDF path
    
    if os.path.exists(pdf_path):
        result = extract_pdf_tables(pdf_path, method='auto')
        
        if result['success']:
            print(f"Successfully extracted {result['tables_count']} tables using {result['method_used']} method")
            for i, table in enumerate(result['tables']):
                print(f"\nTable {i+1} shape: {table.shape}")
                print(table.head())
        else:
            print(f"Failed to extract tables: {result['message']}")
    else:
        print(f"PDF file not found: {pdf_path}")
