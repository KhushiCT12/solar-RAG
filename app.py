"""
Streamlit UI for the RAG System
Beautiful interface for querying documents using CIR RAG System
"""
import streamlit as st
import os
from rag_system import RAGSystem
from config import PDF_PATH
import time
from pdf_processor import PDFProcessor
from PIL import Image, ImageDraw, ImageFont
import io


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
if 'show_chunking' not in st.session_state:
    st.session_state.show_chunking = False

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
    
    # Chunking Visualization Button
    st.subheader("📊 Chunking Visualization")
    
    # Check if we have data to visualize
    if st.session_state.rag_system and st.session_state.rag_system.is_ready():
        if st.button("📄 View All Chunks", type="primary", use_container_width=True):
            st.session_state.show_chunking = True
            st.rerun()
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
# Show chunking visualization if requested
if st.session_state.show_chunking and st.session_state.rag_system:
    # Import the chunking visualization content
    try:
        from pages.chunking_visualization import show_chunking_page
        show_chunking_page(st.session_state.rag_system.vector_store)
    except ImportError:
        # Fallback: show inline visualization
        st.title("📊 Chunking Visualization")
        st.markdown("View how your PDF has been chunked - chunks displayed by page with colored boxes")
        
        if st.button("← Back to Query"):
            st.session_state.show_chunking = False
            st.rerun()
        
        # Get chunks grouped by page
        chunks_by_page = st.session_state.rag_system.vector_store.get_all_chunks_by_page()
        
        if not chunks_by_page:
            st.warning("No chunks found. Please process a PDF first.")
        else:
            # Summary metrics
            total_pages = len(chunks_by_page)
            total_chunks = sum(len(chunks) for chunks in chunks_by_page.values())
            total_text = sum(1 for chunks in chunks_by_page.values() for c in chunks if c['metadata'].get('type', '').lower() == 'text')
            total_tables = sum(1 for chunks in chunks_by_page.values() for c in chunks if c['metadata'].get('type', '').lower() == 'table')
            total_images = sum(1 for chunks in chunks_by_page.values() for c in chunks if c['metadata'].get('type', '').lower() == 'image')
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Pages", total_pages)
            with col2:
                st.metric("Total Chunks", total_chunks)
            with col3:
                st.metric("📝 Text", total_text)
            with col4:
                st.metric("📊 Tables", total_tables)
            with col5:
                st.metric("🖼️ Images", total_images)
            
            st.divider()
            
            # Page selector
            sorted_pages = sorted(chunks_by_page.keys())
            selected_page = st.selectbox(
                "Select Page to View:",
                sorted_pages,
                format_func=lambda x: f"Page {x} ({len(chunks_by_page[x])} chunks)"
            )
            
            st.markdown(f"### 📄 Page {selected_page} - {len(chunks_by_page[selected_page])} Chunks")
            
            # Render and display the actual PDF page
            try:
                pdf_path = PDF_PATH if os.path.exists(PDF_PATH) else None
                if not pdf_path and st.session_state.rag_system and hasattr(st.session_state.rag_system, 'pdf_processor'):
                    pdf_path = st.session_state.rag_system.pdf_processor.pdf_path if st.session_state.rag_system.pdf_processor else None
                
                if pdf_path and os.path.exists(pdf_path):
                    pdf_processor = PDFProcessor(pdf_path)
                    page_image = pdf_processor.render_page_as_image(selected_page, zoom=1.5)
                    
                    # Draw bounding boxes on the page
                    draw = ImageDraw.Draw(page_image)
                    page_width, page_height = page_image.size
                    
                    # Get chunks for this page
                    page_chunks = chunks_by_page[selected_page]
                    
                    # Draw bounding boxes for each chunk
                    for chunk in page_chunks:
                        chunk_type = chunk['metadata'].get('type', '').lower()
                        bbox = chunk['metadata'].get('bbox')
                        
                        if bbox:
                            # Convert PDF coordinates to image coordinates
                            # PDF coordinates: (x0, y0, x1, y1) where y0 is from bottom
                            # Image coordinates: (x, y) where y is from top
                            
                            # Get page dimensions from PDF
                            pdf_page = pdf_processor.doc[selected_page - 1]
                            pdf_width = pdf_page.rect.width
                            pdf_height = pdf_page.rect.height
                            
                            # Scale factors
                            scale_x = page_width / pdf_width
                            scale_y = page_height / pdf_height
                            
                            # Convert coordinates
                            x0 = int(bbox['x0'] * scale_x)
                            y0 = int((pdf_height - bbox['y1']) * scale_y)  # Flip Y axis
                            x1 = int(bbox['x1'] * scale_x)
                            y1 = int((pdf_height - bbox['y0']) * scale_y)  # Flip Y axis
                            
                            # Choose color based on chunk type
                            if chunk_type == 'text':
                                color = '#28a745'  # Green
                            elif chunk_type == 'table':
                                color = '#6f42c1'  # Purple
                            elif chunk_type == 'image':
                                color = '#dc3545'  # Red
                            else:
                                color = '#000000'  # Black
                            
                            # Draw rectangle
                            draw.rectangle([x0, y0, x1, y1], outline=color, width=3)
                    
                    # Display the annotated page image
                    st.image(page_image, caption=f"Page {selected_page} with Chunk Bounding Boxes", use_container_width=True)
                    pdf_processor.close()
                else:
                    st.info("PDF file not found. Cannot render page image.")
            except Exception as e:
                st.warning(f"Could not render PDF page: {str(e)}")
                st.info("Showing chunks without page visualization.")
            
            # Display chunks for selected page
            page_chunks = chunks_by_page[selected_page]
            
            # Group chunks by type for this page
            text_chunks = [c for c in page_chunks if c['metadata'].get('type', '').lower() == 'text']
            table_chunks = [c for c in page_chunks if c['metadata'].get('type', '').lower() == 'table']
            image_chunks = [c for c in page_chunks if c['metadata'].get('type', '').lower() == 'image']
            
            # Display text chunks in green boxes
            if text_chunks:
                st.markdown("#### 📝 Text Chunks")
                for chunk in text_chunks:
                    content = chunk['content']
                    display_content = content[:500] + "..." if len(content) > 500 else content
                    chunk_idx = chunk['metadata'].get('chunk_index', 0) + 1
                    
                    st.markdown(
                        f"""
                        <div style="background-color: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 8px; color: #155724;">📝 Text Chunk #{chunk_idx}</div>
                            <div style="color: #555; line-height: 1.6;">{display_content}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if len(content) > 500:
                        with st.expander(f"View full content of Text Chunk #{chunk_idx}"):
                            st.text(content)
            
            # Display table chunks in purple boxes
            if table_chunks:
                st.markdown("#### 📊 Table Chunks")
                for chunk in table_chunks:
                    content = chunk['content']
                    display_content = content[:800] + "..." if len(content) > 800 else content
                    chunk_idx = chunk['metadata'].get('chunk_index', 0) + 1
                    table_idx = chunk['metadata'].get('table_index', 0) + 1
                    rows = chunk['metadata'].get('rows', 0)
                    cols = chunk['metadata'].get('columns', 0)
                    
                    st.markdown(
                        f"""
                        <div style="background-color: #e2d9f3; border: 2px solid #6f42c1; border-radius: 8px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 8px; color: #4a148c;">📊 Table Chunk #{chunk_idx} (Table #{table_idx})</div>
                            <div style="color: #666; font-size: 0.9em; margin-bottom: 8px;">{rows} rows × {cols} columns</div>
                            <pre style="white-space: pre-wrap; font-family: monospace; background: transparent; color: #555; margin: 0; font-size: 0.9em;">{display_content}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if len(content) > 800:
                        with st.expander(f"View full content of Table Chunk #{chunk_idx}"):
                            st.text(content)
            
            # Display image chunks in red boxes
            if image_chunks:
                st.markdown("#### 🖼️ Image Chunks")
                for chunk in image_chunks:
                    chunk_idx = chunk['metadata'].get('chunk_index', 0) + 1
                    img_idx = chunk['metadata'].get('image_index', 0) + 1
                    img_format = chunk['metadata'].get('format', 'N/A')
                    width = chunk['metadata'].get('width', 0)
                    height = chunk['metadata'].get('height', 0)
                    
                    st.markdown(
                        f"""
                        <div style="background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 15px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <div style="font-weight: bold; font-size: 1.1em; margin-bottom: 8px; color: #721c24;">🖼️ Image Chunk #{chunk_idx}</div>
                            <div style="color: #555; line-height: 1.6;">
                                Image #{img_idx} on this page<br>
                                Format: {img_format} | Dimensions: {width} × {height} pixels
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Navigation between pages
            st.divider()
            col_prev, col_next = st.columns(2)
            with col_prev:
                if selected_page > min(sorted_pages):
                    prev_page = sorted_pages[sorted_pages.index(selected_page) - 1]
                    if st.button(f"← Previous Page ({prev_page})"):
                        st.session_state.selected_page = prev_page
                        st.rerun()
            with col_next:
                if selected_page < max(sorted_pages):
                    next_page = sorted_pages[sorted_pages.index(selected_page) + 1]
                    if st.button(f"Next Page ({next_page}) →"):
                        st.session_state.selected_page = next_page
                        st.rerun()

elif st.session_state.processed and st.session_state.rag_system:
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

