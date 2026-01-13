"""
PDF Processing Module
Extracts text, images, and tables from PDF documents separately
Uses marker-pdf for better extraction accuracy
"""
try:
    from marker.convert import convert_single_pdf
    from marker.models import load_all_models
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    print("Warning: marker-pdf not available, falling back to pdfplumber/PyMuPDF")

import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import pandas as pd
import io
from typing import List, Dict, Tuple
import base64
import os
import tempfile
import re


class PDFProcessor:
    """Process PDF files to extract text, images, and tables separately"""
    
    def __init__(self, pdf_path: str, use_marker: bool = True):
        self.pdf_path = pdf_path
        self.use_marker = use_marker and MARKER_AVAILABLE
        self.doc = fitz.open(pdf_path)
        
        # Load marker models if using marker
        if self.use_marker:
            try:
                print("Loading marker-pdf models...")
                self.marker_models = load_all_models()
                print("Marker models loaded successfully")
            except Exception as e:
                print(f"Error loading marker models: {e}")
                print("Falling back to pdfplumber/PyMuPDF")
                self.use_marker = False
    
    def extract_text(self) -> List[Dict]:
        """Extract all text from PDF pages"""
        text_chunks = []
        
        if self.use_marker:
            try:
                # Use marker-pdf to extract text
                print("Extracting text using marker-pdf...")
                result = convert_single_pdf(
                    self.pdf_path,
                    self.marker_models,
                    batch_multiplier=1,
                    max_pages=None,
                    langs=None,
                    ocr_all_pages=False,
                    render_math=True,
                    output_format="text"
                )
                
                # marker returns a dictionary with 'text' and 'images' keys
                if result and 'text' in result:
                    # Split by pages (marker processes the whole document)
                    # For now, we'll treat it as a single chunk per page
                    # You may need to adjust based on marker's actual output format
                    full_text = result.get('text', '')
                    
                    # Try to split by pages if possible
                    # If marker doesn't provide page info, we'll use pdfplumber for page count
                    with pdfplumber.open(self.pdf_path) as pdf:
                        total_pages = len(pdf.pages)
                        # Roughly divide text by pages
                        text_per_page = len(full_text) // total_pages if total_pages > 0 else len(full_text)
                        
                        for page_num in range(1, total_pages + 1):
                            start_idx = (page_num - 1) * text_per_page
                            end_idx = page_num * text_per_page if page_num < total_pages else len(full_text)
                            page_text = full_text[start_idx:end_idx].strip()
                            
                            if page_text:
                                text_chunks.append({
                                    'type': 'text',
                                    'page': page_num,
                                    'content': page_text,
                                    'metadata': {
                                        'page_number': page_num,
                                        'total_pages': total_pages,
                                        'extraction_method': 'marker-pdf'
                                    }
                                })
                
            except Exception as e:
                print(f"Error using marker-pdf: {e}")
                print("Falling back to pdfplumber")
                self.use_marker = False
        
        # Fallback to pdfplumber
        if not self.use_marker:
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
                                'total_pages': len(pdf.pages),
                                'extraction_method': 'pdfplumber'
                            }
                        })
        
        return text_chunks
    
    def extract_images(self) -> List[Dict]:
        """Extract all images from PDF pages"""
        image_chunks = []
        
        if self.use_marker:
            try:
                # Use marker-pdf to extract images
                print("Extracting images using marker-pdf...")
                result = convert_single_pdf(
                    self.pdf_path,
                    self.marker_models,
                    batch_multiplier=1,
                    max_pages=None,
                    langs=None,
                    ocr_all_pages=False,
                    render_math=True,
                    output_format="text"
                )
                
                # marker may extract images, check the result structure
                if result and 'images' in result:
                    images_data = result.get('images', [])
                    for img_index, img_data in enumerate(images_data):
                        # Process marker image data
                        # Adjust based on marker's actual image format
                        try:
                            if isinstance(img_data, dict):
                                image_bytes = img_data.get('data', b'')
                                image_ext = img_data.get('format', 'png')
                                page_num = img_data.get('page', 1)
                            else:
                                # If images are in a different format
                                continue
                            
                            if image_bytes:
                                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                                image_chunks.append({
                                    'type': 'image',
                                    'page': page_num,
                                    'content': image_b64,
                                    'metadata': {
                                        'page_number': page_num,
                                        'image_index': img_index,
                                        'format': image_ext,
                                        'extraction_method': 'marker-pdf'
                                    }
                                })
                        except Exception as e:
                            print(f"Error processing marker image {img_index}: {e}")
                            continue
                            
            except Exception as e:
                print(f"Error using marker-pdf for images: {e}")
                print("Falling back to PyMuPDF")
        
        # Fallback to PyMuPDF
        if not image_chunks:
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
                                'extraction_method': 'pymupdf'
                            }
                        })
                    except Exception as e:
                        print(f"Error extracting image {img_index} from page {page_num + 1}: {e}")
                        continue
        
        return image_chunks
    
    def _parse_markdown_table(self, markdown_text: str) -> List[List[str]]:
        """Parse a markdown table string into a 2D list"""
        lines = markdown_text.strip().split('\n')
        table_data = []
        
        for line in lines:
            # Skip separator lines (e.g., |---|---|)
            if re.match(r'^\|[\s\-\|:]+\|$', line):
                continue
            # Parse table row
            if '|' in line:
                # Remove leading/trailing pipes and split
                cells = [cell.strip() for cell in line.strip().split('|')]
                # Remove empty cells at start/end
                if cells and not cells[0]:
                    cells = cells[1:]
                if cells and not cells[-1]:
                    cells = cells[:-1]
                if cells:
                    table_data.append(cells)
        
        return table_data if len(table_data) > 1 else []  # Need at least header + 1 row
    
    def extract_tables(self) -> List[Dict]:
        """Extract all tables from PDF pages"""
        table_chunks = []
        
        if self.use_marker:
            try:
                # Use marker-pdf to extract tables
                print("Extracting tables using marker-pdf...")
                result = convert_single_pdf(
                    self.pdf_path,
                    self.marker_models,
                    batch_multiplier=1,
                    max_pages=None,
                    langs=None,
                    ocr_all_pages=False,
                    render_math=True,
                    output_format="text"
                )
                
                # marker converts tables to markdown format in the text
                if result and 'text' in result:
                    full_text = result.get('text', '')
                    
                    # Find all markdown tables in the text
                    # Markdown tables start with | and have a separator line
                    table_pattern = r'(\|.+\|\n\|[\s\-\|:]+\|\n(?:\|.+\|\n?)+)'
                    markdown_tables = re.findall(table_pattern, full_text, re.MULTILINE)
                    
                    if markdown_tables:
                        print(f"Found {len(markdown_tables)} tables in marker output")
                        
                        # Get page count for metadata
                        with pdfplumber.open(self.pdf_path) as pdf:
                            total_pages = len(pdf.pages)
                        
                        for table_index, md_table in enumerate(markdown_tables):
                            try:
                                # Parse markdown table
                                table_data = self._parse_markdown_table(md_table)
                                
                                if table_data and len(table_data) > 1:
                                    # Convert to DataFrame
                                    df = pd.DataFrame(table_data[1:], columns=table_data[0] if table_data[0] else None)
                                    
                                    # Convert to string representation
                                    table_str = df.to_string(index=False)
                                    
                                    # Estimate page number (rough approximation)
                                    # Find position in full text to estimate page
                                    table_pos = full_text.find(md_table)
                                    estimated_page = min(int((table_pos / len(full_text)) * total_pages) + 1, total_pages) if full_text else 1
                                    
                                    table_chunks.append({
                                        'type': 'table',
                                        'page': estimated_page,
                                        'content': table_str,
                                        'dataframe': df.to_dict('records'),
                                        'metadata': {
                                            'page_number': estimated_page,
                                            'table_index': table_index,
                                            'rows': len(table_data),
                                            'columns': len(table_data[0]) if table_data[0] else 0,
                                            'extraction_method': 'marker-pdf'
                                        }
                                    })
                            except Exception as e:
                                print(f"Error parsing marker table {table_index}: {e}")
                                continue
                    
                    if not table_chunks:
                        print("No markdown tables found in marker output, falling back to pdfplumber")
                        self.use_marker = False
                    else:
                        print(f"Successfully extracted {len(table_chunks)} tables using marker-pdf")
                        return table_chunks
                    
            except Exception as e:
                print(f"Error using marker-pdf for tables: {e}")
                print("Falling back to pdfplumber")
                self.use_marker = False
        
        # Fallback to pdfplumber for tables
        if not self.use_marker:
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
                                    'columns': len(table[0]) if table[0] else 0,
                                    'extraction_method': 'pdfplumber'
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
