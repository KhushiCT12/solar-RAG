"""
Main RAG System
Orchestrates the entire RAG pipeline
"""
from pdf_processor import PDFProcessor
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
        self.chunker = Chunker()
        self.perplexity_client = PerplexityClient()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
    
    def process_pdf(self, pdf_path: str = PDF_PATH):
        """Process PDF and build the knowledge base"""
        print(f"Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Step 1: Extract content from PDF
        print("Step 1: Extracting content from PDF...")
        self.pdf_processor = PDFProcessor(pdf_path)
        content = self.pdf_processor.extract_all()
        
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
        
        # Step 3: Generate summaries using Perplexity
        print("\nStep 3: Generating AI summaries...")
        all_chunks = (
            chunked_content['text'] + 
            chunked_content['images'] + 
            chunked_content['tables']
        )
        
        for i, chunk in enumerate(all_chunks):
            if i % 10 == 0:
                print(f"  - Processing chunk {i+1}/{total_chunks}...")
            
            # Generate summary
            summary = self.perplexity_client.summarize(
                chunk['content'], 
                chunk['type']
            )
            chunk['summary'] = summary
        
        print("  - All summaries generated")
        
        # Step 4: Generate embeddings
        print("\nStep 4: Generating embeddings...")
        embedded_chunks = self.embedding_generator.generate_embeddings_for_chunks(all_chunks)
        print(f"  - Generated {len(embedded_chunks)} embeddings")
        
        # Step 5: Store in vector database
        print("\nStep 5: Storing in vector database...")
        self.vector_store.add_chunks(embedded_chunks)
        print("  - All chunks stored successfully")
        
        # Close PDF processor
        if self.pdf_processor:
            self.pdf_processor.close()
        
        print("\n✅ PDF processing complete!")
        return self.vector_store.get_collection_info()
    
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

