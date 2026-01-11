# AI-Powered Category Generation - Setup Guide

## Overview

The finance app includes an AI-powered category generation feature that analyzes transaction descriptions and types (income/expense) to automatically suggest and create relevant categories.

## Prerequisites

- Docker and Docker Compose installed
- Ollama service running (included in docker-compose.yml)
- An Ollama model pulled (e.g., gemma2, llama3, mistral)

## Setup Instructions

### Option 1: Using Docker Compose (Recommended)

The Ollama service is already configured in `docker-compose.yml`. You just need to pull a model.

#### 1. Pull a Model

Choose one of these models (smaller is faster):

```bash
# Small and fast (recommended for development)
docker compose exec ollama ollama pull gemma2:2b

# Medium size, good balance
docker compose exec ollama ollama pull gemma2

# Larger, more capable
docker compose exec ollama ollama pull llama3
```

**Note:** If you encounter certificate errors, you may need to:
- Use a different network
- Configure proxy settings
- Or manually download the model

#### 2. Verify Model is Available

```bash
docker compose exec ollama ollama list
```

You should see your model listed.

#### 3. Configure Environment Variables

Update `deploy/.env.example` or set environment variables:

```bash
# Ollama configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=gemma2  # or llama3, mistral, etc.
```

#### 4. Test the Feature

From Django admin:
1. Go to Users or Bank Accounts
2. Select a user with transactions
3. Choose "🤖 Generate categories" action
4. Check Celery logs for progress

### Option 2: Using Local Ollama

If you prefer to run Ollama locally:

#### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

#### 2. Start Ollama Service

```bash
ollama serve
```

#### 3. Pull a Model

```bash
ollama pull gemma2
```

#### 4. Configure Environment

```bash
OLLAMA_HOST=http://host.docker.internal:11434  # For Docker to access host
OLLAMA_MODEL=gemma2
```

### Option 3: Without AI (Pattern-Based Only)

If Ollama is not available or you don't want to use AI, the system will automatically fall back to pattern-based category suggestions.

No configuration needed - it just works! The pattern-based system uses keyword matching across 10 predefined categories with support for English and German.

## How It Works

### With AI Enhancement

1. **Pattern Analysis**: System analyzes transactions using keyword matching
   - Identifies: Groceries, Restaurants, Transportation, Shopping, Entertainment, etc.
   - Requires min 3 transactions per category
   
2. **AI Enhancement**: Ollama analyzes transaction samples
   - Reviews up to 50 transaction descriptions
   - Considers income vs expense indicators
   - Generates 5-10 intelligent suggestions
   - Provides reasons for each suggestion

3. **Smart Merging**: Combines both approaches
   - Pattern-based (high confidence, 0.85+)
   - AI-generated (medium-high confidence, 0.75)
   - Removes duplicates

4. **Auto-Creation**: Categories with confidence > 0.7 are created automatically

### Without AI (Fallback)

- Uses only pattern-based keyword matching
- 10 predefined categories with multilingual support
- Still creates categories automatically
- Confidence based on transaction frequency

## Troubleshooting

### Issue: "Model not found" (404 error)

**Solution:**
```bash
# Pull the model
docker compose exec ollama ollama pull gemma2

# Or use a different model
export OLLAMA_MODEL=llama3
docker compose exec ollama ollama pull llama3
```

### Issue: "Cannot connect to Ollama"

**Solution:**
```bash
# Check if Ollama is running
docker compose ps ollama

# Restart Ollama
docker compose restart ollama

# Check logs
docker compose logs ollama
```

### Issue: TLS certificate errors when pulling models

**Solution:**
```bash
# Try a smaller model
docker compose exec ollama ollama pull gemma2:2b

# Or use local Ollama instead (see Option 2 above)
```

### Issue: Slow performance

**Solution:**
- Use a smaller model (gemma2:2b instead of gemma2)
- Reduce the number of transaction samples (edit category_generator.py)
- Use pattern-based only (no AI)

## API Endpoints

### Generate Categories (Async)
```bash
POST /api/ai/generate-categories/
Content-Type: application/json

{
  "auto_approve": true
}
```

### Get Suggestions (Sync)
```bash
GET /api/ai/category-suggestions/
```

### Create from Suggestions
```bash
POST /api/ai/category-suggestions/
Content-Type: application/json

{
  "suggestions": [
    {"name": "Groceries", "color": "#22c55e"},
    {"name": "Transport", "color": "#3b82f6"}
  ]
}
```

## Performance Tips

1. **Model Size**: Smaller models are faster
   - gemma2:2b (2GB) - Fast
   - gemma2 (4.8GB) - Balanced
   - llama3 (4.7GB) - Capable

2. **Batch Processing**: Use async endpoint for multiple users
   ```python
   from finance_project.apps.ai.tasks import generate_categories_task
   for user_id in user_ids:
       generate_categories_task.delay(user_id, auto_approve=True)
   ```

3. **Graceful Degradation**: The system works fine without AI
   - Pattern-based suggestions still provide good results
   - No need to wait for AI if it's slow or unavailable

## Logs

Check Celery worker logs for detailed information:

```bash
docker compose logs -f celery-worker
```

Look for:
- `Starting AI-powered category generation for user_id=X`
- `Using Ollama at http://ollama:11434 with model gemma2`
- `Generated X category suggestions`
- `Auto-created X categories`

## Support

If AI is not working:
- The system automatically falls back to pattern-based suggestions
- You'll see a WARNING in logs: "AI enhancement failed, using pattern-based suggestions"
- This is expected and normal if Ollama is not configured
- Categories will still be created successfully!

