import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.rag_service import RAGService

app = FastAPI(
    title="ISRO UHI Mitigation AI Microservice",
    description="Decoupled AI Engine for RAG Knowledge Indexing and LLM Completions",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG service
rag_service = RAGService()

from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    selected_cells: Optional[List[dict]] = None

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "ISRO UHI AI Agent"}

@app.post("/api/chat")
def run_chat(req: ChatRequest):
    try:
        if not req.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        answer = rag_service.query(req.message, req.selected_cells)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Allow running directly on port 8001
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
