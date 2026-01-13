"""
PDF Processing Module
Extracts text, images, and tables from PDF documents separately
"""
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd
import io
from typing import List, Dict, Tuple
import base64


class PDFProcessor:
    """Process PDF files to extract text, images, and tables separately"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        
    def extract_text(self) -> List[Dict]:
        """Extract all text from PDF pages"""
        text_chunks = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and text.strip():
                    text_chunks.append({
                        'type': 'text',
                        'page': page_num,
                        'content': text.strip(),
                        'metadata': {
                            'page_number': page_num,
                            'total_pages': len(pdf.pages)
                        }
                    })
        
        return text_chunks
    
    def extract_images(self) -> List[Dict]:
        """Extract all images from PDF pages"""
        image_chunks = []
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = self.doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Convert to base64 for storage
                    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    image_chunks.append({
                        'type': 'image',
                        'page': page_num + 1,
                        'content': image_b64,
                        'metadata': {
                            'page_number': page_num + 1,
                            'image_index': img_index,
                            'format': image_ext,
                            'width': base_image.get('width', 0),
                            'height': base_image.get('height', 0)
                        }
                    })
                except Exception as e:
                    print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                    continue
        
        return image_chunks
    
    def extract_tables(self) -> List[Dict]:
        """Extract all tables from PDF pages"""
        table_chunks = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = page.extract_tables()
                
                for table_index, table in enumerate(tables):
                    if table:
                        # Convert table to DataFrame for easier handling
                        df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
                        
                        # Convert to string representation
                        table_str = df.to_string(index=False)
                        
                        table_chunks.append({
                            'type': 'table',
                            'page': page_num,
                            'content': table_str,
                            'dataframe': df.to_dict('records'),  # Store as dict for JSON serialization
                            'metadata': {
                                'page_number': page_num,
                                'table_index': table_index,
                                'rows': len(table),
                                'columns': len(table[0]) if table[0] else 0
                            }
                        })
        
        return table_chunks
    
    def extract_all(self) -> Dict[str, List[Dict]]:
        """Extract all content types from PDF"""
        return {
            'text': self.extract_text(),
            'images': self.extract_images(),
            'tables': self.extract_tables()
        }
    
    def close(self):
        """Close the PDF document"""
        if self.doc:
            self.doc.close()

