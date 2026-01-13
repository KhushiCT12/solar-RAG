"""
Embedding Generation Module
Creates separate embeddings for text, images, and tables
"""
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import numpy as np
from config import EMBEDDING_MODEL


class EmbeddingGenerator:
    """Generate embeddings for different content types"""
    
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Embedding model loaded successfully")
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text content"""
        return self.model.encode(text, convert_to_numpy=True)
    
    def generate_image_embedding(self, image_content: str, metadata: Dict) -> np.ndarray:
        """Generate embedding for image content
        For images, we use the metadata description or a placeholder text
        """
        # Create a text description from image metadata
        description = f"Image from page {metadata.get('page_number', 'N/A')}, format: {metadata.get('format', 'unknown')}"
        return self.model.encode(description, convert_to_numpy=True)
    
    def generate_table_embedding(self, table_content: str) -> np.ndarray:
        """Generate embedding for table content"""
        return self.model.encode(table_content, convert_to_numpy=True)
    
    def generate_embeddings_for_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for a list of chunks"""
        embedded_chunks = []
        
        for chunk in chunks:
            content_type = chunk['type']
            content = chunk['content']
            metadata = chunk.get('metadata', {})
            
            if content_type == 'text':
                embedding = self.generate_text_embedding(content)
            elif content_type == 'image':
                embedding = self.generate_image_embedding(content, metadata)
            elif content_type == 'table':
                embedding = self.generate_table_embedding(content)
            else:
                # Default to text embedding
                embedding = self.generate_text_embedding(str(content))
            
            embedded_chunk = {
                **chunk,
                'embedding': embedding.tolist()  # Convert numpy array to list for JSON serialization
            }
            embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks

