"""
PDF to Markdown Converter Utility

This module handles PDF text extraction, cleaning, and conversion to markdown format
for integration with the research agents vector store.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFToMarkdownConverter:
    """
    Converts PDF documents to cleaned markdown format for vector store processing
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the PDF to Markdown converter
        
        Args:
            output_dir: Directory to save converted markdown files (optional)
        """
        if pdfplumber is None:
            raise ImportError("pdfplumber is required. Install it with: pip install pdfplumber")
        
        self.output_dir = output_dir
        logger.info("PDF to Markdown converter initialized with pdfplumber")
    def _tables_to_markdown(self, tables: List[List[List[Optional[str]]]]) -> str:
        """
        Convert extracted tables to markdown format.
        """
        markdown_tables = []
        for table_index, table in enumerate(tables):
            if not table or len(table) == 0:
                continue
            
            # Clean and process table data
            cleaned_table = []
            max_cols = 0
            
            # First pass: clean data and find max columns
            for row in table:
                if row is None:
                    continue
                cleaned_row = []
                for cell in row:
                    if cell is None:
                        cleaned_row.append("")
                    else:
                        # Clean cell content - remove newlines and extra spaces
                        cell_text = str(cell).replace('\n', ' ').replace('\r', ' ').strip()
                        # Escape markdown special characters in table cells
                        cell_text = cell_text.replace('|', '\\|')
                        cleaned_row.append(cell_text)
                
                if cleaned_row:  # Only add non-empty rows
                    cleaned_table.append(cleaned_row)
                    max_cols = max(max_cols, len(cleaned_row))
            
            if not cleaned_table or max_cols == 0:
                continue
            
            # Normalize all rows to have the same number of columns
            for row in cleaned_table:
                while len(row) < max_cols:
                    row.append("")
            
            # Create markdown table
            if len(cleaned_table) > 0:
                # Create header (first row)
                header_row = cleaned_table[0]
                header = "| " + " | ".join(header_row) + " |"
                
                # Create separator
                separator = "| " + " | ".join(["---"] * max_cols) + " |"
                
                # Create body (remaining rows)
                body_rows = []
                for row in cleaned_table[1:]:
                    body_row = "| " + " | ".join(row) + " |"
                    body_rows.append(body_row)
                
                # Combine all parts
                table_markdown = [header, separator] + body_rows
                markdown_tables.append("\n".join(table_markdown))
        
        return "\n\n".join(markdown_tables)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content and tables from a PDF file using pdfplumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content with tables converted to markdown
        """
        table_settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "lines",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
            "text_tolerance": 3,
            "intersection_tolerance": 3,
        }
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = []
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        tables = page.extract_tables(table_settings)
                          # Debug logging for table detection
                        if tables:
                            logger.info(f"Found {len(tables)} tables on page {page_num}")
                            for i, table in enumerate(tables):
                                logger.debug(f"Table {i+1} structure: {len(table)} rows, sample: {table[:2] if table else 'empty'}")
                        else:
                            logger.debug(f"No tables found on page {page_num}")
                        
                        if page_text or tables:
                            text_content.append(f"\n<!-- PAGE {page_num} -->\n")
                            if page_text:
                                text_content.append(page_text)
                            
                            if tables:
                                markdown_tables = self._tables_to_markdown(tables)
                                if markdown_tables.strip():
                                    text_content.append("\n\n" + markdown_tables + "\n\n")
                                    logger.info(f"Successfully converted {len(tables)} tables to markdown on page {page_num}")
                                else:
                                    logger.warning(f"Table conversion resulted in empty markdown on page {page_num}")

                        if page_num % 10 == 0:
                            logger.info(f"Processed {page_num}/{total_pages} pages from {os.path.basename(pdf_path)}")
                    
                    except Exception as e:
                        logger.warning(f"Error extracting content from page {page_num} of {pdf_path}: {e}")
                        continue
                
                extracted_text = "\n".join(text_content)
                logger.info(f"Successfully extracted {len(extracted_text)} characters from {total_pages} pages in {os.path.basename(pdf_path)}")
                
                return extracted_text
                
        except Exception as e:
            logger.error(f"Error reading PDF file {pdf_path} with pdfplumber: {e}")
            return ""
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted PDF text
        
        Args:
            text: Raw extracted text from PDF
            
        Returns:
            Cleaned text content
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Fix broken words (words split across lines)
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Remove extra spaces
        text = re.sub(r' +', ' ', text)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi')
        text = text.replace('ﬂ', 'fl')
        # text = text.replace(''', "'")
        text = text.replace('"', '"')
        text = text.replace('"', '"')
        text = text.replace('–', '-')
        text = text.replace('—', '--')
        
        # Remove standalone numbers (likely page numbers)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        # Clean up line breaks around sentences
        text = re.sub(r'(?<=[.!?])\s*\n\s*(?=[A-Z])', ' ', text)
        
        return text.strip()
    
    def extract_metadata_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        metadata = {
            'source_file': os.path.basename(pdf_path),
            'source_path': pdf_path,
            'document_type': 'pdf_converted',
            'file_size': 0,
            'page_count': 0,
            'title': '',
            'author': '',
            'creation_date': '',
            'company_code': 'UNKNOWN',
            'quarter': None,
            'year': None
        }
        
        try:
            # Get file size
            metadata['file_size'] = os.path.getsize(pdf_path)
            
            # Extract from PDF properties using pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                metadata['page_count'] = len(pdf.pages)
                pdf_metadata = pdf.metadata
                
                metadata['title'] = pdf_metadata.get('Title', '').strip()
                metadata['author'] = pdf_metadata.get('Author', '').strip()
                
                creation_date = pdf_metadata.get('CreationDate', '')
                if creation_date:
                    metadata['creation_date'] = str(creation_date)
            
            # Extract company code, quarter, and year from filename or path
            filename = os.path.basename(pdf_path)
            path_parts = pdf_path.replace('\\', '/').split('/')
            
            # Try to extract from folder structure (docs/YYYY/QX/COMPANY/)
            try:
                docs_index = next(i for i, part in enumerate(path_parts) if part == 'docs')
                if len(path_parts) > docs_index + 3:
                    year_from_path = path_parts[docs_index + 1]
                    quarter_from_path = path_parts[docs_index + 2]
                    company_from_path = path_parts[docs_index + 3]
                    
                    if year_from_path.isdigit() and len(year_from_path) == 4:
                        metadata['year'] = int(year_from_path)
                    if quarter_from_path.startswith('Q'):
                        metadata['quarter'] = quarter_from_path
                    if company_from_path:
                        metadata['company_code'] = company_from_path.upper()
            except (StopIteration, ValueError, IndexError):
                pass
            
            # Fallback: extract from filename (COMPANY_research_QX_YYYY.pdf)
            if metadata['company_code'] == 'UNKNOWN':
                filename_parts = filename.replace('.pdf', '').split('_')
                if len(filename_parts) >= 1:
                    metadata['company_code'] = filename_parts[0].upper()
                
                # Look for quarter and year in filename
                for part in filename_parts:
                    if part.startswith('Q') and len(part) == 2:
                        metadata['quarter'] = part
                    elif part.isdigit() and len(part) == 4:
                        metadata['year'] = int(part)
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {e}")
        
        return metadata
    
    def convert_to_markdown(self, text: str, metadata: Dict[str, Any]) -> str:
        """
        Convert cleaned text to markdown format with proper structure
        
        Args:
            text: Cleaned text content
            metadata: Document metadata
            
        Returns:
            Formatted markdown content
        """
        company_code = metadata.get('company_code', 'UNKNOWN')
        quarter = metadata.get('quarter', '')
        year = metadata.get('year', '')
        title = metadata.get('title', '')
        
        # Create markdown header
        markdown_parts = []
        
        # Title
        if title:
            markdown_parts.append(f"# {title}")
        else:
            period_info = f"{quarter} {year}" if quarter and year else "Research Document"
            markdown_parts.append(f"# {company_code} - {period_info}")
        
        # Metadata section
        markdown_parts.append("\n## Document Information")
        markdown_parts.append(f"- **Company Code**: {company_code}")
        if quarter:
            markdown_parts.append(f"- **Quarter**: {quarter}")
        if year:
            markdown_parts.append(f"- **Year**: {year}")
        markdown_parts.append(f"- **Source**: {metadata.get('source_file', 'Unknown')}")
        markdown_parts.append(f"- **Document Type**: PDF (Converted to Markdown)")
        markdown_parts.append(f"- **Page Count**: {metadata.get('page_count', 0)}")
        
        if metadata.get('author'):
            markdown_parts.append(f"- **Author**: {metadata.get('author')}")
        
        markdown_parts.append("\n---\n")
        
        # Process the main content
        content_lines = text.split('\n')
        processed_content = []
        
        for line in content_lines:
            line = line.strip()
            if not line:
                processed_content.append("")
                continue
            
            # Handle page markers
            if line.startswith('<!-- PAGE'):
                processed_content.append(f"\n{line}\n")
                continue
            
            # Try to identify headers (lines that are all caps or start with numbers/bullets)
            if self._is_likely_header(line):
                # Convert to markdown header
                if len(line) < 100:  # Reasonable header length
                    processed_content.append(f"\n## {line}\n")
                else:
                    processed_content.append(line)
            else:
                processed_content.append(line)
        
        # Join all content
        markdown_parts.append('\n'.join(processed_content))
        
        return '\n'.join(markdown_parts)
    
    def _is_likely_header(self, line: str) -> bool:
        """
        Determine if a line is likely a header/section title
        
        Args:
            line: Text line to analyze
            
        Returns:
            True if line appears to be a header
        """
        line = line.strip()
        
        # Skip very short or very long lines
        if len(line) < 3 or len(line) > 100:
            return False
        
        # Check for all caps (but not if it's mostly numbers)
        if line.isupper() and sum(c.isalpha() for c in line) > len(line) * 0.5:
            return True
        
        # Check for numbered sections
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        
        # Check for roman numerals
        if re.match(r'^[IVX]+\.?\s+[A-Z]', line):
            return True
        
        # Check for bullet points followed by title case
        if re.match(r'^[-•]\s+[A-Z][a-z]', line):
            return True
        
        return False
    
    def process_pdf_file(self, pdf_path: str, output_path: str = None) -> Optional[str]:
        """
        Process a single PDF file and convert it to markdown
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Optional output path for the markdown file
            
        Returns:
            Path to the created markdown file, or None if processing failed
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return None
        
        logger.info(f"Processing PDF: {os.path.basename(pdf_path)}")
        
        # Extract text and metadata
        extracted_text = self.extract_text_from_pdf(pdf_path)
        if not extracted_text:
            logger.error(f"No text could be extracted from {pdf_path}")
            return None
        
        # Clean the text
        cleaned_text = self.clean_extracted_text(extracted_text)
        
        # Extract metadata
        metadata = self.extract_metadata_from_pdf(pdf_path)
        
        # Convert to markdown
        markdown_content = self.convert_to_markdown(cleaned_text, metadata)
        
        # Determine output path
        if not output_path:
            pdf_filename = os.path.basename(pdf_path)
            md_filename = pdf_filename.replace('.pdf', '_converted.md')
            
            if self.output_dir:
                output_path = os.path.join(self.output_dir, md_filename)
            else:
                output_path = os.path.join(os.path.dirname(pdf_path), md_filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write markdown file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logger.info(f"Successfully converted PDF to markdown: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error writing markdown file {output_path}: {e}")
            return None
    
    def process_pdf_directory(self, directory_path: str) -> List[str]:
        """
        Process all PDF files in a directory and convert them to markdown
        
        Args:
            directory_path: Path to directory containing PDF files
            
        Returns:
            List of paths to created markdown files
        """
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        converted_files = []
        pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
        
        if not pdf_files:
            logger.info(f"No PDF files found in {directory_path}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files to process in {directory_path}")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(directory_path, pdf_file)
            converted_path = self.process_pdf_file(pdf_path)
            
            if converted_path:
                converted_files.append(converted_path)
        
        logger.info(f"Successfully converted {len(converted_files)} PDF files to markdown")
        return converted_files


def convert_pdf_to_markdown(pdf_path: str, output_path: str = None) -> Optional[str]:
    """
    Convenience function to convert a single PDF to markdown
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Optional output path for the markdown file
        
    Returns:
        Path to the created markdown file, or None if processing failed
    """
    converter = PDFToMarkdownConverter()
    return converter.process_pdf_file(pdf_path, output_path)


def convert_pdfs_in_directory(directory_path: str, output_dir: str = None) -> List[str]:
    """
    Convenience function to convert all PDFs in a directory to markdown
    
    Args:
        directory_path: Path to directory containing PDF files
        output_dir: Optional output directory for markdown files
        
    Returns:
        List of paths to created markdown files
    """
    converter = PDFToMarkdownConverter(output_dir=output_dir)
    return converter.process_pdf_directory(directory_path)
