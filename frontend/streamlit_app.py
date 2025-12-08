# frontend/streamlit_app.py
"""
Streamlit UI for ImageAI Document AI Platform.
Provides interactive interface for OCR, RAG, and Knowledge Graph features.
"""
import streamlit as st
import requests
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.rag_engine import create_vector_store, query_vector_store, get_store_stats, FAISS_AVAILABLE
from core.kg_builder import build_graph_from_fields, export_graph_json, export_graph_png, get_graph_stats
from utils.file_handler import extract_text_sync
import asyncio

# Page config
st.set_page_config(
    page_title="ImageAI Document AI Platform",
    page_icon="📄",
    layout="wide"
)

# Title
st.title("📄 ImageAI Document AI Platform")
st.markdown("**Complete OCR, RAG, and Knowledge Graph solution for document processing**")

# Sidebar
st.sidebar.title("Navigation")
tab_selection = st.sidebar.radio(
    "Select Feature",
    ["OCR Processing", "Structured Extraction", "RAG Query", "Knowledge Graph", "Debug Info"]
)

# Initialize session state
if 'ocr_text' not in st.session_state:
    st.session_state.ocr_text = ""
if 'extracted_fields' not in st.session_state:
    st.session_state.extracted_fields = {}
if 'rag_indexed' not in st.session_state:
    st.session_state.rag_indexed = False

# Tab 1: OCR Processing
if tab_selection == "OCR Processing":
    st.header("📸 OCR Processing")
    
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'xlsx', 'csv', 'txt'],
        help="Supports images, PDFs, DOCX, Excel, CSV, and TXT files"
    )
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Document")
            if uploaded_file.type.startswith('image'):
                st.image(uploaded_file, use_container_width=True)
            else:
                st.info(f"📄 {uploaded_file.name} ({uploaded_file.type})")
        
        if st.button("🔍 Extract Text", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    # Extract text
                    content = uploaded_file.read()
                    result = extract_text_sync(content, uploaded_file.name)
                    
                    if isinstance(result, dict):
                        st.session_state.ocr_text = result.get("text", "")
                        if not result.get("success", False):
                            st.error(f"❌ {result.get('message', 'Extraction failed')}")
                    else:
                        st.session_state.ocr_text = result
                    
                    st.success("✅ Text extracted successfully!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        if st.session_state.ocr_text:
            with col2:
                st.subheader("Extracted Text")
                st.text_area(
                    "OCR Output",
                    st.session_state.ocr_text,
                    height=400,
                    label_visibility="collapsed"
                )
                
                st.download_button(
                    "📥 Download Text",
                    st.session_state.ocr_text,
                    file_name="extracted_text.txt",
                    mime="text/plain"
                )

# Tab 2: Structured Extraction
elif tab_selection == "Structured Extraction":
    st.header("📋 Structured Field Extraction")
    
    if not st.session_state.ocr_text:
        st.warning("⚠️ Please extract text from a document first (go to OCR Processing tab)")
    else:
        st.text_area("Current OCR Text", st.session_state.ocr_text, height=200, disabled=True)
        
        question = st.text_input(
            "Ask a question about the document",
            placeholder="e.g., Extract invoice number, date, and total amount"
        )
        
        if st.button("🎯 Extract Fields", type="primary"):
            if question:
                with st.spinner("Extracting structured fields..."):
                    try:
                        from core.field_extractor import extract_structured_fields
                        result = asyncio.run(extract_structured_fields(st.session_state.ocr_text, question))
                        st.session_state.extracted_fields = result
                        st.success("✅ Fields extracted!")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter a question")
        
        if st.session_state.extracted_fields:
            st.subheader("Extracted Information")
            st.json(st.session_state.extracted_fields)
            
            st.download_button(
                "📥 Download as JSON",
                json.dumps(st.session_state.extracted_fields, indent=2),
                file_name="extracted_fields.json",
                mime="application/json"
            )

# Tab 3: RAG Query
elif tab_selection == "RAG Query":
    st.header("🔍 RAG Query System")
    
    if not FAISS_AVAILABLE:
        st.error("❌ FAISS is not installed. Install with: `pip install faiss-cpu`")
    else:
        if not st.session_state.ocr_text:
            st.warning("⚠️ Please extract text from a document first (go to OCR Processing tab)")
        else:
            st.subheader("Index Document")
            
            if st.button("📚 Index Current Document", type="primary"):
                with st.spinner("Indexing document..."):
                    try:
                        store_id = create_vector_store(st.session_state.ocr_text)
                        st.session_state.rag_indexed = True
                        stats = get_store_stats(store_id)
                        st.success(f"✅ Document indexed! Created {stats['num_chunks']} chunks")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            if st.session_state.rag_indexed:
                st.subheader("Query Document")
                
                query = st.text_input(
                    "Ask a question",
                    placeholder="e.g., What is the total amount?"
                )
                
                top_k = st.slider("Number of results", 1, 10, 5)
                
                if st.button("🔎 Search", type="primary"):
                    if query:
                        with st.spinner("Searching..."):
                            try:
                                result = query_vector_store(query, top_k=top_k)
                                
                                st.subheader("Results")
                                for i, (chunk, score) in enumerate(zip(result["chunks"], result["scores"])):
                                    with st.expander(f"Result {i+1} (Relevance: {score:.3f})"):
                                        st.write(chunk)
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    else:
                        st.warning("Please enter a query")

# Tab 4: Knowledge Graph
elif tab_selection == "Knowledge Graph":
    st.header("🕸️ Knowledge Graph")
    
    if not st.session_state.extracted_fields:
        st.warning("⚠️ Please extract structured fields first (go to Structured Extraction tab)")
    else:
        st.subheader("Generate Knowledge Graph")
        
        doc_name = st.text_input("Document Name", value="Document")
        export_format = st.selectbox("Export Format", ["JSON", "PNG", "Both"])
        
        if st.button("🎨 Generate Graph", type="primary"):
            with st.spinner("Generating knowledge graph..."):
                try:
                    graph = build_graph_from_fields(st.session_state.extracted_fields, doc_name)
                    stats = get_graph_stats(graph)
                    
                    st.success(f"✅ Graph generated! {stats['num_nodes']} nodes, {stats['num_edges']} edges")
                    
                    # Export
                    if export_format in ["JSON", "Both"]:
                        json_path = export_graph_json(graph)
                        with open(json_path, 'r') as f:
                            st.download_button(
                                "📥 Download JSON",
                                f.read(),
                                file_name="knowledge_graph.json",
                                mime="application/json"
                            )
                    
                    if export_format in ["PNG", "Both"]:
                        png_path = export_graph_png(graph)
                        st.image(png_path, caption="Knowledge Graph Visualization")
                        with open(png_path, 'rb') as f:
                            st.download_button(
                                "📥 Download PNG",
                                f.read(),
                                file_name="knowledge_graph.png",
                                mime="image/png"
                            )
                    
                    # Show stats
                    st.subheader("Graph Statistics")
                    st.json(stats)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Tab 5: Debug Info
elif tab_selection == "Debug Info":
    st.header("🔧 Debug Information")
    
    st.subheader("Session State")
    st.json({
        "ocr_text_length": len(st.session_state.ocr_text),
        "has_extracted_fields": bool(st.session_state.extracted_fields),
        "rag_indexed": st.session_state.rag_indexed
    })
    
    st.subheader("System Info")
    st.json({
        "faiss_available": FAISS_AVAILABLE,
        "python_version": sys.version,
    })
    
    if st.session_state.ocr_text:
        st.subheader("Current OCR Text")
        st.code(st.session_state.ocr_text, language="text")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**ImageAI v2.0**")
st.sidebar.markdown("Document AI Platform")
