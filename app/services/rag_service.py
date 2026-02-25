import uuid
from typing import List
from pathlib import Path
from app.services.pdf_processor import PDFProcessor
from app.services.chunker import TextChunker
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.answer_generator import AnswerGenerator
from app.models.schemas import UploadResponse, QueryRequest, QueryResponse, DocumentChunk
from app.core.config import get_settings


class RAGService:
    """Orchestrates the RAG pipeline for document processing and querying."""
    
    def __init__(self):
        settings = get_settings()
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.answer_generator = AnswerGenerator()
        self.settings = settings
    
    async def upload_document(self, file_path: str) -> UploadResponse:
        """
        Process and index a PDF document.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            UploadResponse with document ID and status
        """
        is_valid, error_msg = self.pdf_processor.validate_pdf(
            file_path, 
            self.settings.max_pdf_size_mb
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        document_id = str(uuid.uuid4())
        
        if await self.vector_store.document_exists(document_id):
            return UploadResponse(
                document_id=document_id,
                status="indexed"
            )
        
        pages_data = self.pdf_processor.extract_text_with_metadata(file_path)
        
        chunks = self.chunker.chunk_pages(pages_data, document_id)
        
        texts = [chunk.text for chunk in chunks]
        embeddings = await self.embedding_service.generate_embeddings_batch(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        await self.vector_store.store_chunks(chunks)
        
        return UploadResponse(
            document_id=document_id,
            status="indexed"
        )
    
    async def query_document(self, request: QueryRequest) -> QueryResponse:
        """
        Query a document and generate an answer with citations.
        
        Args:
            request: QueryRequest with document_id, question, and top_k
            
        Returns:
            QueryResponse with answer and citations
        """
        if not await self.vector_store.document_exists(request.document_id):
            raise ValueError(f"Document {request.document_id} not found")
        
        query_embedding = await self.embedding_service.generate_embedding(request.question)
        
        retrieved_chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            document_id=request.document_id,
            top_k=request.top_k,
            score_threshold=None  # Don't filter at Qdrant level, filter in answer_generator
        )
        
        response = await self.answer_generator.generate_answer(
            question=request.question,
            retrieved_chunks=retrieved_chunks
        )
        
        return response
