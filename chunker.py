"""
Chunking Module
Separate chunking logic for text, images, and tables
Now supports section-based chunking to keep related content together
"""
from typing import List, Dict
import re
from config import TEXT_CHUNK_SIZE, TEXT_CHUNK_OVERLAP


class Chunker:
    """Handle chunking for different content types"""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = TEXT_CHUNK_SIZE, 
                   overlap: int = TEXT_CHUNK_OVERLAP) -> List[str]:
        """Chunk text into smaller pieces with overlap"""
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_text = ' '.join(current_chunk[-overlap//50:]) if len(current_chunk) > overlap//50 else current_chunk[-1]
                current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                current_length = len(' '.join(current_chunk))
            else:
                current_chunk.append(sentence)
                current_length += sentence_length + 1
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def chunk_text_content(text_chunks: List[Dict]) -> List[Dict]:
        """Chunk text content from PDF"""
        chunked_content = []
        
        for text_item in text_chunks:
            chunks = Chunker.chunk_text(text_item['content'])
            
            for idx, chunk in enumerate(chunks):
                chunked_content.append({
                    'type': 'text',
                    'page': text_item['page'],
                    'content': chunk,
                    'chunk_index': idx,
                    'total_chunks': len(chunks),
                    'metadata': {
                        **text_item['metadata'],
                        'chunk_index': idx,
                        'total_chunks': len(chunks)
                    }
                })
        
        return chunked_content
    
    @staticmethod
    def chunk_image_content(image_chunks: List[Dict]) -> List[Dict]:
        """Images are already one per chunk, but we add chunk metadata"""
        chunked_content = []
        
        for img_item in image_chunks:
            chunked_content.append({
                'type': 'image',
                'page': img_item['page'],
                'content': img_item['content'],
                'chunk_index': 0,
                'total_chunks': 1,
                'metadata': {
                    **img_item['metadata'],
                    'chunk_index': 0,
                    'total_chunks': 1
                }
            })
        
        return chunked_content
    
    @staticmethod
    def chunk_table_content(table_chunks: List[Dict]) -> List[Dict]:
        """Tables are already one per chunk, but we add chunk metadata"""
        chunked_content = []
        
        for table_item in table_chunks:
            chunked_content.append({
                'type': 'table',
                'page': table_item['page'],
                'content': table_item['content'],
                'dataframe': table_item.get('dataframe', []),
                'chunk_index': 0,
                'total_chunks': 1,
                'metadata': {
                    **table_item['metadata'],
                    'chunk_index': 0,
                    'total_chunks': 1
                }
            })
        
        return chunked_content
    
    @staticmethod
    def detect_sections(text: str) -> List[Dict]:
        """Detect section headings in text using common patterns"""
        sections = []
        # Patterns for section headings: "5.3", "Section 5.3", "5.3.1", etc.
        section_patterns = [
            r'^(\d+\.\d+(?:\.\d+)?)\s+(.+?)(?:\n|$)',  # "5.3 Title"
            r'^Section\s+(\d+\.\d+(?:\.\d+)?)\s*:?\s*(.+?)(?:\n|$)',  # "Section 5.3: Title"
            r'^(\d+)\s+([A-Z][^\n]+?)(?:\n|$)',  # "5 TITLE" (major sections)
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            for pattern in section_patterns:
                match = re.match(pattern, line_stripped, re.IGNORECASE)
                if match:
                    section_num = match.group(1) if len(match.groups()) >= 1 else None
                    section_title = match.group(2) if len(match.groups()) >= 2 else line_stripped
                    sections.append({
                        'number': section_num,
                        'title': section_title.strip(),
                        'line_index': i,
                        'full_match': line_stripped
                    })
                    break
        
        return sections
    
    @staticmethod
    def chunk_by_sections(content: Dict[str, List[Dict]]) -> List[Dict]:
        """Chunk content by sections, keeping related text and tables together
        
        This method groups content by page, detects sections across pages, and creates chunks
        that include both text and tables from the same section, even if they're on different pages.
        """
        # Organize content by page
        page_content = {}
        all_pages = set()
        
        # Group text by page
        for text_item in content['text']:
            page = text_item['page']
            all_pages.add(page)
            if page not in page_content:
                page_content[page] = {'text': [], 'tables': [], 'images': []}
            page_content[page]['text'].append(text_item)
        
        # Group tables by page
        for table_item in content['tables']:
            page = table_item['page']
            all_pages.add(page)
            if page not in page_content:
                page_content[page] = {'text': [], 'tables': [], 'images': []}
            page_content[page]['tables'].append(table_item)
        
        # Group images by page
        for image_item in content['images']:
            page = image_item['page']
            all_pages.add(page)
            if page not in page_content:
                page_content[page] = {'text': [], 'tables': [], 'images': []}
            page_content[page]['images'].append(image_item)
        
        # First pass: detect all sections across all pages and track their page ranges
        section_map = {}  # Maps section number to {'title', 'start_page', 'end_page', 'pages'}
        
        for page in sorted(all_pages):
            page_text = '\n\n'.join([item['content'] for item in page_content[page]['text']])
            sections = Chunker.detect_sections(page_text)
            
            for section in sections:
                section_num = section.get('number', '')
                if section_num:
                    if section_num not in section_map:
                        section_map[section_num] = {
                            'title': section.get('title', ''),
                            'start_page': page,
                            'end_page': page,
                            'pages': [page]
                        }
                    else:
                        # Section continues on this page
                        section_map[section_num]['end_page'] = page
                        if page not in section_map[section_num]['pages']:
                            section_map[section_num]['pages'].append(page)
        
        # Process each page to create section-based chunks
        section_chunks = []
        
        for page in sorted(all_pages):
            page_data = page_content[page]
            
            # Combine all text from this page
            page_text = '\n\n'.join([item['content'] for item in page_data['text']])
            
            # Detect sections in the page text
            sections = Chunker.detect_sections(page_text)
            
            if not sections:
                # No sections detected, chunk normally but attach tables to last chunk
                # Also check if this page might be continuation of a section from previous page
                text_chunks = Chunker.chunk_text(page_text)
                
                # Check if there's a section that spans to this page (from previous page)
                section_tables = []
                for section_num, section_info in section_map.items():
                    if page in section_info['pages'] and page > section_info['start_page']:
                        # This page is part of a section that started earlier
                        # Include tables from this page and next page
                        if page in page_content:
                            section_tables.extend(page_content[page]['tables'])
                        next_page = page + 1
                        if next_page in page_content:
                            section_tables.extend(page_content[next_page]['tables'])
                        break
                
                # If no section continuation, just use tables from this page
                if not section_tables:
                    section_tables = page_data['tables']
                
                # Add each text chunk, attaching tables to the last chunk
                for idx, text_chunk in enumerate(text_chunks):
                    chunk_content = text_chunk
                    
                    # If this is the last chunk and there are tables, include them
                    if idx == len(text_chunks) - 1 and section_tables:
                        table_texts = [f"\n\nTable:\n{t['content']}" for t in section_tables]
                        chunk_content = chunk_content + ''.join(table_texts)
                    
                    section_chunks.append({
                        'type': 'text' if not (idx == len(text_chunks) - 1 and page_data['tables']) else 'mixed',
                        'page': page,
                        'content': chunk_content,
                        'chunk_index': idx,
                        'total_chunks': len(text_chunks),
                        'metadata': {
                            'page_number': page,
                            'chunk_index': idx,
                            'total_chunks': len(text_chunks),
                            'section_based': False,
                            'has_tables': idx == len(text_chunks) - 1 and bool(page_data['tables'])
                        }
                    })
            else:
                # Sections detected - create section-based chunks
                # Split text by sections
                lines = page_text.split('\n')
                current_section = None
                current_section_text = []
                section_start_idx = 0
                
                for i, section in enumerate(sections):
                    section_end_idx = section['line_index']
                    
                    # Process previous section if exists
                    if current_section is not None:
                        section_text = '\n'.join(lines[section_start_idx:section_end_idx])
                        if section_text.strip():
                            # Chunk the section text
                            text_chunks = Chunker.chunk_text(section_text.strip())
                            
                            # Find tables that belong to this section
                            # Look for tables on current page AND next page(s) that belong to this section
                            section_num = current_section.get('number', '')
                            section_tables = []
                            
                            # Get section page range from section_map
                            if section_num in section_map:
                                section_pages = section_map[section_num]['pages']
                                # Look for tables on current page and next page (within section range)
                                for check_page in section_pages:
                                    if check_page in page_content:
                                        section_tables.extend(page_content[check_page]['tables'])
                            else:
                                # Fallback: just tables on current page and next page
                                section_tables = [t for t in page_data['tables'] if t['page'] == page]
                                # Also check next page
                                next_page = page + 1
                                if next_page in page_content:
                                    section_tables.extend(page_content[next_page]['tables'])
                            
                            # Create chunks for this section
                            for idx, text_chunk in enumerate(text_chunks):
                                chunk_content_parts = [text_chunk]
                                
                                # Add section heading
                                if current_section:
                                    chunk_content_parts.insert(0, 
                                        f"Section {current_section.get('number', '')} {current_section.get('title', '')}")
                                
                                # If this is the last text chunk and there are tables, include table info
                                if idx == len(text_chunks) - 1 and section_tables:
                                    for table in section_tables:
                                        chunk_content_parts.append(f"\n\nTable:\n{table['content']}")
                                
                                section_chunks.append({
                                    'type': 'mixed' if section_tables and idx == len(text_chunks) - 1 else 'text',
                                    'page': page,
                                    'content': '\n\n'.join(chunk_content_parts),
                                    'chunk_index': idx,
                                    'total_chunks': len(text_chunks),
                                    'metadata': {
                                        'page_number': page,
                                        'section_number': current_section.get('number'),
                                        'section_title': current_section.get('title'),
                                        'chunk_index': idx,
                                        'total_chunks': len(text_chunks),
                                        'section_based': True
                                    }
                                })
                            
                            # If no text chunks but there are tables, add tables as separate chunks
                            if not text_chunks and section_tables:
                                for table in section_tables:
                                    section_chunks.append({
                                        'type': 'table',
                                        'page': page,
                                        'content': table['content'],
                                        'dataframe': table.get('dataframe', []),
                                        'chunk_index': 0,
                                        'total_chunks': 1,
                                        'metadata': {
                                            **table.get('metadata', {}),
                                            'page_number': page,
                                            'section_number': current_section.get('number'),
                                            'section_title': current_section.get('title'),
                                            'section_based': True
                                        }
                                    })
                    
                    # Start new section
                    current_section = section
                    section_start_idx = section_end_idx
                    current_section_text = []
                
                # Process last section
                if current_section:
                    section_text = '\n'.join(lines[section_start_idx:])
                    if section_text.strip():
                        text_chunks = Chunker.chunk_text(section_text.strip())
                        
                        # Find tables that belong to this section (current page and next page)
                        section_num = current_section.get('number', '')
                        section_tables = []
                        
                        # Get section page range from section_map
                        if section_num in section_map:
                            section_pages = section_map[section_num]['pages']
                            # Look for tables on pages within this section
                            for check_page in section_pages:
                                if check_page in page_content:
                                    section_tables.extend(page_content[check_page]['tables'])
                        else:
                            # Fallback: tables on current page and next page
                            section_tables = [t for t in page_data['tables'] if t['page'] == page]
                            next_page = page + 1
                            if next_page in page_content:
                                section_tables.extend(page_content[next_page]['tables'])
                        
                        for idx, text_chunk in enumerate(text_chunks):
                            chunk_content_parts = [text_chunk]
                            chunk_content_parts.insert(0, 
                                f"Section {current_section.get('number', '')} {current_section.get('title', '')}")
                            
                            if idx == len(text_chunks) - 1 and section_tables:
                                for table in section_tables:
                                    chunk_content_parts.append(f"\n\nTable:\n{table['content']}")
                            
                            section_chunks.append({
                                'type': 'mixed' if section_tables and idx == len(text_chunks) - 1 else 'text',
                                'page': page,
                                'content': '\n\n'.join(chunk_content_parts),
                                'chunk_index': idx,
                                'total_chunks': len(text_chunks),
                                'metadata': {
                                    'page_number': page,
                                    'section_number': current_section.get('number'),
                                    'section_title': current_section.get('title'),
                                    'chunk_index': idx,
                                    'total_chunks': len(text_chunks),
                                    'section_based': True
                                }
                            })
            
            # Add images from this page
            for image_item in page_data['images']:
                section_chunks.append({
                    'type': 'image',
                    'page': page,
                    'content': image_item['content'],
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'metadata': {
                        **image_item.get('metadata', {}),
                        'page_number': page,
                        'section_based': False
                    }
                })
        
        return section_chunks
    
    @staticmethod
    def chunk_all(content: Dict[str, List[Dict]], use_sections: bool = True) -> Dict[str, List[Dict]]:
        """Chunk all content types
        
        Args:
            content: Dictionary with 'text', 'images', 'tables' keys
            use_sections: If True, use section-based chunking to keep related content together
        """
        if use_sections:
            # Use section-based chunking
            section_chunks = Chunker.chunk_by_sections(content)
            
            # Separate by type for return format
            result = {'text': [], 'images': [], 'tables': []}
            for chunk in section_chunks:
                chunk_type = chunk['type']
                if chunk_type in ['text', 'mixed']:
                    result['text'].append(chunk)
                elif chunk_type == 'table':
                    result['tables'].append(chunk)
                elif chunk_type == 'image':
                    result['images'].append(chunk)
            
            return result
        else:
            # Original chunking method
            return {
                'text': Chunker.chunk_text_content(content['text']),
                'images': Chunker.chunk_image_content(content['images']),
                'tables': Chunker.chunk_table_content(content['tables'])
            }

