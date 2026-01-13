"""
Vector Store Module
Manages ChromaDB for storing and retrieving embeddings with indexing
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, TOP_K_RESULTS
import uuid


class VectorStore:
    """Manage vector database operations with ChromaDB"""
    
    def __init__(self, db_path: str = CHROMA_DB_PATH, collection_name: str = CHROMA_COLLECTION_NAME):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
            )
            print(f"Created new collection: {collection_name}")
    
    def add_chunks(self, chunks: List[Dict]):
        """Add chunks with embeddings to the vector store"""
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            embeddings.append(chunk['embedding'])
            
            # Store content as document
            content = chunk['content']
            if len(content) > 10000:  # ChromaDB has limits
                content = content[:10000]
            documents.append(content)
            
            # Store metadata
            metadata = {
                'type': chunk['type'],
                'page': chunk.get('page', 0),
                'chunk_index': chunk.get('chunk_index', 0),
                'total_chunks': chunk.get('total_chunks', 1),
                **chunk.get('metadata', {})
            }
            metadatas.append(metadata)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Added {len(chunks)} chunks to vector store")
    
    def search(self, query_embedding: List[float], top_k: int = TOP_K_RESULTS, 
               content_type: Optional[str] = None) -> List[Dict]:
        """Search for similar chunks"""
        where_clause = {}
        if content_type:
            where_clause['type'] = content_type
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results
    
    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'total_chunks': count,
            'db_path': self.db_path
        }
    
    def has_data(self) -> bool:
        """Check if the collection has any data"""
        try:
            count = self.collection.count()
            return count > 0
        except:
            return False
    
    def get_all_chunks_by_type(self) -> Dict[str, List[Dict]]:
        """Get all chunks grouped by type"""
        try:
            # Get all chunks from the collection
            results = self.collection.get()
            
            chunks_by_type = {
                'text': [],
                'table': [],
                'image': []
            }
            
            if results['ids']:
                for i in range(len(results['ids'])):
                    chunk = {
                        'id': results['ids'][i],
                        'content': results['documents'][i] if 'documents' in results else '',
                        'metadata': results['metadatas'][i] if 'metadatas' in results else {}
                    }
                    chunk_type = chunk['metadata'].get('type', 'text').lower()
                    if chunk_type in chunks_by_type:
                        chunks_by_type[chunk_type].append(chunk)
            
            return chunks_by_type
        except Exception as e:
            print(f"Error getting chunks by type: {e}")
            return {'text': [], 'table': [], 'image': []}
    
    def get_all_chunks_by_page(self) -> Dict[int, List[Dict]]:
        """Get all chunks grouped by page number"""
        try:
            # Get all chunks from the collection
            results = self.collection.get()
            
            chunks_by_page = {}
            
            if results['ids']:
                for i in range(len(results['ids'])):
                    chunk = {
                        'id': results['ids'][i],
                        'content': results['documents'][i] if 'documents' in results else '',
                        'metadata': results['metadatas'][i] if 'metadatas' in results else {}
                    }
                    page = chunk['metadata'].get('page', 0)
                    if page not in chunks_by_page:
                        chunks_by_page[page] = []
                    chunks_by_page[page].append(chunk)
            
            # Sort chunks within each page by type and chunk index
            for page in chunks_by_page:
                chunks_by_page[page].sort(key=lambda x: (
                    x['metadata'].get('type', 'text'),
                    x['metadata'].get('chunk_index', 0)
                ))
            
            return chunks_by_page
        except Exception as e:
            print(f"Error getting chunks by page: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all data from the collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
        )
        print(f"Cleared collection: {self.collection_name}")

