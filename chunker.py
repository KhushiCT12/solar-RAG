"""
Chunking Module
Separate chunking logic for text, images, and tables
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
    def chunk_all(content: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Chunk all content types"""
        return {
            'text': Chunker.chunk_text_content(content['text']),
            'images': Chunker.chunk_image_content(content['images']),
            'tables': Chunker.chunk_table_content(content['tables'])
        }

