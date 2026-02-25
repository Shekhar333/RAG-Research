from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, 
    Distance, 
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from app.core.config import get_settings
from app.models.schemas import DocumentChunk


class VectorStore:
    """Handles vector storage and retrieval using Qdrant."""
    
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.collection_name = settings.qdrant_collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        settings = get_settings()
        collections = self.client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimension,  # 384 for all-MiniLM-L6-v2
                    distance=Distance.COSINE
                )
            )
    
    async def store_chunks(self, chunks: List[DocumentChunk]):
        """
        Store document chunks with embeddings in the vector database.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
        """
        if not chunks:
            return
        
        points = []
        for idx, chunk in enumerate(chunks):
            if chunk.embedding is None:
                raise ValueError(f"Chunk {idx} is missing embedding")
            
            # Use chunk_index as ID (unsigned integer) as Qdrant requires
            # Store document_id in payload for filtering
            point = PointStruct(
                id=chunk.metadata.chunk_index,
                vector=chunk.embedding,
                payload={
                    "document_id": chunk.metadata.document_id,
                    "section": chunk.metadata.section,
                    "page": chunk.metadata.page,
                    "chunk_index": chunk.metadata.chunk_index,
                    "text": chunk.text
                }
            )
            points.append(point)
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    async def search(
        self, 
        query_embedding: List[float],
        document_id: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for similar chunks in the vector database.
        
        Args:
            query_embedding: Query vector
            document_id: Filter by document ID
            top_k: Number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of search results with metadata and scores
        """
        print(f"Searching for document_id: {document_id}")
        
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )
        
        print(f"Found {len(results)} results from Qdrant")
        
        return [
            {
                "text": result.payload["text"],
                "section": result.payload["section"],
                "page": result.payload["page"],
                "chunk_index": result.payload["chunk_index"],
                "score": result.score
            }
            for result in results
        ]
    
    async def document_exists(self, document_id: str) -> bool:
        """
        Check if a document exists in the vector store.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=query_filter,
            limit=1
        )
        
        return len(results[0]) > 0
    
    async def delete_document(self, document_id: str):
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: Document identifier
        """
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id)
                )
            ]
        )
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=query_filter
        )
    
    def reset_collection(self):
        """Delete and recreate the collection."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except Exception:
            pass
        
        self._ensure_collection()
