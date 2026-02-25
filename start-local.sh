#!/bin/bash

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              RAG Research Assistant - Local Setup (No API Keys!)             ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS:   brew install ollama  OR  download from https://ollama.com"
    echo "  Linux:   curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: https://ollama.com/download/windows"
    echo ""
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama server is not running"
    echo ""
    echo "Starting Ollama server in the background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
    
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama server started"
    else
        echo "❌ Failed to start Ollama server"
        echo "Please run manually: ollama serve"
        exit 1
    fi
else
    echo "✅ Ollama server is running"
fi

# Check if llama3 model is downloaded
if ! ollama list | grep -q "llama3"; then
    echo "⚠️  Llama 3 model not found"
    echo ""
    echo "Downloading Llama 3 model (~4.7GB)..."
    echo "This may take 5-15 minutes depending on your internet connection."
    echo ""
    ollama pull llama3
    
    if [ $? -eq 0 ]; then
        echo "✅ Llama 3 model downloaded successfully"
    else
        echo "❌ Failed to download Llama 3 model"
        exit 1
    fi
else
    echo "✅ Llama 3 model is installed"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if Python venv exists
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo ""
echo "Installing/updating Python dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                         Starting Services                                    ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Qdrant is already running
if curl -s http://localhost:6333/ > /dev/null 2>&1; then
    echo "✅ Qdrant is already running"
else
    echo "Starting Qdrant..."
    docker run -d -p 6333:6333 -p 6334:6334 --name rag-qdrant qdrant/qdrant > /dev/null 2>&1 || {
        echo "Qdrant container exists, starting it..."
        docker start rag-qdrant > /dev/null 2>&1
    }
    
    # Wait for Qdrant to be ready
    echo "Waiting for Qdrant to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/ > /dev/null 2>&1; then
            echo "✅ Qdrant is running"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                            🎉 Ready to Start! 🎉                             ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "All prerequisites are met! Starting the backend..."
echo ""
echo "Services running:"
echo "  • Ollama:  http://localhost:11434"
echo "  • Qdrant:  http://localhost:6333"
echo ""
echo "Starting FastAPI backend..."
echo ""

# Start the backend
uvicorn app.main:app --reload

# Cleanup on exit
trap "echo ''; echo 'Shutting down...'; docker stop rag-qdrant > /dev/null 2>&1" EXIT
