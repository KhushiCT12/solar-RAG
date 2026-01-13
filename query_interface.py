"""
Interactive Query Interface for RAG System
"""

import os
import sys
from rag_system import RAGSystem
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()


class QueryInterface:
    """Interactive interface for querying the RAG system"""
    
    def __init__(self, pdf_path: str, vector_store_path: str = "./vector_store"):
        """
        Initialize query interface
        
        Args:
            pdf_path: Path to the PDF file
            vector_store_path: Path to the vector store
        """
        self.rag = RAGSystem(pdf_path=pdf_path, vector_store_path=vector_store_path)
        
        # Try to load existing vector store
        try:
            self.rag.load_existing_vector_store()
        except FileNotFoundError:
            print("Vector store not found. Processing PDF first...")
            self.rag.process_pdf()
        
        # Initialize LLM
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.llm = ChatOpenAI(
            model_name="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=api_key
        )
        
        # Create QA chain
        self.qa_chain = self._create_qa_chain()
    
    def _create_qa_chain(self) -> RetrievalQA:
        """Create a QA chain with custom prompt"""
        prompt_template = """Use the following pieces of context from a solar energy project due diligence report to answer the question. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.rag.vector_store.as_retriever(
                search_kwargs={"k": 4}
            ),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
        
        return qa_chain
    
    def query(self, question: str) -> dict:
        """
        Query the RAG system with a question
        
        Args:
            question: User's question
        
        Returns:
            Dictionary with answer and source documents
        """
        result = self.qa_chain({"query": question})
        return result
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("\n" + "="*60)
        print("RAG Query Interface - Radar Solar Energy Storage Report")
        print("="*60)
        print("Type your questions about the report. Type 'quit' or 'exit' to stop.")
        print("="*60 + "\n")
        
        while True:
            question = input("Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            try:
                result = self.query(question)
                
                print("\n" + "-"*60)
                print("Answer:")
                print("-"*60)
                print(result['result'])
                
                print("\n" + "-"*60)
                print("Sources:")
                print("-"*60)
                for i, doc in enumerate(result['source_documents'], 1):
                    page = doc.metadata.get('page', 'N/A')
                    content_preview = doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                    print(f"\n[{i}] Page {page}:")
                    print(f"    {content_preview}")
                
                print("\n" + "="*60 + "\n")
                
            except Exception as e:
                print(f"Error: {str(e)}\n")


if __name__ == "__main__":
    pdf_file = "251001- FULL DDR_RADAR_SOLAR_ENERGY STORAGE_EXT_V0.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"Error: PDF file '{pdf_file}' not found in current directory.")
        print("Please ensure the PDF file is in the same directory as this script.")
        sys.exit(1)
    
    interface = QueryInterface(pdf_path=pdf_file)
    interface.interactive_mode()

