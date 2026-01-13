# Setup Instructions - Disk Space Issue

## Current Status
Your disk is **100% full** (only 237MB free), which prevents package installation.

## Solution Steps

### 1. Free Up Disk Space
You need at least **2-3 GB** of free space to install all packages. Here are some options:

**Quick cleanup:**
```bash
# Check disk usage
du -sh ~/Library/Caches/*
du -sh ~/.cache/*

# Clean Python cache
find ~ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~ -name "*.pyc" -delete 2>/dev/null

# Clean pip cache
pip cache purge

# Clean system caches (macOS)
sudo rm -rf ~/Library/Caches/*
```

**More aggressive cleanup:**
- Empty Trash
- Delete old downloads
- Remove unused applications
- Clear browser caches
- Remove old Docker images/containers if installed

### 2. Install Packages (After Freeing Space)

Once you have at least 2-3 GB free:

```bash
# Activate virtual environment
source .raaag/bin/activate

# Install packages
pip install -r requirements.txt
```

If you still encounter issues, install in smaller batches:

```bash
# Core packages first
pip install streamlit chromadb pdfplumber pillow

# Then API and utilities
pip install openai httpx python-dotenv

# Then data processing
pip install numpy pandas

# Finally ML models (largest)
pip install sentence-transformers pymupdf
```

### 3. Run the Application

```bash
source .raaag/bin/activate
streamlit run app.py
```

Or use the run script:
```bash
./run.sh
```

## Alternative: Use System Python (Not Recommended)

If you have streamlit installed system-wide, you can try:

```bash
# Check if streamlit is available
which streamlit
streamlit --version

# If available, run directly (but this won't use venv packages)
streamlit run app.py
```

However, you'll still need to install other packages (chromadb, pdfplumber, etc.) which requires disk space.

## Minimum Disk Space Required

- **Streamlit**: ~50 MB
- **ChromaDB**: ~100 MB
- **PDF libraries**: ~50 MB
- **Sentence Transformers**: ~500 MB (model downloads)
- **PyTorch**: ~1-2 GB (if not using CPU-only)
- **Other dependencies**: ~200 MB

**Total: ~2-3 GB minimum**

## Check Current Space

```bash
df -h .
du -sh .raaag/
```

## After Installation

Once packages are installed, the application will:
1. Process your PDF (one-time, takes 5-15 minutes)
2. Store data in ChromaDB (persistent)
3. Allow fast querying afterward

The ChromaDB will be stored in `./chroma_db/` directory.

