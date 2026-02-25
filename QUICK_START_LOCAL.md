# 🚀 Quick Start - Local RAG (No API Keys!)

## ⚡ 3-Step Setup

### 1️⃣ Install Ollama
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download/windows
```

### 2️⃣ Download Llama 3
```bash
ollama pull llama3
```

### 3️⃣ Start Everything
```bash
./start-local.sh
```

**That's it!** 🎉

---

## 📋 Manual Alternative

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 3: Start Backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---
```

---
```


-----USE THE RAG-----------

--get the document_id

curl -X POST "http://localhost:8000/upload" \
  -F "file=@EJ1172284.pdf"


--give the prompt using the same documentid

curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "YOUR_DOCUMENT_ID_HERE",
    "question": "What is this paper about?",
    "top_k": 5
  }'


---

## 📚 More Info

- **Detailed Setup**: `LOCAL_RAG_SETUP.md`
- **What Changed**: `LOCAL_RAG_SUMMARY.md`
- **Troubleshooting**: Both files above have detailed sections

---

**Everything runs 100% locally - No API keys needed! 🎊**
