# Docker Deployment Guide

## Quick Start

### 1. Build and start all services

```bash
docker-compose up -d
```

This will start:
- **Redis** (port 6379) - Message broker and result backend
- **API Server** (port 3000) - FastAPI application
- **Celery Worker** - Background task processor
- **Flower** (port 5555) - Celery monitoring dashboard
- **Streamlit UI** (port 8501) - Interactive web interface

### 2. Access the services

- **API Documentation**: http://localhost:3000/docs
- **Flower Dashboard**: http://localhost:5555
- **Streamlit UI**: http://localhost:8501

### 3. Stop all services

```bash
docker-compose down
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
TESSERACT_PATH=tesseract
POPPLER_PATH=
HOST=0.0.0.0
PORT=3000
RELOAD=False
ALLOWED_ORIGINS=*

# Redis/Celery (auto-configured in docker-compose)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Using Async Endpoints

### Submit async OCR task

```bash
curl -X POST "http://localhost:3000/api/async/ocr/image" \
  -F "file=@document.jpg"
```

Response:
```json
{
  "success": true,
  "task_id": "abc123-def456-...",
  "message": "OCR task submitted for document.jpg"
}
```

### Check task status

```bash
curl "http://localhost:3000/api/async/status/abc123-def456-..."
```

Response:
```json
{
  "task_id": "abc123-def456-...",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "filename": "document.jpg",
    "result": {
      "text": "Extracted text..."
    }
  }
}
```

## Monitoring with Flower

Access Flower dashboard at http://localhost:5555 to:
- View active/completed tasks
- Monitor worker status
- See task execution times
- Inspect task results

## Scaling Workers

Scale Celery workers horizontally:

```bash
docker-compose up -d --scale celery-worker=4
```

## Logs

View logs for specific services:

```bash
# API server logs
docker-compose logs -f api

# Celery worker logs
docker-compose logs -f celery-worker

# All logs
docker-compose logs -f
```

## Development Mode

For development with auto-reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## Production Deployment

1. Set `RELOAD=False` in `.env`
2. Configure specific `ALLOWED_ORIGINS`
3. Use production-grade Redis with persistence
4. Set up reverse proxy (nginx) for API
5. Enable HTTPS
6. Configure resource limits in docker-compose.yml

## Troubleshooting

### Redis connection errors

Check Redis is running:
```bash
docker-compose ps redis
```

### Celery worker not processing tasks

Check worker logs:
```bash
docker-compose logs celery-worker
```

Restart worker:
```bash
docker-compose restart celery-worker
```

### Out of memory

Increase Docker memory limits or reduce worker concurrency in docker-compose.yml:
```yaml
command: celery -A core.celery_tasks worker --loglevel=info --concurrency=1
```
