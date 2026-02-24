# RAG Research Paper AI Assistant

A production-ready FastAPI application implementing a Retrieval-Augmented Generation (RAG) system for research paper question answering with strict citation support.

## Features

- **PDF Processing**: Robust PDF parsing with section detection and metadata extraction
- **Smart Chunking**: Token-based chunking with overlap for context preservation
- **Embedding Caching**: Efficient embedding generation with disk-based caching
- **Vector Search**: Fast similarity search using Qdrant vector database
- **Citation-Aware Answers**: LLM-generated answers with section and page citations
- **Production-Ready**: Async FastAPI, Docker support, comprehensive error handling
- **Deterministic Outputs**: Temperature=0 for consistent, reproducible answers

## Architecture

```
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
┌─────────────────┐
│   Embeddings    │  (OpenAI + Cache)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Vector Store   │  (Qdrant)
└─────────────────┘

Query Flow:
┌─────────────┐
│    Query    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Query Embed    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Vector Search   │  (Cosine similarity)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   LLM Answer    │  (GPT-4 + Citations)
└─────────────────┘
```

## System Requirements

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- OpenAI API Key
- 4GB RAM minimum
- 10GB disk space

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd RAG-Reseach
```

### 2. Environment Configuration

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Run with Docker Compose (Recommended)

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### 4. Alternative: Local Development Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Qdrant (in separate terminal)
docker run -p 6333:6333 qdrant/qdrant

# Run the application
uvicorn app.main:app --reload
```

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
- Processing timeout: 8 seconds

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
| `OPENAI_API_KEY` | OpenAI API key | **Required** |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Chat model for answers | `gpt-4-turbo-preview` |
| `QDRANT_HOST` | Qdrant host | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `QDRANT_COLLECTION_NAME` | Collection name | `research_papers` |
| `MAX_PDF_SIZE_MB` | Max PDF size in MB | `20` |
| `MAX_QUERY_LATENCY_SECONDS` | Query timeout | `8` |
| `CHUNK_SIZE` | Tokens per chunk | `500` |
| `CHUNK_OVERLAP` | Overlap tokens | `100` |
| `TOP_K_RETRIEVAL` | Default retrieval count | `5` |
| `SIMILARITY_THRESHOLD` | Min similarity score | `0.75` |
| `LLM_TEMPERATURE` | LLM temperature | `0` |
| `CACHE_DIR` | Embedding cache directory | `./cache` |

## Project Structure

```
RAG-Reseach/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py      # PDF parsing & section detection
│   │   ├── chunker.py             # Text chunking with overlap
│   │   ├── embeddings.py          # Embedding generation & caching
│   │   ├── vector_store.py        # Qdrant integration
│   │   ├── answer_generator.py    # LLM answer generation
│   │   └── rag_service.py         # RAG pipeline orchestration
│   ├── utils/
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py                    # FastAPI application
├── cache/                         # Embedding cache (auto-created)
├── uploads/                       # Temporary upload storage
├── .env                           # Environment variables (create from .env.example)
├── .env.example                   # Environment template
├── .gitignore
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Docker image definition
├── requirements.txt               # Python dependencies
└── README.md
```

## Technical Details

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

- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Caching**: SHA-256 hash-based disk cache using `diskcache`
- **Batching**: Efficient batch processing for multiple chunks
- **Performance**: Reuses cached embeddings for duplicate uploads

### Vector Store

- **Database**: Qdrant (local or clustered)
- **Similarity**: Cosine distance
- **Indexing**: O(log n) HNSW algorithm
- **Filtering**: Document-specific queries via metadata filters
- **Threshold**: Configurable minimum similarity score (default: 0.75)

### Answer Generation

- **Model**: GPT-4 Turbo
- **Temperature**: 0 (deterministic outputs)
- **Prompt Engineering**: Strict grounding rules with citation enforcement
- **Citations**: Automatic extraction of section and page references
- **Fallback**: Returns "Insufficient information" if no relevant chunks found

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

### Testing with Python

```python
import requests

# Upload
with open("paper.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Query
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

## Performance Optimization

### Embedding Cache

Embeddings are cached to avoid recomputation:
- Cache key: `embedding:{model}:{text_hash}`
- Storage: Disk-based persistent cache
- Benefit: 10-100x speedup for duplicate content

### Async Operations

All I/O operations are async:
- OpenAI API calls
- Vector database operations
- File processing

### Vector Search

Qdrant uses HNSW indexing for efficient similarity search:
- Time complexity: O(log n)
- Space complexity: O(n)
- Recommended for 10K+ documents

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
        - secretRef:
            name: rag-secrets
        ports:
        - containerPort: 8000
```

### Environment Variables for Production

Create a `rag-secrets` secret:
```bash
kubectl create secret generic rag-secrets \
  --from-literal=OPENAI_API_KEY=your-key-here
```

## Troubleshooting

### Common Issues

**1. Qdrant Connection Error**
```
Error: Could not connect to Qdrant
```
Solution: Ensure Qdrant is running on specified host/port:
```bash
docker ps | grep qdrant
```

**2. OpenAI API Error**
```
Error: Invalid API key
```
Solution: Check `.env` file contains valid `OPENAI_API_KEY`

**3. PDF Processing Failed**
```
Error: Failed to process PDF
```
Solution: Ensure PDF is not corrupted and under 20MB

**4. Insufficient Information Response**

If you frequently get "Insufficient information", try:
- Increase `top_k` parameter (up to 20)
- Lower `SIMILARITY_THRESHOLD` in `.env` (e.g., 0.6)
- Rephrase the question to match document terminology

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics to Monitor

- Upload success rate
- Query latency (target: < 8 seconds)
- Cache hit rate
- Vector database size
- API error rates

## Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **File Uploads**: Validate file types and sizes
- **Rate Limiting**: Consider adding rate limiting for production
- **Authentication**: Add authentication layer for production use
- **HTTPS**: Use HTTPS in production environments

## Scalability

### Horizontal Scaling

- FastAPI app can be scaled across multiple instances
- Qdrant supports clustering for distributed vector search
- Stateless design enables load balancing

### Vertical Scaling

- Increase RAM for larger embedding cache
- GPU acceleration for embedding generation (future optimization)

## Future Enhancements

- [ ] Multi-document querying
- [ ] Document management (list, delete operations)
- [ ] Streaming responses for long answers
- [ ] Support for other document formats (DOCX, TXT)
- [ ] Advanced citation formatting (BibTeX, APA)
- [ ] User authentication and authorization
- [ ] Rate limiting and usage quotas
- [ ] Observability with Prometheus/Grafana

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

**Built with**: FastAPI, OpenAI, Qdrant, PyMuPDF, and modern async Python
