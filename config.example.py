"""
Configuration file for the RAG system
Example configuration - copy this to config.py and add your API keys
"""
import os

# Perplexity API Configuration
PERPLEXITY_API_KEY = "your-perplexity-api-key-here"
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

# ChromaDB Configuration
CHROMA_DB_PATH = "./chroma_db"
CHROMA_COLLECTION_NAME = "radar_solar_report"

# PDF Configuration
PDF_PATH = "251001- FULL DDR_RADAR_SOLAR_ENERGY STORAGE_EXT_V0.pdf"

# Chunking Configuration
TEXT_CHUNK_SIZE = 1000
TEXT_CHUNK_OVERLAP = 200
IMAGE_CHUNK_SIZE = 1  # One image per chunk
TABLE_CHUNK_SIZE = 1  # One table per chunk

# Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Retrieval Configuration
TOP_K_RESULTS = 5

# Summarization Configuration
SUMMARY_PROMPT = """Please provide a concise summary of the following content. Focus on key facts, numbers, and important information:

{content}

Summary:"""

