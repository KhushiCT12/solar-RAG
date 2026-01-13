"""
Vector Store Module
Manages ChromaDB for storing and retrieving embeddings with indexing
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME, TOP_K_RESULTS
import uuid
import os
import shutil


class VectorStore:
    """Manage vector database operations with ChromaDB"""
    
    def __init__(self, db_path: str = CHROMA_DB_PATH, collection_name: str = CHROMA_COLLECTION_NAME):
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with error handling for corruption
        try:
            self.client = chromadb.PersistentClient(path=db_path)
        except Exception as e:
            # If database is corrupted, reset it
            if "compaction" in str(e).lower() or "metadata" in str(e).lower():
                print(f"⚠️ ChromaDB corruption detected. Resetting database...")
                self._reset_database()
                self.client = chromadb.PersistentClient(path=db_path)
            else:
                raise
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except Exception as e:
            error_str = str(e).lower()
            # If collection access fails due to corruption or schema mismatch, reset and recreate
            if "compaction" in error_str or "metadata" in error_str or "no such column" in error_str or "topic" in error_str:
                print(f"⚠️ Database schema incompatibility detected. Resetting database...")
                print(f"   (This will clear existing data. If you need to preserve it, backup chroma_db/ first)")
                self._reset_database()
                self.client = chromadb.PersistentClient(path=db_path)
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
                )
                print(f"Created new collection: {collection_name}")
            else:
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
        
        # Add to collection with error handling for corruption
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Added {len(chunks)} chunks to vector store")
        except Exception as e:
            # If corruption detected during write, reset and retry once
            if "compaction" in str(e).lower() or "metadata" in str(e).lower():
                print(f"⚠️ Corruption detected during write. Resetting database and retrying...")
                self._reset_database()
                self.client = chromadb.PersistentClient(path=self.db_path)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
                )
                # Retry the add operation
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"Added {len(chunks)} chunks to vector store (after reset)")
            else:
                raise
    
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
    
    def _reset_database(self):
        """Reset the entire ChromaDB database by deleting and recreating the directory"""
        try:
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
                print(f"Deleted corrupted database at: {self.db_path}")
        except Exception as e:
            print(f"Error resetting database: {e}")
            raise
    
    def clear_collection(self):
        """Clear all data from the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
        except:
            # If deletion fails, reset the entire database
            self._reset_database()
            self.client = chromadb.PersistentClient(path=self.db_path)
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
        )
        print(f"Cleared collection: {self.collection_name}")
    
    def reset_database(self):
        """Public method to reset the entire database (for recovery from corruption)"""
        self._reset_database()
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "RAG system for Radar Solar Energy Storage Report"}
        )
        print(f"Database reset complete. New collection created: {self.collection_name}")
