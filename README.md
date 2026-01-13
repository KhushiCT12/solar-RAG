# Radar Solar RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system for querying the Desktop Due Diligence Report for the Radar Solar + Energy Storage Project.

## Features

- ✅ **Separate Chunking**: Text, images, and tables are processed separately
- ✅ **AI Summarization**: Each chunk gets an AI-generated summary using Perplexity Sonar Pro
- ✅ **Separate Embeddings**: Different embedding vectors for each content type
- ✅ **Vector Database**: ChromaDB for efficient similarity search with indexing
- ✅ **LLM Querying**: Perplexity Sonar Pro for generating answers
- ✅ **Beautiful UI**: Streamlit interface for easy querying

## Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd SAR
```

### 2. Create Virtual Environment

```bash
python3 -m venv .raaag
source .raaag/bin/activate  # On Windows: .raaag\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

1. Copy the example config file:
   ```bash
   cp config.example.py config.py
   ```

2. Edit `config.py` and add your Perplexity API key:
   ```python
   PERPLEXITY_API_KEY = "your-perplexity-api-key-here"
   ```

   The system uses the `sonar-pro` model by default.

### 4. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

1. **Upload PDF**: Use the sidebar to upload the PDF document (or use the default one if available)
2. **Process PDF**: Click "Process PDF & Build Knowledge Base" to extract and index all content
3. **Query**: Ask questions about the document and get AI-generated answers with source citations

## Project Structure

```
SAR/
├── app.py                 # Streamlit UI
├── config.py              # Configuration settings
├── pdf_processor.py       # PDF extraction (text, images, tables)
├── chunker.py             # Chunking logic
├── perplexity_client.py   # Perplexity API integration
├── embeddings.py          # Embedding generation
├── vector_store.py        # ChromaDB management
├── rag_system.py          # Main RAG orchestration
├── requirements.txt        # Python dependencies
└── README.md             # This file
```

## Components

### PDF Processor
Extracts text, images, and tables separately from PDF documents using `pdfplumber` and `PyMuPDF`.

### Chunker
Implements separate chunking strategies for:
- **Text**: Sentence-based chunking with overlap
- **Images**: One image per chunk
- **Tables**: One table per chunk

### Perplexity Client
- Generates AI summaries for each chunk
- Handles querying with context from retrieved chunks

### Embedding Generator
Creates embeddings using Sentence Transformers:
- Text embeddings from content
- Image embeddings from metadata descriptions
- Table embeddings from table content

### Vector Store
Manages ChromaDB:
- Stores chunks with embeddings and metadata
- Performs similarity search
- Maintains indexes for efficient retrieval

## Notes

- The system processes PDFs and creates a persistent vector database
- First-time processing may take several minutes depending on PDF size
- All embeddings and summaries are cached in ChromaDB for fast subsequent queries

## Troubleshooting

If you encounter disk space issues during installation:
1. Free up disk space
2. Install packages one by one if needed
3. Consider using a smaller embedding model

For any issues, check:
- PDF file is accessible
- Perplexity API key is valid
- Sufficient disk space for ChromaDB

