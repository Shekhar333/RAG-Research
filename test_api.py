#!/usr/bin/env python3
"""
Test script for the RAG Research Paper AI Assistant API.

Usage:
    python test_api.py path/to/paper.pdf "Your question here"
"""

import sys
import requests
import json
from pathlib import Path


API_BASE_URL = "http://localhost:8000"


def upload_document(pdf_path: str) -> str:
    """Upload a PDF document and return the document ID."""
    print(f"Uploading document: {pdf_path}")
    
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        response = requests.post(
            f"{API_BASE_URL}/upload",
            files={"file": f}
        )
    
    if response.status_code != 201:
        raise Exception(f"Upload failed: {response.text}")
    
    data = response.json()
    document_id = data["document_id"]
    print(f"✓ Document uploaded successfully")
    print(f"  Document ID: {document_id}")
    print(f"  Status: {data['status']}")
    return document_id


def query_document(document_id: str, question: str, top_k: int = 5):
    """Query a document with a question."""
    print(f"\nQuerying document: {document_id}")
    print(f"Question: {question}")
    
    response = requests.post(
        f"{API_BASE_URL}/query",
        json={
            "document_id": document_id,
            "question": question,
            "top_k": top_k
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.text}")
    
    data = response.json()
    
    print("\n" + "="*80)
    print("ANSWER")
    print("="*80)
    print(data["answer"])
    
    if data["citations"]:
        print("\n" + "="*80)
        print("CITATIONS")
        print("="*80)
        for i, citation in enumerate(data["citations"], 1):
            print(f"\n[{i}] Section: {citation['section']}, Page: {citation['page']}")
            print(f"    Snippet: {citation['text_snippet'][:150]}...")
    else:
        print("\n(No citations available)")
    
    print("\n" + "="*80)


def check_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API is healthy and running")
            return True
        else:
            print(f"✗ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to API: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("Usage: python test_api.py <pdf_path> <question> [top_k]")
        print("\nExample:")
        print('  python test_api.py paper.pdf "What is the main contribution?"')
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    question = sys.argv[2]
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    print("RAG Research Paper AI Assistant - Test Script")
    print("="*80)
    
    if not check_health():
        print("\nPlease ensure the API is running:")
        print("  docker-compose up")
        print("  OR")
        print("  uvicorn app.main:app --reload")
        sys.exit(1)
    
    try:
        document_id = upload_document(pdf_path)
        query_document(document_id, question, top_k)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
