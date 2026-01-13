"""
Main RAG System
Orchestrates the entire RAG pipeline
"""
from pdf_processor import PDFProcessor
from excel_processor import ExcelProcessor
from chunker import Chunker
from perplexity_client import PerplexityClient
from embeddings import EmbeddingGenerator
from vector_store import VectorStore
from config import PDF_PATH
from typing import List, Dict
import os


class RAGSystem:
    """Main RAG system that coordinates all components"""
    
    def __init__(self):
        self.pdf_processor = None
        self.excel_processor = None
        self.chunker = Chunker()
        self.perplexity_client = PerplexityClient()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
    
    def process_document(self, file_path: str, clear_existing: bool = False):
        """Process a document (PDF, Excel, etc.) and add to knowledge base
        
        Args:
            file_path: Path to the document file
            clear_existing: If True, clears existing data before processing. If False, adds to existing data.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get document info
        document_name = os.path.basename(file_path)
        document_type = os.path.splitext(document_name)[1].lower()
        
        print(f"Processing document: {document_name} ({document_type})")
        
        # Clear existing data if requested
        if clear_existing:
            print("Clearing existing data...")
            self.vector_store.clear_collection()
        
        # Step 1: Extract content based on file type
        print("Step 1: Extracting content...")
        if document_type == '.pdf':
            self.pdf_processor = PDFProcessor(file_path)
            content = self.pdf_processor.extract_all()
        elif document_type in ['.xlsx', '.xls']:
            self.excel_processor = ExcelProcessor(file_path)
            content = self.excel_processor.extract_all()
        else:
            raise ValueError(f"Unsupported file type: {document_type}. Supported: .pdf, .xlsx, .xls")
        
        print(f"  - Extracted {len(content['text'])} text chunks")
        print(f"  - Extracted {len(content['images'])} images")
        print(f"  - Extracted {len(content['tables'])} tables")
        
        # Step 2: Chunk the content
        print("\nStep 2: Chunking content...")
        chunked_content = self.chunker.chunk_all(content)
        
        total_chunks = (
            len(chunked_content['text']) + 
            len(chunked_content['images']) + 
            len(chunked_content['tables'])
        )
        print(f"  - Created {total_chunks} total chunks")
        print(f"    - {len(chunked_content['text'])} text chunks")
        print(f"    - {len(chunked_content['images'])} image chunks")
        print(f"    - {len(chunked_content['tables'])} table chunks")
        
        # Add document metadata to all chunks
        for chunk_type in ['text', 'images', 'tables']:
            for chunk in chunked_content[chunk_type]:
                chunk['metadata'] = chunk.get('metadata', {})
                chunk['metadata']['document_name'] = document_name
                chunk['metadata']['document_type'] = document_type
                chunk['metadata']['document_path'] = file_path
        
        # Step 3: Generate embeddings
        print("\nStep 3: Generating embeddings...")
        all_chunks = (
            chunked_content['text'] + 
            chunked_content['images'] + 
            chunked_content['tables']
        )
        
        embedded_chunks = self.embedding_generator.generate_embeddings_for_chunks(all_chunks)
        print(f"  - Generated {len(embedded_chunks)} embeddings")
        
        # Step 4: Store in vector database (additive - doesn't clear existing)
        print("\nStep 4: Storing in vector database...")
        self.vector_store.add_chunks(embedded_chunks)
        print("  - All chunks stored successfully")
        
        # Close processors
        if self.pdf_processor:
            self.pdf_processor.close()
        if self.excel_processor:
            pass  # Excel processor doesn't need closing
        
        print(f"\n✅ Document processing complete! ({document_name})")
        return self.vector_store.get_collection_info()
    
    def process_pdf(self, pdf_path: str = PDF_PATH, clear_existing: bool = False):
        """Process PDF and build the knowledge base (backward compatibility)"""
        return self.process_document(pdf_path, clear_existing)
    
    def query(self, question: str, top_k: int = 5) -> Dict:
        """Query the RAG system"""
        print(f"\nQuerying: {question}")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_text_embedding(question)
        query_embedding_list = query_embedding.tolist()
        
        # Search vector store
        results = self.vector_store.search(query_embedding_list, top_k=top_k)
        
        print(f"Found {len(results)} relevant chunks")
        
        # Generate answer using Perplexity
        answer = self.perplexity_client.query(question, results)
        
        return {
            'question': question,
            'answer': answer,
            'sources': results,
            'num_sources': len(results)
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base"""
        return self.vector_store.get_collection_info()
    
    def is_ready(self) -> bool:
        """Check if the RAG system has data loaded"""
        return self.vector_store.has_data()

