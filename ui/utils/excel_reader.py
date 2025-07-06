import pandas as pd
import json
import os
from typing import List, Dict, Any, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelReader:
    """
    A utility class for reading Excel files and extracting specific columns as JSON.
    Supports reading by column letters (A, B, C...) and custom header row numbers.
    """
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.xlsm']
    
    def _column_letter_to_index(self, column_letter: str) -> int:
        """
        Convert Excel column letter to zero-based index.
        A=0, B=1, C=2, ..., Z=25, AA=26, AB=27, etc.
        
        Args:
            column_letter (str): Excel column letter (e.g., 'A', 'B', 'AC')
            
        Returns:
            int: Zero-based column index
        """
        column_letter = column_letter.upper()
        result = 0
        for char in column_letter:
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result - 1
    
    def _validate_file(self, filename_with_path: str) -> bool:
        """
        Validate if the file exists and is a supported Excel format.
        
        Args:
            filename_with_path (str): Full path to the Excel file
            
        Returns:
            bool: True if file is valid, False otherwise
        """
        if not os.path.exists(filename_with_path):
            logger.error(f"File not found: {filename_with_path}")
            return False
        
        file_extension = os.path.splitext(filename_with_path)[1].lower()
        if file_extension not in self.supported_formats:
            logger.error(f"Unsupported file format: {file_extension}")
            logger.info(f"Supported formats: {', '.join(self.supported_formats)}")
            return False
        
        return True
    
    def _read_excel_file(self, filename_with_path: str, header_row_number: int) -> Optional[pd.DataFrame]:
        """
        Read Excel file into a pandas DataFrame.
        
        Args:
            filename_with_path (str): Full path to the Excel file
            header_row_number (int): Row number to use as header (1-based)
            
        Returns:
            pd.DataFrame or None: DataFrame if successful, None if failed
        """
        try:
            # Convert to zero-based index for pandas
            header_index = header_row_number - 1 if header_row_number > 0 else None
            
            # Read Excel file
            df = pd.read_excel(
                filename_with_path,
                header=header_index,
                engine='openpyxl'  # Use openpyxl for better compatibility
            )
            
            logger.info(f"Successfully read Excel file: {filename_with_path}")
            logger.info(f"Shape: {df.shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error reading Excel file: {str(e)}")
            return None
    
    def _extract_columns(self, df: pd.DataFrame, columns_to_read: List[str]) -> pd.DataFrame:
        """
        Extract specific columns from DataFrame using column letters.
        
        Args:
            df (pd.DataFrame): Source DataFrame
            columns_to_read (List[str]): List of column letters to extract
            
        Returns:
            pd.DataFrame: DataFrame with only the specified columns
        """
        try:
            # Convert column letters to indices
            column_indices = [self._column_letter_to_index(col) for col in columns_to_read]
            
            # Validate column indices
            max_columns = len(df.columns)
            valid_indices = []
            valid_letters = []
            
            for i, (letter, index) in enumerate(zip(columns_to_read, column_indices)):
                if 0 <= index < max_columns:
                    valid_indices.append(index)
                    valid_letters.append(letter)
                else:
                    logger.warning(f"Column {letter} (index {index}) is out of range. Max columns: {max_columns}")
            
            if not valid_indices:
                logger.error("No valid columns found")
                return pd.DataFrame()
              # Extract columns by position
            extracted_df = df.iloc[:, valid_indices].copy()
            
            # Rename columns to use only the header values (no column letter prefix)
            new_column_names = {}
            for i, letter in enumerate(valid_letters):
                old_name = extracted_df.columns[i]
                # Use only the original column name/header value
                if pd.notna(old_name) and str(old_name).strip():
                    new_column_names[old_name] = str(old_name).strip()
                else:
                    # If no header name, use the column letter as fallback
                    new_column_names[old_name] = f"Column_{letter}"
            
            extracted_df.rename(columns=new_column_names, inplace=True)
            
            logger.info(f"Extracted {len(valid_letters)} columns: {valid_letters}")
            
            return extracted_df
            
        except Exception as e:
            logger.error(f"Error extracting columns: {str(e)}")
            return pd.DataFrame()
    
    def _dataframe_to_json(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to JSON array format.
        
        Args:
            df (pd.DataFrame): DataFrame to convert
            
        Returns:
            List[Dict[str, Any]]: JSON array representation
        """
        try:
            # Replace NaN values with None for proper JSON serialization
            df_clean = df.where(pd.notna(df), None)
            
            # Convert to list of dictionaries
            json_data = df_clean.to_dict('records')
            
            logger.info(f"Converted DataFrame to JSON with {len(json_data)} records")
            
            return json_data
            
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}")
            return []
    
    def fetch_columns(self, 
                     columns_to_read: List[str], 
                     header_row_number: int, 
                     filename_with_path: str) -> List[Dict[str, Any]]:
        """
        Main method to fetch specific columns from Excel file and return as JSON array.
        
        Args:
            columns_to_read (List[str]): List of Excel column letters (e.g., ['B', 'D', 'AC'])
            header_row_number (int): Row number to use as header (1-based, e.g., 3 means row 3)
            filename_with_path (str): Full path to the Excel file
            
        Returns:
            List[Dict[str, Any]]: JSON array with the extracted data
            
        Example:
            reader = ExcelReader()
            result = reader.fetch_columns(['B', 'D', 'AC'], 3, '/path/to/file.xlsx')
            # Returns: [{'B_Name': 'John', 'D_Age': 25, 'AC_Score': 95.5}, ...]
        """
        try:
            
            # Validate file
            # if not self._validate_file(filename_with_path):
            #     return []
            
            # Read Excel file
            df = self._read_excel_file(filename_with_path, header_row_number)
            if df is None:
                return []
            
            # Extract specified columns
            extracted_df = self._extract_columns(df, columns_to_read)
            if extracted_df.empty:
                logger.warning("No data extracted")
                return []
            
            # Convert to JSON
            json_result = self._dataframe_to_json(extracted_df)
            
            logger.info(f"Successfully extracted {len(json_result)} rows")
            
            return json_result
            
        except Exception as e:
            logger.error(f"Unexpected error in fetch_columns: {str(e)}")
            return []
    
    def get_sheet_info(self, filename_with_path: str) -> Dict[str, Any]:
        """
        Get basic information about the Excel file (sheets, dimensions, etc.).
        
        Args:
            filename_with_path (str): Full path to the Excel file
            
        Returns:
            Dict[str, Any]: Information about the Excel file
        """
        try:
            if not self._validate_file(filename_with_path):
                return {}
            
            # Read all sheets
            excel_file = pd.ExcelFile(filename_with_path)
            
            info = {
                "filename": os.path.basename(filename_with_path),
                "full_path": filename_with_path,
                "sheet_names": excel_file.sheet_names,
                "total_sheets": len(excel_file.sheet_names),
                "sheets_info": {}
            }
            
            # Get info for each sheet
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(filename_with_path, sheet_name=sheet_name)
                    info["sheets_info"][sheet_name] = {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "column_names": list(df.columns)
                    }
                except Exception as e:
                    info["sheets_info"][sheet_name] = {"error": str(e)}
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting sheet info: {str(e)}")
            return {"error": str(e)}

# Convenience function for direct usage
def fetch_columns(columns_to_read: List[str], 
                 header_row_number: int, 
                 filename_with_path: str) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch columns from Excel file.
    
    Args:
        columns_to_read (List[str]): List of Excel column letters (e.g., ['B', 'D', 'AC'])
        header_row_number (int): Row number to use as header (1-based)
        filename_with_path (str): Full path to the Excel file
        
    Returns:
        List[Dict[str, Any]]: JSON array with the extracted data
        
    Example:
        result = fetch_columns(['B', 'D', 'AC'], 3, '/path/to/file.xlsx')
    """
    reader = ExcelReader()
    return reader.fetch_columns(columns_to_read, header_row_number, filename_with_path)

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    print("Excel Reader Utility")
    print("===================")
    
    # Create reader instance
    reader = ExcelReader()
    
    # Example file path (adjust as needed)
    example_file = "sample_data.xlsx"
    
    if os.path.exists(example_file):
        # Get file info
        info = reader.get_sheet_info(example_file)
        print(f"File info: {json.dumps(info, indent=2)}")
        
        # Extract specific columns
        result = reader.fetch_columns(['B', 'D', 'AC'], 3, example_file)
        print(f"Extracted data: {json.dumps(result, indent=2)}")
    else:
        print(f"Example file {example_file} not found.")
        print("Usage example:")
        print("result = fetch_columns(['B', 'D', 'AC'], 3, '/path/to/your/file.xlsx')")
