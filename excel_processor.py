"""
Excel Processing Module
Extracts text and tables from Excel documents
"""
import pandas as pd
from typing import List, Dict
import os


class ExcelProcessor:
    """Process Excel files to extract text and tables"""
    
    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
    
    def extract_text(self) -> List[Dict]:
        """Extract text from Excel - convert all sheets to text"""
        text_chunks = []
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(self.excel_path)
            sheet_names = excel_file.sheet_names
            
            for sheet_idx, sheet_name in enumerate(sheet_names, 1):
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                
                # Convert DataFrame to text representation
                text_content = df.to_string(index=False)
                
                if text_content and text_content.strip():
                    text_chunks.append({
                        'type': 'text',
                        'page': sheet_idx,  # Use sheet index as "page"
                        'content': text_content.strip(),
                        'metadata': {
                            'sheet_name': sheet_name,
                            'sheet_index': sheet_idx,
                            'total_sheets': len(sheet_names),
                            'rows': len(df),
                            'columns': len(df.columns),
                            'extraction_method': 'pandas-excel'
                        }
                    })
        except Exception as e:
            print(f"Error extracting text from Excel: {e}")
        
        return text_chunks
    
    def extract_tables(self) -> List[Dict]:
        """Extract tables from Excel - each sheet is a table"""
        table_chunks = []
        
        try:
            excel_file = pd.ExcelFile(self.excel_path)
            sheet_names = excel_file.sheet_names
            
            for sheet_idx, sheet_name in enumerate(sheet_names, 1):
                df = pd.read_excel(self.excel_path, sheet_name=sheet_name)
                
                # Convert to string representation
                table_str = df.to_string(index=False)
                
                table_chunks.append({
                    'type': 'table',
                    'page': sheet_idx,  # Use sheet index as "page"
                    'content': table_str,
                    'dataframe': df.to_dict('records'),
                    'metadata': {
                        'sheet_name': sheet_name,
                        'sheet_index': sheet_idx,
                        'table_index': sheet_idx - 1,
                        'rows': len(df),
                        'columns': len(df.columns),
                        'extraction_method': 'pandas-excel'
                    }
                })
        except Exception as e:
            print(f"Error extracting tables from Excel: {e}")
        
        return table_chunks
    
    def extract_images(self) -> List[Dict]:
        """Excel files don't typically have extractable images in the same way as PDFs"""
        return []
    
    def extract_all(self) -> Dict[str, List[Dict]]:
        """Extract all content types from Excel"""
        return {
            'text': self.extract_text(),
            'images': [],
            'tables': self.extract_tables()
        }

