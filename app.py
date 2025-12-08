# app.py
"""
Entry point for ImageAI Document AI Platform.
Runs the FastAPI server.
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3000"))
    reload = os.getenv("RELOAD", "True").lower() == "true"
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   ImageAI Document AI Platform v2.0                      ║
║   Complete OCR, RAG, and Knowledge Graph Solution        ║
║                                                          ║
║   API Server: http://{host}:{port}                    ║
║   API Docs:   http://{host}:{port}/docs              ║
║                                                          ║
║   Run Streamlit UI:                                      ║
║   streamlit run frontend/streamlit_app.py                ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run("api.server:app", host=host, port=port, reload=reload)
