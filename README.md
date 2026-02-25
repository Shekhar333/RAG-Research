# RAG Research Paper AI Assistant

A production-ready FastAPI application implementing a **fully local** Retrieval-Augmented Generation (RAG) system for research paper question answering with strict citation support.

## Architecture


Upload Flow:
┌─────────────┐
│   PDF Upload │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  PDF Processing │  (PyMuPDF)
│  + Section      │
│    Detection    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Text Chunking  │  (500 tokens, 100 overlap)
└──────┬──────────┘
       │
       ▼
┌─────────────────────────────┐
│   Local Embeddings          │
│   sentence-transformers     │
│   (all-MiniLM-L6-v2)       │
│   + Disk Cache              │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────┐
│  Vector Store   │  (Qdrant - 384 dim)
└─────────────────┘

Query Flow:
┌─────────────┐
│    Query    │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  Query Embedding     │  (sentence-transformers)
└──────┬───────────────┘
       │
       ▼
┌─────────────────┐
│ Vector Search   │  (Cosine similarity)
└──────┬──────────┘
       │
       ▼
┌──────────────────────┐
│   Local LLM          │
│   Ollama (Llama 3)   │
│   + Citations        │
└──────────────────────┘
```

## System Requirements

- Python 3.11+
- Docker (for Qdrant)
- **Ollama** (for local LLM) - [Download here](https://ollama.com/)
- **No API Keys Required** 🎉
- 8GB RAM minimum (16GB recommended)
- 15GB disk space (for models)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RAG-Reseach
```

### 2. Install Ollama and Download Llama 3

**macOS:**
```bash
brew install ollama
ollama pull llama3
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```

**Windows:** Download from [ollama.com](https://ollama.com/download/windows)

### 3. Quick Start with Automated Script (Recommended)

```bash
# Run the automated setup script
./start-local.sh
```

This will:
- Check prerequisites
- Install Python dependencies
- Start Ollama and Qdrant
- Launch the backend

### 4. Alternative: Manual Setup

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 3: Start Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the application is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Endpoints

#### 1. Upload Document

**POST** `/upload`

Upload and index a research paper PDF.

**Request:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@paper.pdf"
```

**Response:**
```json
{
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "indexed"
}
```

**Constraints:**
- Maximum file size: 20MB
- Format: PDF only
- Processing timeout: 60 seconds (local model loading)

#### 2. Query Document

**POST** `/query`

Ask questions about an indexed document.

**Request:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "123e4567-e89b-12d3-a456-426614174000",
    "question": "What is the main contribution of this paper?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "answer": "The main contribution is... [Source 1] [Source 2]",
  "citations": [
    {
      "section": "Introduction",
      "page": 2,
      "text_snippet": "We propose a novel approach..."
    },
    {
      "section": "Methodology",
      "page": 5,
      "text_snippet": "Our method consists of..."
    }
  ]
}
```

**Parameters:**
- `document_id` (required): UUID from upload response
- `question` (required): Natural language question
- `top_k` (optional): Number of chunks to retrieve (1-20, default: 5)

**Edge Cases:**

If no relevant information is found:
```json
{
  "answer": "Insufficient information in the document.",
  "citations": []
}
```

#### 3. Health Check

**GET** `/health`

Check service health status.

```bash
curl http://localhost:8000/health
```

## Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | Local embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| `EMBEDDING_DIMENSION` | Embedding vector size | `384` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM model name | `llama3` |
| `LLM_TEMPERATURE` | LLM temperature | `0` |
| `QDRANT_HOST` | Qdrant host | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `QDRANT_COLLECTION_NAME` | Collection name | `research_papers` |
| `MAX_PDF_SIZE_MB` | Max PDF size in MB | `20` |
| `MAX_QUERY_LATENCY_SECONDS` | Query timeout | `60` |
| `CHUNK_SIZE` | Tokens per chunk | `500` |
| `CHUNK_OVERLAP` | Overlap tokens | `100` |
| `TOP_K_RETRIEVAL` | Default retrieval count | `5` |
| `SIMILARITY_THRESHOLD` | Min similarity score | `0.1` |
| `CACHE_DIR` | Embedding cache directory | `./cache` |

**Note**: No API keys required! Everything runs locally.

## Project Structure

```
RAG-Reseach/
├── app/                           # Backend (FastAPI)
│   ├── core/
│   │   └── config.py              # Configuration management
│   ├── models/
│   │   └── schemas.py             # Pydantic models
│   ├── services/
│   │   ├── pdf_processor.py       # PDF parsing & section detection
│   │   ├── chunker.py             # Text chunking with overlap
│   │   ├── embeddings.py          # Local sentence-transformers embeddings
│   │   ├── vector_store.py        # Qdrant integration
│   │   ├── answer_generator.py    # Ollama/Llama 3 (local)
│   │   └── rag_service.py         # RAG pipeline orchestration
│   └── main.py                    # FastAPI application
│
├── cache/                         # Embedding cache (created at runtime)
├── uploads/                       # Temporary upload storage (created at runtime)
├── .env                           # Environment variables (optional, from example)
├── .env.example                   # Environment template
├── docker-compose.yml             # Backend + Qdrant
├── Dockerfile                     # Backend Docker image
├── requirements.txt               # Python dependencies
├── start-local.sh                 # Automated local setup script
├── QUICK_START_LOCAL.md           # Quick local setup guide
├── PROJECT_SUMMARY.md             # High-level backend summary
├── Makefile                       # Helper commands
└── README.md                      # This file
```

## Why Local RAG?

| Aspect | Local (This System) | Cloud (OpenAI) |
|--------|-------------------|----------------|
| **Cost** | $0 (Free forever) | $0.10-0.50 per PDF |
| **Privacy** | 100% local | Data sent to API |
| **API Keys** | None needed | Required |
| **Speed** | Medium (2-5s queries) | Fast (<1s queries) |
| **Quality** | Good | Excellent |
| **Offline** | Yes (after setup) | No |
| **Limits** | Unlimited | Rate limits apply |
| **Setup** | 20 min (first time) | 2 min |

**Best for**: Research, sensitive data, offline environments, learning, unlimited usage

## Technical Details

### Local AI Stack

- **Embeddings**: sentence-transformers (HuggingFace) - all-MiniLM-L6-v2
- **LLM**: Llama 3 (8B parameters) via Ollama
- **Vector DB**: Qdrant (local or cloud)
- **Cost**: $0 (completely free)
- **Privacy**: 100% local, offline capable after model downloads

### PDF Processing

- **Library**: PyMuPDF (fitz)
- **Section Detection**: Pattern-based regex matching for common academic formats
- **Fallback**: Sections default to "Unknown" if detection fails
- **Metadata**: Extracts page numbers, section names, and text content

### Chunking Strategy

- **Method**: Token-based splitting using `tiktoken`
- **Size**: 500 tokens per chunk
- **Overlap**: 100 tokens between chunks
- **Encoding**: `cl100k_base` (OpenAI standard)
- **Preservation**: Maintains document_id, section, page, and chunk_index metadata

### Embeddings

- **Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, local)
- **Caching**: SHA-256 hash-based disk cache using `diskcache`
- **Batching**: Efficient batch processing for multiple chunks
- **Performance**: Reuses cached embeddings for duplicate uploads
- **Inference**: Runs locally on CPU (~10ms per chunk)

### Vector Store

- **Database**: Qdrant (local or clustered)
- **Similarity**: Cosine distance
- **Indexing**: O(log n) HNSW algorithm
- **Filtering**: Document-specific queries via metadata filters
- **Dimension**: 384 (optimized for sentence-transformers)
- **Threshold**: Configurable minimum similarity score (default: 0.1 for local models)

### Answer Generation

- **Model**: Llama 3 (8B parameters) via Ollama (local)
- **Temperature**: 0 (deterministic outputs)
- **Prompt Engineering**: Strict grounding rules with citation enforcement
- **Citations**: Automatic extraction of section and page references
- **Fallback**: Returns "Insufficient information" if no relevant chunks found
- **Privacy**: All processing happens locally, data never leaves your machine

### Error Handling

- **Validation**: PDF format and size checks before processing
- **Timeouts**: Configurable timeouts for upload and query operations
- **HTTP Status Codes**:
  - `400`: Invalid input (bad PDF, missing fields)
  - `404`: Document not found
  - `408`: Request timeout
  - `500`: Internal server error

## Testing

### Manual Testing with cURL

1. **Upload a document:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample_paper.pdf"
```

2. **Query the document:**
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_DOCUMENT_ID",
    "question": "What is the methodology used in this research?"
  }'
```

#### Testing with Python

Use the included test script:

```bash
python test_api.py your_paper.pdf "What is this paper about?"
```

Or manually:

```python
import requests

# Upload
with open("paper.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]
    print(f"Document ID: {doc_id}")

# Query (first query may take 10-30 seconds as Llama 3 loads)
response = requests.post(
    "http://localhost:8000/query",
    json={
        "document_id": doc_id,
        "question": "What are the main findings?",
        "top_k": 5
    }
)
print(response.json())
```

**Note**: The first query takes 10-30 seconds as the LLM loads. Subsequent queries are much faster (2-5 seconds).

## Performance Optimization

### Embedding Cache

Embeddings are cached to avoid recomputation:
- Cache key: `embedding:{model}:{text_hash}`
- Storage: Disk-based persistent cache
- Benefit: 10-100x speedup for duplicate content
- Location: `./cache` directory

### Async Operations

All I/O operations are async:
- Ollama LLM calls (local HTTP)
- Vector database operations
- File processing
- Embedding generation

### Vector Search

Qdrant uses HNSW indexing for efficient similarity search:
- Time complexity: O(log n)
- Space complexity: O(n)
- Recommended for 10K+ documents

### Local Model Performance

- **Embedding generation**: ~10-50ms per chunk (CPU)
- **First LLM query**: 10-30 seconds (model loading)
- **Subsequent queries**: 2-5 seconds
- **Upload processing**: 5-15 seconds (10-30 page paper)

## Production Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Kubernetes (Example)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: rag-config
data:
  QDRANT_HOST: "qdrant-service"
  QDRANT_PORT: "6333"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-app
  template:
    metadata:
      labels:
        app: rag-app
    spec:
      containers:
      - name: rag-app
        image: rag-app:latest
        envFrom:
        - configMapRef:
            name: rag-config
        ports:
        - containerPort: 8000
```

## Troubleshooting

### Common Issues

**1. "Failed to connect to Ollama"**
```
Error: Failed to connect to Ollama
```
Solution: Ensure Ollama is running:
```bash
ollama serve
# Verify: curl http://localhost:11434/api/tags
```

**2. "Model not found"**
```
Error: Model 'llama3' not found
```
Solution: Download the model:
```bash
ollama pull llama3
```

**3. Qdrant Connection Error**
```
Error: Could not connect to Qdrant
```
Solution: Ensure Qdrant is running:
```bash
docker ps | grep qdrant
# Start if not running: docker run -p 6333:6333 qdrant/qdrant
```

**4. PDF Processing Failed**
```
Error: Failed to process PDF
```
Solution: Ensure PDF is not corrupted and under 20MB

**5. Query Timeout (408)**
```
Error: Query processing exceeded timeout
```
Solution: This is normal for the **first query** as Ollama loads the model. Wait 10-30 seconds and try again. Subsequent queries will be faster (2-5 seconds).

**6. Insufficient Information Response**

If you frequently get "Insufficient information", try:
- Increase `top_k` parameter (up to 20)
- Lower `SIMILARITY_THRESHOLD` in `.env` (default: 0.1 for local models)
- Rephrase the question to match document terminology
- Check that similarity scores in logs are reasonable

**7. "Retrieved 0 chunks"**

Solution: Make sure you're using the correct `document_id` from the upload response

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics to Monitor

- Upload success rate
- Query latency (first: 10-30s, subsequent: 2-5s)
- Cache hit rate
- Vector database size
- Ollama response times
- Embedding generation speed

## Security Considerations

- **No API Keys**: No risk of API key leakage
- **Local Processing**: Data never leaves your machine
- **File Uploads**: Validate file types and sizes
- **Rate Limiting**: Consider adding rate limiting for production
- **Authentication**: Add authentication layer for production use
- **HTTPS**: Use HTTPS in production environments
- **Privacy**: Perfect for sensitive research data

## Scalability

### Horizontal Scaling

- FastAPI app can be scaled across multiple instances
- Qdrant supports clustering for distributed vector search
- Stateless design enables load balancing

### Vertical Scaling

- Increase RAM for larger embedding cache
- GPU acceleration for embedding generation (future optimization)

## Alternative Models

### Try Different Embedding Models

Edit `.env` and change:

```env
# Faster, smaller
EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2
EMBEDDING_DIMENSION=384

# Better quality (recommended)
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
EMBEDDING_DIMENSION=768
```

**Note**: After changing embedding model, delete Qdrant data and cache:
```bash
docker stop $(docker ps -q --filter ancestor=qdrant/qdrant)
rm -rf cache/*
```

### Try Different LLMs

```bash
# Smaller, faster
ollama pull mistral    # 7B parameters
ollama pull phi3       # 3.8B parameters

# Larger, better quality
ollama pull llama3.1   # Llama 3.1
ollama pull mixtral    # 8x7B MoE
```

Update `.env`: `OLLAMA_MODEL=mistral`

## Future Enhancements

- [ ] Multi-document querying
- [ ] Document management (list, delete operations)
- [ ] Streaming responses for long answers
- [ ] Support for other document formats (DOCX, TXT)
- [ ] Advanced citation formatting (BibTeX, APA)
- [ ] User authentication and authorization
- [ ] Rate limiting and usage quotas
- [ ] Observability with Prometheus/Grafana
- [ ] GPU acceleration for embeddings
- [ ] Switch between local/cloud models

## License

MIT License

## Support

For issues and questions:
- Create an issue in the repository
- Check the API documentation at `/docs`
- Review logs for error details

## Contributors

Backend Engineering Team

---

**Built with**: FastAPI, Ollama (Llama 3), sentence-transformers, Qdrant, PyMuPDF, Next.js, React, and modern async Python

**🔒 Privacy-First**: 100% local processing, no data sent to external APIs, no API keys required!

---

## 🎓 Learning Resources

- **Ollama**: https://ollama.com/docs
- **sentence-transformers**: https://www.sbert.net/
- **Llama 3**: https://ollama.com/library/llama3
- **Qdrant**: https://qdrant.tech/documentation/
- **FastAPI**: https://fastapi.tiangolo.com/

## 📖 Additional Documentation

- [QUICK_START_LOCAL.md](QUICK_START_LOCAL.md) - 3-step local quick start
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - High-level backend implementation summary

---

**Version**: 2.0.0 (Local Edition)  
**Last Updated**: 2026-02-24  
**License**: MIT
