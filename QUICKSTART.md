# Quick Start Guide

## Installation (When Disk Space is Available)

1. **Activate the virtual environment:**
   ```bash
   source .raaag/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   Note: If you encounter disk space issues, you can install packages incrementally:
   ```bash
   pip install streamlit chromadb pdfplumber pillow openai httpx python-dotenv numpy pandas sentence-transformers pymupdf pdf2image
   ```

## Running the Application

### Option 1: Using the run script
```bash
./run.sh
```

### Option 2: Manual
```bash
source .raaag/bin/activate
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## First-Time Setup

1. **Upload PDF**: 
   - Use the sidebar to upload `251001- FULL DDR_RADAR_SOLAR_ENERGY STORAGE_EXT_V0.pdf`
   - Or place it in the project root directory

2. **Process PDF**:
   - Click "🔄 Process PDF & Build Knowledge Base" in the sidebar
   - This will:
     - Extract text, images, and tables
     - Chunk the content
     - Generate AI summaries using Perplexity
     - Create embeddings
     - Store in ChromaDB
   - This process may take 5-15 minutes depending on PDF size

3. **Start Querying**:
   - Once processed, enter questions in the main interface
   - View answers with source citations

## Example Queries

- "What is the project capacity and location?"
- "What are the environmental concerns mentioned in the report?"
- "What is the interconnection status?"
- "What are the financial incentives available?"
- "What is the expected energy yield?"
- "What are the risks and constraints identified?"

## Troubleshooting

### Disk Space Issues
- Free up disk space before installing packages
- Consider using a smaller embedding model in `config.py`

### PDF Not Found
- Ensure the PDF file exists in the project directory
- Or upload it through the Streamlit UI

### API Errors
- Verify the Perplexity API key in `config.py`
- Check your internet connection
- Ensure you have API credits available

### Import Errors
- Make sure all packages are installed: `pip install -r requirements.txt`
- Activate the virtual environment: `source .raaag/bin/activate`

## Project Structure

```
SAR/
├── app.py                 # Streamlit UI (Main entry point)
├── config.py              # Configuration (API keys, paths, etc.)
├── pdf_processor.py       # PDF extraction
├── chunker.py             # Content chunking
├── perplexity_client.py   # Perplexity API integration
├── embeddings.py          # Embedding generation
├── vector_store.py        # ChromaDB management
├── rag_system.py          # Main RAG orchestration
├── requirements.txt       # Dependencies
├── run.sh                 # Quick run script
├── README.md             # Full documentation
└── QUICKSTART.md         # This file
```

## Next Steps

After successful installation and first run:
- The ChromaDB will persist, so you only need to process the PDF once
- Subsequent queries will be fast
- You can add more PDFs by processing them separately

