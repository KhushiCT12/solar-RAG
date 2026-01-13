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
            # Give more characters to tables since they contain structured data
            context_parts = []
            for item in context:
                content_type = item.get('metadata', {}).get('type', 'unknown')
                doc_name = item.get('metadata', {}).get('document_name', 'Unknown')
                page = item.get('metadata', {}).get('page', 'N/A')
                content = item.get('content', '')
                
                # Allocate more characters for tables (they need full data)
                if content_type == 'table':
                    # Tables can be long, allow up to 3000 characters
                    content_snippet = content[:3000] if len(content) > 3000 else content
                    if len(content) > 3000:
                        content_snippet += "\n[... table continues ...]"
                elif content_type == 'text':
                    # Text chunks get 1500 characters
                    content_snippet = content[:1500] if len(content) > 1500 else content
                else:
                    # Images and others get 500 characters
                    content_snippet = content[:500] if len(content) > 500 else content
                
                context_parts.append(
                    f"[Document: {doc_name} | {content_type.upper()} - Page {page}]:\n{content_snippet}"
                )
            
            context_text = "\n\n".join(context_parts)
            
            # Check if we have tables in the context
            has_tables = any(item.get('metadata', {}).get('type') == 'table' for item in context)
            table_note = "\n\nNote: Some context includes TABLE data. Please carefully analyze table content including all rows, columns, and values when answering the question." if has_tables else ""
            
            prompt = f"""Based on the following context from a solar energy storage project report, please answer the question. If the answer is not in the context, say so.

When analyzing tables, examine all rows and columns carefully. Extract specific values, numbers, and relationships from the table data.

Context:
{context_text}{table_note}

Question: {question}

Answer:"""
            
            response = self.client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided context. Be accurate and do not cite page numbers."
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

