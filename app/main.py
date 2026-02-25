import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.models.schemas import UploadResponse, QueryRequest, QueryResponse
from app.services.rag_service import RAGService
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    settings = get_settings()
    os.makedirs(settings.cache_dir, exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    yield
    

app = FastAPI(
    title="RAG Research Paper AI Assistant",
    description="A production-ready RAG system for research paper question answering",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = RAGService()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Research Paper AI Assistant",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/upload",
            "query": "/query"
        }
    }


@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a research paper PDF.
    
    Args:
        file: PDF file to upload
        
    Returns:
        UploadResponse with document_id and status
        
    Raises:
        HTTPException: If file is invalid or processing fails
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    temp_path = None
    try:
        temp_path = Path("uploads") / f"temp_{file.filename}"
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        settings = get_settings()
        timeout = settings.max_query_latency_seconds
        
        try:
            response = await asyncio.wait_for(
                rag_service.upload_document(str(temp_path)),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Upload processing exceeded {timeout} seconds"
            )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


@app.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    Query a document with a question and receive an answer with citations.
    
    Args:
        request: QueryRequest with document_id, question, and optional top_k
        
    Returns:
        QueryResponse with answer and citations
        
    Raises:
        HTTPException: If document not found or query fails
    """
    try:
        settings = get_settings()
        timeout = settings.max_query_latency_seconds
        
        try:
            response = await asyncio.wait_for(
                rag_service.query_document(request),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail=f"Query processing exceeded {timeout} seconds"
            )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
