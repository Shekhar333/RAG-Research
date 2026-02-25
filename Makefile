.PHONY: help install run docker-up docker-down docker-build test clean

help:
	@echo "RAG Research Paper AI Assistant - Makefile Commands"
	@echo ""
	@echo "  make install        - Install Python dependencies"
	@echo "  make run            - Run the application locally"
	@echo "  make docker-up      - Start services with Docker Compose"
	@echo "  make docker-down    - Stop Docker Compose services"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make test           - Run API tests"
	@echo "  make clean          - Clean cache and temporary files"
	@echo "  make setup          - Initial setup (create .env from example)"

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file from .env.example"; \
		echo "⚠  Please edit .env and add your OPENAI_API_KEY"; \
	else \
		echo "✓ .env file already exists"; \
	fi
	@mkdir -p cache uploads
	@echo "✓ Created cache and uploads directories"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "✓ Services started"
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"
	@echo "  Qdrant: http://localhost:6333"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

test:
	@echo "Testing API health..."
	@curl -s http://localhost:8000/health | python -m json.tool

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf cache/* 2>/dev/null || true
	rm -rf uploads/* 2>/dev/null || true
	@echo "✓ Cleaned cache and temporary files"

format:
	black app/
	isort app/

lint:
	flake8 app/
	mypy app/
