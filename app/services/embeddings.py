import hashlib
from typing import List
from sentence_transformers import SentenceTransformer
from diskcache import Cache
from app.core.config import get_settings


class EmbeddingService:
    """Handles embedding generation with caching using local sentence-transformers model."""
    
    def __init__(self):
        settings = get_settings()
        self.model_name = settings.embedding_model
        self.cache = Cache(settings.cache_dir)
        
        # Load the sentence-transformers model once at startup
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"Embedding model loaded. Dimension: {self.model.get_sentence_embedding_dimension()}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text with caching.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector
        """
        cache_key = self._get_cache_key(text)
        
        cached_embedding = self.cache.get(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        
        try:
            # sentence-transformers encode is synchronous, but we run it in async context
            embedding = self.model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()
            
            self.cache.set(cache_key, embedding_list)
            
            return embedding_list
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        uncached_texts = []
        uncached_indices = []
        
        # Check cache first
        for idx, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cached_embedding = self.cache.get(cache_key)
            
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                uncached_texts.append(text)
                uncached_indices.append(idx)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            try:
                # Batch encode is much faster than encoding one by one
                batch_embeddings = self.model.encode(
                    uncached_texts, 
                    convert_to_numpy=True,
                    show_progress_bar=True
                )
                
                for i, embedding in enumerate(batch_embeddings):
                    embedding_list = embedding.tolist()
                    original_idx = uncached_indices[i]
                    embeddings[original_idx] = embedding_list
                    
                    # Cache the embedding
                    cache_key = self._get_cache_key(uncached_texts[i])
                    self.cache.set(cache_key, embedding_list)
                    
            except Exception as e:
                raise RuntimeError(f"Failed to generate batch embeddings: {str(e)}")
        
        return embeddings
    
    def _get_cache_key(self, text: str) -> str:
        """
        Generate a cache key for a text.
        
        Args:
            text: Text to generate key for
            
        Returns:
            Cache key
        """
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{self.model_name}:{text_hash}"
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self.cache.clear()
