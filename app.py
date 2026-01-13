"""
Streamlit UI for the RAG System
Beautiful interface for querying documents using CIR RAG System
"""
import streamlit as st
import os
from rag_system import RAGSystem
from config import PDF_PATH
import time


# Page configuration
st.set_page_config(
    page_title="CIR RAG System",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1565a0;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Auto-load RAG system if data exists
if st.session_state.rag_system is None:
    try:
        temp_rag = RAGSystem()
        if temp_rag.is_ready():
            st.session_state.rag_system = temp_rag
            st.session_state.processed = True
    except Exception as e:
        # If there's an error, we'll handle it in the UI
        pass

# Header
st.markdown('<h1 class="main-header">☀️ CIR RAG System</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Retrieval-Augmented Generation System for Document Querying</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Chunking Visualization Tab
    st.subheader("📊 Chunking Visualization")
    
    # Check if we have data to visualize
    if st.session_state.rag_system and st.session_state.rag_system.is_ready():
        try:
            chunks_by_type = st.session_state.rag_system.vector_store.get_all_chunks_by_type()
            
            # Summary
            total_text = len(chunks_by_type['text'])
            total_tables = len(chunks_by_type['table'])
            total_images = len(chunks_by_type['image'])
            total_chunks = total_text + total_tables + total_images
            
            if total_chunks > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Text", total_text, delta=None)
                with col2:
                    st.metric("Tables", total_tables, delta=None)
                with col3:
                    st.metric("Images", total_images, delta=None)
                
                # Show chunking visualization
                with st.expander("📄 View Chunking Details", expanded=False):
                    # Text chunks in green boxes
                    if total_text > 0:
                        st.markdown("### 📝 Text Chunks")
                        for i, chunk in enumerate(chunks_by_type['text'][:10]):  # Show first 10
                            page = chunk['metadata'].get('page', 'N/A')
                            content_preview = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                            st.markdown(
                                f"""
                                <div style="background-color: #d4edda; border: 2px solid #28a745; border-radius: 5px; padding: 10px; margin: 5px 0;">
                                    <strong>Text Chunk #{i+1}</strong> - Page {page}<br>
                                    <small>{content_preview}</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        if total_text > 10:
                            st.caption(f"... and {total_text - 10} more text chunks")
                    
                    # Table chunks in purple boxes
                    if total_tables > 0:
                        st.markdown("### 📊 Table Chunks")
                        for i, chunk in enumerate(chunks_by_type['table'][:10]):  # Show first 10
                            page = chunk['metadata'].get('page', 'N/A')
                            content_preview = chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
                            st.markdown(
                                f"""
                                <div style="background-color: #e2d9f3; border: 2px solid #6f42c1; border-radius: 5px; padding: 10px; margin: 5px 0;">
                                    <strong>Table Chunk #{i+1}</strong> - Page {page}<br>
                                    <small><pre style="white-space: pre-wrap; font-size: 0.8em;">{content_preview}</pre></small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        if total_tables > 10:
                            st.caption(f"... and {total_tables - 10} more table chunks")
                    
                    # Image chunks in red boxes
                    if total_images > 0:
                        st.markdown("### 🖼️ Image Chunks")
                        for i, chunk in enumerate(chunks_by_type['image'][:10]):  # Show first 10
                            page = chunk['metadata'].get('page', 'N/A')
                            img_index = chunk['metadata'].get('image_index', 'N/A')
                            st.markdown(
                                f"""
                                <div style="background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 5px; padding: 10px; margin: 5px 0;">
                                    <strong>Image Chunk #{i+1}</strong> - Page {page}, Image #{img_index}<br>
                                    <small>Format: {chunk['metadata'].get('format', 'N/A')}</small>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        if total_images > 10:
                            st.caption(f"... and {total_images - 10} more image chunks")
            else:
                st.info("No chunks found in the database.")
        except Exception as e:
            st.warning(f"Unable to load chunking data: {str(e)}")
    else:
        st.info("Process a PDF first to see chunking visualization.")
    
    st.divider()
    
    # PDF file uploader
    st.subheader("📄 PDF Document")
    pdf_file = st.file_uploader("Upload PDF", type=['pdf'], help="Upload a PDF document to process")
    
    if pdf_file is not None:
        # Save uploaded file
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        
        pdf_path = os.path.join("uploads", pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
        
        st.success(f"✅ PDF uploaded: {pdf_file.name}")
    else:
        # Use default PDF if available
        if os.path.exists(PDF_PATH):
            pdf_path = PDF_PATH
            st.info(f"📄 Using default PDF: {PDF_PATH}")
        else:
            pdf_path = None
            st.warning("⚠️ Please upload a PDF file or ensure the default PDF exists")
    
    st.divider()
    
    # Check if data already exists
    data_exists = False
    if st.session_state.rag_system:
        try:
            data_exists = st.session_state.rag_system.is_ready()
        except:
            pass
    
    # Process PDF button (only show if no data exists)
    if pdf_path and not data_exists:
        if st.button("🔄 Process PDF & Build Knowledge Base", type="primary"):
            st.session_state.processing = True
            st.session_state.processed = False
            
            with st.spinner("Processing PDF... This may take a few minutes."):
                try:
                    rag_system = RAGSystem()
                    stats = rag_system.process_pdf(pdf_path)
                    
                    st.session_state.rag_system = rag_system
                    st.session_state.processed = True
                    st.session_state.processing = False
                    
                    st.success("✅ PDF processed successfully!")
                    st.json(stats)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {str(e)}")
                    st.session_state.processing = False
    
    # Show status
    if data_exists:
        st.success("✅ Knowledge base loaded! Ready to query.")
        if st.button("🔄 Reprocess PDF", help="Clear existing data and reprocess"):
            if st.session_state.rag_system:
                try:
                    st.session_state.rag_system.vector_store.clear_collection()
                    st.session_state.rag_system = None
                    st.session_state.processed = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing data: {str(e)}")
    
    # Stats
    if st.session_state.processed and st.session_state.rag_system:
        st.divider()
        st.subheader("📊 Statistics")
        try:
            stats = st.session_state.rag_system.get_stats()
            st.metric("Total Chunks", stats['total_chunks'])
            st.metric("Collection", stats['collection_name'])
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

# Main content area
if st.session_state.processed and st.session_state.rag_system:
    # Query interface
    st.header("💬 Ask Questions")
    
    # Query input
    query = st.text_input(
        "Enter your question about the Radar Solar Energy Storage Project:",
        placeholder="e.g., What is the project capacity? What are the environmental concerns?",
        key="query_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        top_k = st.slider("Number of sources", 1, 10, 5)
    
    with col2:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Process query
    if search_button and query:
        with st.spinner("Searching and generating answer..."):
            result = st.session_state.rag_system.query(query, top_k=top_k)
            
            # Display answer
            st.markdown("### 💡 Answer")
            st.markdown(result['answer'])
            
            # Display sources
            st.markdown("### 📚 Sources")
            for i, source in enumerate(result['sources'], 1):
                with st.expander(f"Source {i} - Page {source['metadata'].get('page', 'N/A')} ({source['metadata'].get('type', 'unknown').upper()})"):
                    st.write(f"**Type:** {source['metadata'].get('type', 'unknown')}")
                    st.write(f"**Page:** {source['metadata'].get('page', 'N/A')}")
                    if source['metadata'].get('type') == 'table':
                        st.write("**Content:**")
                        st.code(source['content'][:1000], language=None)
                    else:
                        st.write("**Content:**")
                        st.write(source['content'][:1000])
                    if 'distance' in source and source['distance']:
                        st.write(f"**Similarity Score:** {1 - source['distance']:.4f}")
            
            # Show number of sources
            st.info(f"📊 Found {result['num_sources']} relevant sources")

else:
    # Welcome message
    if os.path.exists(PDF_PATH):
        st.info("📄 PDF found in root folder. The system will auto-load existing embeddings if available, or you can process it using the sidebar.")
    else:
        st.info("👈 Please upload a PDF file and process it using the sidebar to start querying.")
    
    st.markdown("""
    ### 🚀 Features
    
    - ✅ **Separate Chunking**: Text, images, and tables are processed separately
    - ✅ **AI Summarization**: Each chunk gets an AI-generated summary using Perplexity Sonar Pro
    - ✅ **Separate Embeddings**: Different embedding vectors for each content type
    - ✅ **Vector Database**: ChromaDB for efficient similarity search with indexing
    - ✅ **LLM Querying**: Perplexity Sonar Pro for generating answers
    - ✅ **Beautiful UI**: Streamlit interface for easy querying
    - ✅ **Persistent Storage**: Embeddings are saved and auto-loaded on startup
    
    ### 📖 How to Use
    
    1. Place your PDF in the root folder (or upload via sidebar)
    2. Click "Process PDF & Build Knowledge Base" **once** - embeddings will be saved
    3. Next time you open the app, it will auto-load existing embeddings
    4. Ask questions about the document
    5. View answers with source citations
    
    ### 💾 Data Persistence
    
    - Embeddings are stored in `chroma_db/` directory
    - Once processed, you don't need to reprocess unless you want to update the data
    - The system automatically detects and loads existing embeddings
    """)


if __name__ == "__main__":
    pass

