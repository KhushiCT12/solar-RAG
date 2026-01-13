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
if 'show_comparison' not in st.session_state:
    st.session_state.show_comparison = False
if 'show_processed_docs' not in st.session_state:
    st.session_state.show_processed_docs = False

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
    
    # Extraction Comparison Button
    st.subheader("🔍 Extraction Comparison")
    if st.button("📊 Compare pdfplumber vs MarkerPDF", type="secondary", use_container_width=True):
        st.session_state.show_comparison = True
        st.rerun()
    
    st.divider()
    
    # Document file uploader
    st.subheader("📄 Document")
    uploaded_file = st.file_uploader("Upload Document", type=['pdf', 'xlsx', 'xls'], help="Upload a PDF or Excel document to process")
    
    if uploaded_file is not None:
        # Save uploaded file
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        
        file_path = os.path.join("uploads", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_type = "PDF" if file_ext == '.pdf' else "Excel" if file_ext in ['.xlsx', '.xls'] else "Document"
        st.success(f"✅ {file_type} uploaded: {uploaded_file.name}")
    else:
        # Use default PDF if available
        if os.path.exists(PDF_PATH):
            file_path = PDF_PATH
            st.info(f"📄 Using default PDF: {PDF_PATH}")
        else:
            file_path = None
            st.warning("⚠️ Please upload a document (PDF/Excel) or ensure the default PDF exists")
    
    # Processed Documents Button
    st.subheader("📚 Processed Documents")
    if st.button("📋 View Processed Documents", type="secondary", use_container_width=True):
        st.session_state.show_processed_docs = True
        st.rerun()
    
    st.divider()
    
    # Check if data already exists
    data_exists = False
    if st.session_state.rag_system:
        try:
            data_exists = st.session_state.rag_system.is_ready()
        except:
            pass
    
    # Process Document button
    if file_path:
        if not data_exists:
            # First time processing - clear existing flag
            if st.button("🔄 Process Document & Build Knowledge Base", type="primary"):
                st.session_state.processing = True
                st.session_state.processed = False
                
                with st.spinner("Processing document... This may take a few minutes."):
                    try:
                        rag_system = RAGSystem()
                        stats = rag_system.process_document(file_path, clear_existing=False)
                        
                        st.session_state.rag_system = rag_system
                        st.session_state.processed = True
                        st.session_state.processing = False
                        
                        st.success("✅ Document processed successfully!")
                        st.json(stats)
                        st.rerun()
                    except Exception as e:
                        error_msg = str(e)
                        st.error(f"❌ Error processing document: {error_msg}")
                        
                        # Check if it's a ChromaDB corruption error
                        if "compaction" in error_msg.lower() or "metadata" in error_msg.lower():
                            st.warning("⚠️ ChromaDB database corruption detected.")
                            st.info("💡 **Solution**: Click 'Reset Database' below to fix this issue, then try processing again.")
                            
                            if st.button("🗑️ Reset Database", type="secondary", key="reset_db_error"):
                                try:
                                    import shutil
                                    if os.path.exists("./chroma_db"):
                                        shutil.rmtree("./chroma_db")
                                    st.success("✅ Database reset. Please try processing the document again.")
                                    st.session_state.rag_system = None
                                    st.session_state.processed = False
                                    st.rerun()
                                except Exception as reset_error:
                                    st.error(f"Error resetting database: {str(reset_error)}")
                        
                        st.session_state.processing = False
        else:
            # Data exists - show additive processing option
            col_add, col_replace = st.columns(2)
            with col_add:
                if st.button("➕ Add Document", type="primary", help="Add this document to existing knowledge base"):
                    st.session_state.processing = True
                    
                    with st.spinner("Adding document to knowledge base... This may take a few minutes."):
                        try:
                            # Use existing RAG system to add to it
                            if st.session_state.rag_system is None:
                                st.session_state.rag_system = RAGSystem()
                            
                            stats = st.session_state.rag_system.process_document(file_path, clear_existing=False)
                            st.session_state.processed = True
                            st.session_state.processing = False
                            
                            st.success("✅ Document added successfully! Embeddings preserved.")
                            st.json(stats)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error adding document: {str(e)}")
                            st.session_state.processing = False
            
            with col_replace:
                if st.button("🔄 Replace All", type="secondary", help="Clear existing data and process this document"):
                    if st.session_state.rag_system:
                        try:
                            st.session_state.rag_system.vector_store.clear_collection()
                            st.session_state.rag_system = None
                            st.session_state.processed = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error clearing data: {str(e)}")
    
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
# Show processed documents page if requested
if st.session_state.show_processed_docs:
    st.title("📚 Processed Documents")
    
    if st.button("← Back to Main", type="secondary"):
        st.session_state.show_processed_docs = False
        st.rerun()
    
    st.markdown("### List of Processed Documents")
    
    # Get processed documents from various sources
    processed_docs = []
    
    # Check uploads folder
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(filename)[1].lower()
                file_size = os.path.getsize(file_path)
                file_mtime = os.path.getmtime(file_path)
                
                # Check if this file has been processed (has data in ChromaDB)
                is_processed = False
                if st.session_state.rag_system:
                    try:
                        is_processed = st.session_state.rag_system.is_ready()
                    except:
                        pass
                
                processed_docs.append({
                    'name': filename,
                    'path': file_path,
                    'type': file_ext,
                    'size': file_size,
                    'modified': file_mtime,
                    'processed': is_processed,
                    'source': 'uploads'
                })
    
    # Check default PDF
    if os.path.exists(PDF_PATH):
        file_ext = os.path.splitext(PDF_PATH)[1].lower()
        file_size = os.path.getsize(PDF_PATH)
        file_mtime = os.path.getmtime(PDF_PATH)
        
        is_processed = False
        if st.session_state.rag_system:
            try:
                is_processed = st.session_state.rag_system.is_ready()
            except:
                pass
        
        processed_docs.append({
            'name': os.path.basename(PDF_PATH),
            'path': PDF_PATH,
            'type': file_ext,
            'size': file_size,
            'modified': file_mtime,
            'processed': is_processed,
            'source': 'default'
        })
    
    # Check ChromaDB for processed documents info
    if st.session_state.rag_system:
        try:
            stats = st.session_state.rag_system.get_stats()
            if stats['total_chunks'] > 0:
                # Mark all documents as potentially processed if ChromaDB has data
                for doc in processed_docs:
                    if doc['type'] in ['.pdf', '.xlsx', '.xls', '.docx', '.doc']:
                        doc['processed'] = True
        except:
            pass
    
    if processed_docs:
        # Sort by modification time (newest first)
        processed_docs.sort(key=lambda x: x['modified'], reverse=True)
        
        # Display documents in a table format
        for idx, doc in enumerate(processed_docs):
            # Determine file type icon
            file_icons = {
                '.pdf': '📄',
                '.xlsx': '📊',
                '.xls': '📊',
                '.docx': '📝',
                '.doc': '📝',
                '.txt': '📃',
                '.csv': '📈'
            }
            icon = file_icons.get(doc['type'], '📎')
            
            # Format file size
            size_mb = doc['size'] / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{doc['size'] / 1024:.2f} KB"
            
            # Format modification date
            from datetime import datetime
            mod_date = datetime.fromtimestamp(doc['modified']).strftime("%Y-%m-%d %H:%M:%S")
            
            # Status badge
            status = "✅ Processed" if doc['processed'] else "⏳ Not Processed"
            status_color = "#28a745" if doc['processed'] else "#ffc107"
            
            # Create expandable card for each document
            with st.expander(f"{icon} {doc['name']} - {status}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**File Type:** {doc['type'].upper() if doc['type'] else 'Unknown'}")
                    st.markdown(f"**File Size:** {size_str}")
                    st.markdown(f"**Source:** {doc['source']}")
                
                with col2:
                    st.markdown(f"**Modified:** {mod_date}")
                    st.markdown(f"**Status:** <span style='color: {status_color}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)
                    if doc['processed']:
                        try:
                            stats = st.session_state.rag_system.get_stats()
                            st.markdown(f"**Total Chunks:** {stats['total_chunks']}")
                        except:
                            pass
                
                # Action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button(f"🔄 Reprocess", key=f"reprocess_{idx}"):
                        st.session_state.reprocess_file = doc['path']
                        st.session_state.show_processed_docs = False
                        st.rerun()
                
                with col_btn2:
                    if st.button(f"🗑️ Remove", key=f"remove_{idx}"):
                        try:
                            if os.path.exists(doc['path']) and doc['source'] == 'uploads':
                                os.remove(doc['path'])
                                st.success(f"Removed {doc['name']}")
                                st.rerun()
                            else:
                                st.warning("Cannot remove default PDF")
                        except Exception as e:
                            st.error(f"Error removing file: {e}")
                
                with col_btn3:
                    if doc['processed']:
                        if st.button(f"🔍 Query", key=f"query_{idx}"):
                            st.session_state.show_processed_docs = False
            st.rerun()
        
        # Summary statistics
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Documents", len(processed_docs))
        
        with col2:
            processed_count = sum(1 for doc in processed_docs if doc['processed'])
            st.metric("Processed", processed_count)
        
        with col3:
            pdf_count = sum(1 for doc in processed_docs if doc['type'] == '.pdf')
            st.metric("PDF Files", pdf_count)
        
        with col4:
            excel_count = sum(1 for doc in processed_docs if doc['type'] in ['.xlsx', '.xls'])
            st.metric("Excel Files", excel_count)
    
    else:
        st.info("📭 No processed documents found. Upload and process a document to see it here.")
    
    # Handle reprocess action
    if 'reprocess_file' in st.session_state and st.session_state.reprocess_file:
        file_path = st.session_state.reprocess_file
        del st.session_state.reprocess_file
        
        with st.spinner(f"Reprocessing {os.path.basename(file_path)}..."):
            try:
                if st.session_state.rag_system:
                    st.session_state.rag_system.vector_store.clear_collection()
                
                rag_system = RAGSystem()
                stats = rag_system.process_pdf(file_path)
                
                st.session_state.rag_system = rag_system
                st.session_state.processed = True
                
                st.success("✅ Document reprocessed successfully!")
                st.json(stats)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reprocessing: {str(e)}")

# Show extraction comparison if requested
elif st.session_state.show_comparison:
    st.title("📊 Extraction Comparison: pdfplumber vs MarkerPDF")
    
    if st.button("← Back to Main", type="secondary"):
        st.session_state.show_comparison = False
        st.rerun()
    
    # Get PDF path
    pdf_file = st.file_uploader("Upload PDF for comparison", type=['pdf'], key="comparison_pdf")
    
    if pdf_file is not None:
        # Save uploaded file
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        pdf_path = os.path.join("uploads", pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.getbuffer())
    else:
        if os.path.exists(PDF_PATH):
            pdf_path = PDF_PATH
        else:
            pdf_path = None
            st.warning("⚠️ Please upload a PDF file or ensure the default PDF exists")
    
    if pdf_path:
        if st.button("🔄 Run Comparison", type="primary"):
            with st.spinner("Extracting with both methods... This may take a moment."):
                try:
                    from pdf_processor import PDFProcessor
                    import pdfplumber
                    
                    # Extract with pdfplumber
                    st.subheader("Extracting with pdfplumber...")
                    pdfplumber_results = {'text': [], 'tables': [], 'images': []}
                    
                    with pdfplumber.open(pdf_path) as pdf:
                        for page_num, page in enumerate(pdf.pages, 1):
                            # Text
                            text = page.extract_text()
                            if text and text.strip():
                                pdfplumber_results['text'].append({
                                    'page': page_num,
                                    'content': text.strip(),
                                    'length': len(text.strip())
                                })
                            
                            # Tables
                            tables = page.extract_tables()
                            for table_index, table in enumerate(tables):
                                if table:
                                    pdfplumber_results['tables'].append({
                                        'page': page_num,
                                        'table_index': table_index,
                                        'rows': len(table),
                                        'columns': len(table[0]) if table[0] else 0,
                                        'content': str(table)[:500] + "..." if len(str(table)) > 500 else str(table)
                                    })
                    
                    # Extract with markerPDF
                    st.subheader("Extracting with MarkerPDF...")
                    marker_results = {'text': [], 'tables': [], 'images': []}
                    
                    try:
                        processor_marker = PDFProcessor(pdf_path, use_marker=True)
                        marker_content = processor_marker.extract_all()
                        
                        # Process marker results
                        for text_item in marker_content['text']:
                            marker_results['text'].append({
                                'page': text_item['page'],
                                'content': text_item['content'],
                                'length': len(text_item['content']),
                                'method': text_item['metadata'].get('extraction_method', 'marker-pdf')
                            })
                        
                        for table_item in marker_content['tables']:
                            marker_results['tables'].append({
                                'page': table_item['page'],
                                'table_index': table_item['metadata'].get('table_index', 0),
                                'rows': table_item['metadata'].get('rows', 0),
                                'columns': table_item['metadata'].get('columns', 0),
                                'content': table_item['content'][:500] + "..." if len(table_item['content']) > 500 else table_item['content'],
                                'method': table_item['metadata'].get('extraction_method', 'marker-pdf')
                            })
                        
                        processor_marker.close()
                    except Exception as e:
                        st.warning(f"MarkerPDF extraction failed: {e}")
                        marker_results = None
                    
                    # Store results in session state
                    st.session_state.comparison_results = {
                        'pdfplumber': pdfplumber_results,
                        'marker': marker_results,
                        'pdf_path': pdf_path
                    }
                    
                    st.success("✅ Extraction complete!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error during extraction: {str(e)}")
    
    # Display comparison results
    if 'comparison_results' in st.session_state:
        results = st.session_state.comparison_results
        
            # Summary metrics
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("pdfplumber Text Pages", len(results['pdfplumber']['text']))
            st.metric("pdfplumber Tables", len(results['pdfplumber']['tables']))
        
        with col2:
            if results['marker']:
                st.metric("MarkerPDF Text Pages", len(results['marker']['text']))
                st.metric("MarkerPDF Tables", len(results['marker']['tables']))
            else:
                st.metric("MarkerPDF Text Pages", "N/A")
                st.metric("MarkerPDF Tables", "N/A")
        
        with col3:
            if results['marker']:
                pdfplumber_total = sum(t['length'] for t in results['pdfplumber']['text'])
                marker_total = sum(t['length'] for t in results['marker']['text'])
                diff = marker_total - pdfplumber_total
                st.metric("Text Length Difference", f"{diff:+d} chars", 
                delta=f"{diff/pdfplumber_total*100:.1f}%" if pdfplumber_total > 0 else "N/A")
            
        st.divider()
            
        # Page-by-page comparison
        st.subheader("📄 Page-by-Page Comparison")
        
        # Get all unique page numbers
        pdfplumber_pages = set(t['page'] for t in results['pdfplumber']['text'])
        marker_pages = set(t['page'] for t in results['marker']['text']) if results['marker'] else set()
        all_pages = sorted(pdfplumber_pages | marker_pages)
        
        if all_pages:
            selected_page = st.selectbox("Select Page to Compare:", all_pages, key="comparison_page")
            
            col_left, col_right = st.columns(2)
            
            # pdfplumber column
            with col_left:
                st.markdown("### 📘 pdfplumber")
                page_text_plumber = [t for t in results['pdfplumber']['text'] if t['page'] == selected_page]
                page_tables_plumber = [t for t in results['pdfplumber']['tables'] if t['page'] == selected_page]
                
                if page_text_plumber:
                    st.markdown(f"**Text ({len(page_text_plumber[0]['content'])} chars):**")
                    with st.expander("View Text"):
                        st.text(page_text_plumber[0]['content'])
                else:
                    st.info("No text extracted for this page")
                
                if page_tables_plumber:
                    st.markdown(f"**Tables ({len(page_tables_plumber)}):**")
                    for table in page_tables_plumber:
                        with st.expander(f"Table {table['table_index']+1} ({table['rows']} rows × {table['columns']} cols)"):
                            st.text(table['content'])
                else:
                    st.info("No tables found")
            
            # MarkerPDF column
            with col_right:
                st.markdown("### 📗 MarkerPDF")
                if results['marker']:
                    page_text_marker = [t for t in results['marker']['text'] if t['page'] == selected_page]
                    page_tables_marker = [t for t in results['marker']['tables'] if t['page'] == selected_page]
                    
                    if page_text_marker:
                        st.markdown(f"**Text ({len(page_text_marker[0]['content'])} chars):**")
                        with st.expander("View Text"):
                            st.text(page_text_marker[0]['content'])
                    else:
                        st.info("No text extracted for this page")
                    
                    if page_tables_marker:
                        st.markdown(f"**Tables ({len(page_tables_marker)}):**")
                        for table in page_tables_marker:
                            with st.expander(f"Table {table['table_index']+1} ({table['rows']} rows × {table['columns']} cols)"):
                                st.text(table['content'])
                    else:
                        st.info("No tables found")
                else:
                    st.warning("MarkerPDF extraction not available")
        
        # Side-by-side text comparison
        if all_pages:
            st.divider()
            st.subheader("📝 Side-by-Side Text Comparison")
            
            selected_page_text = st.selectbox("Select Page for Text Comparison:", all_pages, key="text_comparison_page")
            
            col_text_left, col_text_right = st.columns(2)
            
            with col_text_left:
                st.markdown("#### pdfplumber Text")
                page_text_plumber = [t for t in results['pdfplumber']['text'] if t['page'] == selected_page_text]
                if page_text_plumber:
                    st.text_area("", page_text_plumber[0]['content'], height=400, key="plumber_text_area", label_visibility="collapsed")
                else:
                    st.info("No text available")
            
            with col_text_right:
                st.markdown("#### MarkerPDF Text")
                if results['marker']:
                    page_text_marker = [t for t in results['marker']['text'] if t['page'] == selected_page_text]
                    if page_text_marker:
                        st.text_area("", page_text_marker[0]['content'], height=400, key="marker_text_area", label_visibility="collapsed")
                    else:
                        st.info("No text available")
                else:
                    st.warning("MarkerPDF not available")

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
                doc_name = source['metadata'].get('document_name', 'Unknown Document')
                doc_type = source['metadata'].get('document_type', '').upper()
                page = source['metadata'].get('page', 'N/A')
                chunk_type = source['metadata'].get('type', 'unknown').upper()
                
                with st.expander(f"Source {i} - {doc_name} | Page {page} ({chunk_type})"):
                    st.write(f"**Document:** {doc_name} ({doc_type})")
                    st.write(f"**Type:** {chunk_type}")
                    st.write(f"**Page:** {page}")
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

