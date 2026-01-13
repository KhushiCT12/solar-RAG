"""
Chunking Visualization Page
Shows all chunks with colored boxes (green for text, purple for tables, red for images)
"""
import streamlit as st
from vector_store import VectorStore
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

st.set_page_config(
    page_title="Chunking Visualization - CIR RAG System",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for colored boxes
st.markdown("""
    <style>
    .text-chunk-box {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .table-chunk-box {
        background-color: #e2d9f3;
        border: 2px solid #6f42c1;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .image-chunk-box {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .chunk-header {
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 8px;
        color: #333;
    }
    .chunk-content {
        color: #555;
        font-size: 0.95em;
        line-height: 1.5;
    }
    .chunk-meta {
        color: #777;
        font-size: 0.85em;
        margin-top: 8px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Chunking Visualization")
st.markdown("View how your PDF has been chunked into text, tables, and images")

# Initialize vector store
vector_store = VectorStore(db_path=CHROMA_DB_PATH, collection_name=CHROMA_COLLECTION_NAME)

# Check if data exists
if not vector_store.has_data():
    st.warning("⚠️ No data found. Please process a PDF first from the main page.")
    st.stop()

# Get all chunks
chunks_by_type = vector_store.get_all_chunks_by_type()

total_text = len(chunks_by_type['text'])
total_tables = len(chunks_by_type['table'])
total_images = len(chunks_by_type['image'])
total_chunks = total_text + total_tables + total_images

# Summary metrics
st.markdown("### Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Chunks", total_chunks)
with col2:
    st.metric("📝 Text Chunks", total_text, help="Green boxes")
with col3:
    st.metric("📊 Table Chunks", total_tables, help="Purple boxes")
with col4:
    st.metric("🖼️ Image Chunks", total_images, help="Red boxes")

st.divider()

# Create tabs for each chunk type
tab1, tab2, tab3 = st.tabs([
    f"📝 Text Chunks ({total_text})",
    f"📊 Table Chunks ({total_tables})",
    f"🖼️ Image Chunks ({total_images})"
])

# Text Chunks Tab
with tab1:
    if total_text > 0:
        st.markdown(f"### Showing {total_text} Text Chunks")
        for i, chunk in enumerate(chunks_by_type['text'], 1):
            page = chunk['metadata'].get('page', 'N/A')
            chunk_index = chunk['metadata'].get('chunk_index', 0)
            total_chunks_page = chunk['metadata'].get('total_chunks', 1)
            content = chunk['content']
            
            # Truncate very long content for display
            display_content = content[:500] + "..." if len(content) > 500 else content
            
            st.markdown(
                f"""
                <div class="text-chunk-box">
                    <div class="chunk-header">📝 Text Chunk #{i} - Page {page}</div>
                    <div class="chunk-content">{display_content}</div>
                    <div class="chunk-meta">Chunk {chunk_index + 1} of {total_chunks_page} on this page</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Show full content in expander if truncated
            if len(content) > 500:
                with st.expander(f"View full content of Text Chunk #{i}"):
                    st.text(content)
    else:
        st.info("No text chunks found.")

# Table Chunks Tab
with tab2:
    if total_tables > 0:
        st.markdown(f"### Showing {total_tables} Table Chunks")
        for i, chunk in enumerate(chunks_by_type['table'], 1):
            page = chunk['metadata'].get('page', 'N/A')
            table_index = chunk['metadata'].get('table_index', 0)
            rows = chunk['metadata'].get('rows', 0)
            columns = chunk['metadata'].get('columns', 0)
            content = chunk['content']
            
            # Truncate very long content for display
            display_content = content[:800] + "..." if len(content) > 800 else content
            
            st.markdown(
                f"""
                <div class="table-chunk-box">
                    <div class="chunk-header">📊 Table Chunk #{i} - Page {page}</div>
                    <div class="chunk-content"><pre style="white-space: pre-wrap; font-family: monospace; background: transparent; border: none; padding: 0;">{display_content}</pre></div>
                    <div class="chunk-meta">Table #{table_index + 1} | {rows} rows × {columns} columns</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Show full content in expander if truncated
            if len(content) > 800:
                with st.expander(f"View full content of Table Chunk #{i}"):
                    st.text(content)
    else:
        st.info("No table chunks found.")

# Image Chunks Tab
with tab3:
    if total_images > 0:
        st.markdown(f"### Showing {total_images} Image Chunks")
        for i, chunk in enumerate(chunks_by_type['image'], 1):
            page = chunk['metadata'].get('page', 'N/A')
            img_index = chunk['metadata'].get('image_index', 'N/A')
            img_format = chunk['metadata'].get('format', 'N/A')
            width = chunk['metadata'].get('width', 0)
            height = chunk['metadata'].get('height', 0)
            
            st.markdown(
                f"""
                <div class="image-chunk-box">
                    <div class="chunk-header">🖼️ Image Chunk #{i} - Page {page}</div>
                    <div class="chunk-content">Image #{img_index + 1} on page {page}</div>
                    <div class="chunk-meta">Format: {img_format} | Dimensions: {width} × {height} pixels</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No image chunks found.")

