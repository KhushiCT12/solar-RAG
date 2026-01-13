"""
Streamlit UI for the RAG System
Beautiful interface for querying the Radar Solar Energy Storage Report
"""
import streamlit as st
import os
from rag_system import RAGSystem
from config import PDF_PATH
import time


# Page configuration
st.set_page_config(
    page_title="CIR Solar RAG System",
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

# Header
st.markdown('<h1 class="main-header">☀️ Radar Solar RAG System</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Query the Desktop Due Diligence Report for Solar + Energy Storage Project</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # PDF file uploader
    st.subheader("📄 PDF Document")
    pdf_file = st.file_uploader("Upload PDF", type=['pdf'], help="Upload the Radar Solar report PDF")
    
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
    
    # Process PDF button
    if pdf_path and not st.session_state.processed:
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
    
    # Stats
    if st.session_state.processed and st.session_state.rag_system:
        st.divider()
        st.subheader("📊 Statistics")
        stats = st.session_state.rag_system.get_stats()
        st.metric("Total Chunks", stats['total_chunks'])
        st.metric("Collection", stats['collection_name'])

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
    
    # Example questions
    st.markdown("---")
    st.subheader("💡 Example Questions")
    example_questions = [
        "What is the project capacity and location?",
        "What are the environmental concerns mentioned in the report?",
        "What is the interconnection status?",
        "What are the financial incentives available?",
        "What is the expected energy yield?",
        "What are the risks and constraints identified?",
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(example_questions):
        with cols[i % 2]:
            if st.button(question, key=f"example_{i}", use_container_width=True):
                st.session_state.query_input = question
                st.rerun()

else:
    # Welcome message
    st.info("👈 Please upload a PDF file and process it using the sidebar to start querying.")
    
    st.markdown("""
    ### 🚀 Features
    
    - ✅ **Separate Chunking**: Text, images, and tables are processed separately
    - ✅ **AI Summarization**: Each chunk gets an AI-generated summary using Perplexity Sonar Pro
    - ✅ **Separate Embeddings**: Different embedding vectors for each content type
    - ✅ **Vector Database**: ChromaDB for efficient similarity search with indexing
    - ✅ **LLM Querying**: Perplexity Sonar Pro for generating answers
    - ✅ **Beautiful UI**: Streamlit interface for easy querying
    
    ### 📖 How to Use
    
    1. Upload the PDF document using the sidebar
    2. Click "Process PDF & Build Knowledge Base" to extract and index the content
    3. Once processed, ask questions about the document
    4. View answers with source citations
    """)


if __name__ == "__main__":
    pass

