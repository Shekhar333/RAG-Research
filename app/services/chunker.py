import tiktoken
import random
from typing import List, Dict
from app.models.schemas import DocumentChunk, ChunkMetadata


class TextChunker:
    """Handles text chunking with token-based splitting and overlap."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk_pages(
        self, 
        pages_data: List[Dict[str, any]], 
        document_id: str
    ) -> List[DocumentChunk]:
        """
        Chunk pages into smaller segments with metadata preservation.
        
        Args:
            pages_data: List of page data with text, page number, and section
            document_id: Unique identifier for the document
            
        Returns:
            List of DocumentChunk objects with metadata
        """
        chunks = []
        
        # Generate a unique base ID for this document's chunks to avoid collisions
        # Use a random offset to ensure global uniqueness across documents
        base_chunk_id = random.randint(1, 1_000_000_000)
        chunk_index = 0
        
        for page_data in pages_data:
            text = page_data["text"]
            page_num = page_data["page"]
            section = page_data["section"]
            
            page_chunks = self._chunk_text(text)
            
            for chunk_text in page_chunks:
                # Create globally unique chunk ID
                unique_chunk_id = base_chunk_id + chunk_index
                
                metadata = ChunkMetadata(
                    document_id=document_id,
                    section=section,
                    page=page_num,
                    chunk_index=unique_chunk_id
                )
                
                chunk = DocumentChunk(
                    text=chunk_text,
                    metadata=metadata
                )
                
                chunks.append(chunk)
                chunk_index += 1
        
        return chunks
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks based on token count with overlap.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        tokens = self.encoding.encode(text)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if end >= len(tokens):
                break
            
            start = end - self.chunk_overlap
        
        return chunks if chunks else [text]
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
