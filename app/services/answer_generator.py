from typing import List, Dict
import httpx
from app.core.config import get_settings
from app.models.schemas import Citation, QueryResponse


class AnswerGenerator:
    """Generates answers from retrieved context using local LLM (Ollama) with strict citation rules."""
    
    def __init__(self):
        settings = get_settings()
        self.ollama_base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.temperature = settings.llm_temperature
        self.similarity_threshold = settings.similarity_threshold
        print(f"Using Ollama LLM: {self.model} at {self.ollama_base_url}")
    
    async def generate_answer(
        self, 
        question: str, 
        retrieved_chunks: List[Dict]
    ) -> QueryResponse:
        """
        Generate an answer with citations from retrieved context.
        
        Args:
            question: User's question
            retrieved_chunks: List of retrieved chunk data with text, section, page, and score
            
        Returns:
            QueryResponse with answer and citations
        """
        # Debug logging
        print(f"Retrieved {len(retrieved_chunks)} chunks")
        if retrieved_chunks:
            print(f"Similarity scores: {[chunk['score'] for chunk in retrieved_chunks[:3]]}")
            print(f"Threshold: {self.similarity_threshold}")
        
        if not retrieved_chunks or all(
            chunk["score"] < self.similarity_threshold for chunk in retrieved_chunks
        ):
            return QueryResponse(
                answer="Insufficient information in the document.",
                citations=[]
            )
        
        relevant_chunks = [
            chunk for chunk in retrieved_chunks 
            if chunk["score"] >= self.similarity_threshold
        ]
        
        print(f"Relevant chunks after threshold: {len(relevant_chunks)}")
        
        context = self._format_context(relevant_chunks)
        
        system_prompt = self._get_system_prompt()
        user_prompt = self._get_user_prompt(question, context)
        
        try:
            # Call Ollama API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False,
                        "options": {
                            "temperature": self.temperature
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()
                answer_text = result["message"]["content"].strip()
            
            citations = self._extract_citations(relevant_chunks)
            
            return QueryResponse(
                answer=answer_text,
                citations=citations
            )
            
        except httpx.ConnectError:
            raise RuntimeError(
                f"Failed to connect to Ollama at {self.ollama_base_url}. "
                f"Please ensure Ollama is running: 'ollama serve' and model '{self.model}' is installed: 'ollama pull {self.model}'"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate answer: {str(e)}")
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into context for the LLM.
        
        Args:
            chunks: List of retrieved chunks with metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            section = chunk["section"]
            page = chunk["page"]
            text = chunk["text"]
            
            context_parts.append(
                f"[Source {idx}] (Section: {section}, Page: {page})\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for answer generation."""
        return """You are a research paper question-answering assistant. Your task is to provide accurate, factual answers based STRICTLY on the provided context from academic papers.

CRITICAL RULES:
1. ONLY use information from the provided sources
2. If the answer is not in the context, say "The provided context does not contain sufficient information to answer this question."
3. Include inline citations using [Source N] notation where N is the source number
4. Be precise and quote relevant passages when appropriate
5. Do not add information from your training data
6. Maintain academic tone and clarity
7. If multiple sources support a point, cite all relevant sources"""
    
    def _get_user_prompt(self, question: str, context: str) -> str:
        """
        Get the user prompt with question and context.
        
        Args:
            question: User's question
            context: Formatted context
            
        Returns:
            User prompt
        """
        return f"""Context from the research paper:

{context}

Question: {question}

Please provide a detailed answer based on the context above. Include inline citations [Source N] for all claims."""
    
    def _extract_citations(self, chunks: List[Dict]) -> List[Citation]:
        """
        Extract citation information from retrieved chunks.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            List of Citation objects
        """
        citations = []
        seen_citations = set()
        
        for chunk in chunks:
            citation_key = (chunk["section"], chunk["page"])
            
            if citation_key not in seen_citations:
                text_snippet = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                
                citation = Citation(
                    section=chunk["section"],
                    page=chunk["page"],
                    text_snippet=text_snippet
                )
                citations.append(citation)
                seen_citations.add(citation_key)
        
        return sorted(citations, key=lambda x: (x.page, x.section))
