"""
Perplexity API Client
Handles summarization and querying using Perplexity Sonar Pro
"""
import httpx
from typing import Dict, List, Optional
from config import PERPLEXITY_API_KEY, PERPLEXITY_MODEL, PERPLEXITY_BASE_URL, SUMMARY_PROMPT


class PerplexityClient:
    """Client for interacting with Perplexity API"""
    
    def __init__(self, api_key: str = PERPLEXITY_API_KEY, model: str = PERPLEXITY_MODEL):
        self.api_key = api_key
        self.model = model
        self.base_url = PERPLEXITY_BASE_URL
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0
        )
    
    def summarize(self, content: str, content_type: str = "text") -> str:
        """Generate AI summary for a chunk using Perplexity"""
        try:
            prompt = SUMMARY_PROMPT.format(content=content[:2000])  # Limit content length
            
            if content_type == "image":
                prompt = f"Please provide a concise description of what this image contains. Focus on key visual elements, text visible in the image, and important details:\n\n{content[:500]}"
            elif content_type == "table":
                prompt = f"Please provide a concise summary of this table data. Focus on key numbers, trends, and important information:\n\n{content[:2000]}"
            
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that provides concise, accurate summaries."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Summary unavailable: {str(e)}"
    
    def query(self, question: str, context: List[Dict]) -> str:
        """Query the RAG system using Perplexity with retrieved context"""
        try:
            # Format context for the prompt
            context_text = "\n\n".join([
                f"[Document: {item.get('metadata', {}).get('document_name', 'Unknown')} | {item.get('metadata', {}).get('type', 'unknown').upper()} - Page {item.get('metadata', {}).get('page', 'N/A')}]:\n{item.get('content', '')[:500]}"
                for item in context
            ])
            
            prompt = f"""Based on the following context from a solar energy storage project report, please answer the question. If the answer is not in the context, say so.

Context:
{context_text}

Question: {question}

Answer:"""
            
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided context. Be accurate and cite page numbers when possible."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1000
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"Error querying: {e}")
            return f"Error generating response: {str(e)}"
    
    def close(self):
        """Close the HTTP client"""
        if self.client:
            self.client.close()

