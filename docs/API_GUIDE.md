# 🌐 API Guide

Complete API reference for the LinkedIn Job Information Extraction service.

---

## Quick Reference

**Base URL**: `http://localhost:8001`  
**Interactive Docs**: `http://localhost:8001/docs` (Swagger UI)  
**Alternative Docs**: `http://localhost:8001/redoc`

---

## Endpoints Overview

| Method | Endpoint | Purpose | Max Items |
|--------|----------|---------|-----------|
| GET | `/` | API information | - |
| GET | `/health` | Health check | - |
| POST | `/extract/llm` | Single LLM extraction | 1 |
| POST | `/extract/rule-based` | Single rule-based | 1 |
| POST | `/extract/spacy` | Single spaCy NER | 1 |
| POST | `/extract/hybrid` | Single hybrid | 1 |
| POST | `/extract/batch/llm` | Batch LLM extraction | 100 |
| POST | `/extract/batch/hybrid` | Batch hybrid | 100 |

---

## Request/Response Schemas

### Input Schema: LinkedInPostInput

```json
{
  "name": "string (required)",
  "about": "string (required)",
  "description": "string (required)",
  "userProfileUrl": "string (optional)",
  "source": "string (optional)",
  "searchJobTitle": "string (optional)",
  "companyLinks": ["array of strings (optional)"]
}
```

### Output Schema: LinkedInPostOutput

```json
{
  "name": "string",
  "about": "string",
  "description": "string",
  "userProfileUrl": "string",
  "source": "string",
  "searchJobTitle": "string",
  "companyLinks": ["array"],
  "jobPosterName": "string | null",
  "jobStarterName": "string | null",
  "companyName": "string | null",
  "currentRole": "string | null",
  "classification": "Relevant | Irrelevant",
  "error": "string | null"
}
```

---

## Endpoint Details

### 1. Root - API Information

**GET** `/`

**Response:**
```json
{
  "message": "LinkedIn Job Information Extraction API",
  "version": "2.0.0",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "extract_llm": "/extract/llm"
  }
}
```

---

### 2. Health Check

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "LinkedIn Job Extraction API",
  "version": "2.0.0"
}
```

---

### 3. Extract Single Post - LLM (Recommended)

**POST** `/extract/llm`

Extract using GPT-3.5 with optimized prompt (v4).

**Request:**
```json
{
  "name": "John Smith",
  "about": "HR Director | Talent Acquisition",
  "description": "Thrilled to announce Sarah Johnson has joined as CTO at TechCorp!",
  "userProfileUrl": "https://linkedin.com/in/johnsmith",
  "source": "LinkedIn",
  "searchJobTitle": "CTO",
  "companyLinks": ["https://techcorp.com"]
}
```

**Response:**
```json
{
  "name": "John Smith",
  "about": "HR Director | Talent Acquisition",
  "description": "Thrilled to announce Sarah Johnson has joined as CTO at TechCorp!",
  "userProfileUrl": "https://linkedin.com/in/johnsmith",
  "source": "LinkedIn",
  "searchJobTitle": "CTO",
  "companyLinks": ["https://techcorp.com"],
  "jobPosterName": "John Smith",
  "jobStarterName": "Sarah Johnson",
  "companyName": "TechCorp",
  "currentRole": "CTO",
  "classification": "Relevant"
}
```

**Performance:**
- Accuracy: 94.2%
- Latency: ~2.3s
- Cost: $0.0008/request

---

### 4. Extract Single Post - Rule-Based (Fast)

**POST** `/extract/rule-based`

Extract using regex patterns and keyword matching.

Same request/response format as LLM endpoint.

**Performance:**
- Accuracy: 71.6%
- Latency: ~12ms
- Cost: $0

---

### 5. Extract Single Post - spaCy NER

**POST** `/extract/spacy`

Extract using pretrained spaCy NER models.

Same request/response format as LLM endpoint.

**Performance:**
- Accuracy: 78.4%
- Latency: ~145ms
- Cost: $0

---

### 6. Extract Single Post - Hybrid (Balanced)

**POST** `/extract/hybrid`

Try spaCy first, fallback to rule-based if confidence < 0.6.

Same request/response format as LLM endpoint.

**Performance:**
- Accuracy: 79.8%
- Latency: ~82ms
- Cost: $0

---

### 7. Batch Extract - LLM

**POST** `/extract/batch/llm`

Process up to 100 posts concurrently.

**Request:**
```json
[
  {
    "name": "Person 1",
    "about": "Role 1",
    "description": "Post 1..."
  },
  {
    "name": "Person 2",
    "about": "Role 2",
    "description": "Post 2..."
  }
]
```

**Response:** Array of LinkedInPostOutput objects

**Performance:**
- Batch size: 20 (configurable via `BATCH_SIZE`)
- Throughput: ~2.4 posts/second
- Concurrent processing with async/await

**Limits:**
- Maximum 100 posts per request
- Automatic batching internally

---

### 8. Batch Extract - Hybrid

**POST** `/extract/batch/hybrid`

Process multiple posts using hybrid strategy.

Same request/response format as batch LLM endpoint.

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Empty input list"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Extraction failed: ...",
  "request_id": "123"
}
```

---

## Usage Examples

### cURL

**Single extraction:**
```bash
curl -X POST "http://localhost:8001/extract/llm" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "about": "HR Director",
    "description": "Excited to announce Sarah joined as CTO!"
  }'
```

**Batch extraction:**
```bash
curl -X POST "http://localhost:8001/extract/batch/llm" \
  -H "Content-Type: application/json" \
  -d @batch_posts.json
```

### Python

```python
import requests

# Single extraction
response = requests.post(
    "http://localhost:8001/extract/llm",
    json={
        "name": "John Smith",
        "about": "HR Director",
        "description": "Excited to announce Sarah joined as CTO!"
    }
)
result = response.json()
print(f"Extracted: {result['jobStarterName']} → {result['currentRole']}")

# Batch extraction
posts = [
    {"name": "...", "about": "...", "description": "..."},
    {"name": "...", "about": "...", "description": "..."}
]
response = requests.post(
    "http://localhost:8001/extract/batch/llm",
    json=posts
)
results = response.json()
print(f"Processed {len(results)} posts")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

// Single extraction
const result = await axios.post(
  'http://localhost:8001/extract/llm',
  {
    name: 'John Smith',
    about: 'HR Director',
    description: 'Excited to announce Sarah joined as CTO!'
  }
);
console.log(result.data);

// Batch extraction
const posts = [ /* array of posts */ ];
const results = await axios.post(
  'http://localhost:8001/extract/batch/llm',
  posts
);
console.log(`Processed ${results.data.length} posts`);
```

---

## Configuration

### Environment Variables

Customize behavior via `.env` file:

```bash
# API Settings
APP_HOST=localhost
APP_PORT=8001
BATCH_SIZE=20

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL_NAME=gpt-3.5-turbo-instruct
MODEL_TEMPERATURE=0.0
MODEL_SEED=1234
MAX_TOKENS=2048

# Retry & Timeout
MAX_RETRIES=10
TIMEOUT=30
BASE_DELAY=1

# Logging
LOG_LEVEL=INFO
```

---

## Rate Limiting & Retries

### OpenAI API Rate Limits

Rate limits depend on your OpenAI tier:
- **Tier 1**: 500 RPM, 40K TPM
- **Tier 2**: 3,500 RPM, 80K TPM
- **Tier 3+**: Higher limits

### Automatic Retry Strategy

The API implements exponential backoff:
```
Attempt 1: immediate
Attempt 2: 1s delay
Attempt 3: 2s delay
Attempt 4: 4s delay
...
Max attempts: 10
```

**Rate limit handling:**
- Detects 429 errors
- Backs off automatically
- Logs warnings
- Returns error after max retries

---

## Best Practices

### 1. Use Batch Processing
```python
# ❌ Don't: Sequential requests
for post in posts:
    requests.post("/extract/llm", json=post)

# ✅ Do: Batch request
requests.post("/extract/batch/llm", json=posts)
```
**Impact**: 5.7× faster

### 2. Handle Errors Gracefully
```python
try:
    response = requests.post("/extract/llm", json=post)
    result = response.json()
    
    if result.get("error"):
        print(f"Extraction error: {result['error']}")
    else:
        print(f"Success: {result['jobStarterName']}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### 3. Validate Input
```python
from pydantic import ValidationError
from schemas import LinkedInPostInput

try:
    validated = LinkedInPostInput(**post_data)
    response = requests.post("/extract/llm", json=validated.dict())
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### 4. Monitor Performance
```python
import time

start = time.time()
response = requests.post("/extract/llm", json=post)
latency = time.time() - start

print(f"Latency: {latency:.2f}s")
if latency > 5:
    print("Warning: High latency detected")
```

### 5. Cache Results
```python
import hashlib
import json

def cache_key(post):
    return hashlib.md5(
        json.dumps(post, sort_keys=True).encode()
    ).hexdigest()

cache = {}
key = cache_key(post)

if key in cache:
    return cache[key]
else:
    result = requests.post("/extract/llm", json=post).json()
    cache[key] = result
    return result
```

---

## Performance Tips

### Optimize Throughput

**For high volume:**
```bash
# Increase batch size
BATCH_SIZE=50

# Use multiple workers (if running with Gunicorn)
gunicorn app:app \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8001
```

**Expected:**
- 1 worker: ~2.4 posts/s
- 4 workers: ~9 posts/s
- 8 workers: ~15 posts/s

### Reduce Latency

**Use faster alternatives for simple posts:**
```python
# Try rule-based first for speed
response = requests.post("/extract/rule-based", json=post)

# If confidence low, use LLM
if response.json().get("confidence", 0) < 0.7:
    response = requests.post("/extract/llm", json=post)
```

---

## Postman Collection

Import [`postman_collection.json`](../postman_collection.json) for ready-to-use API tests.

**Collection includes:**
- All endpoint examples
- Pre-configured requests
- Test scripts
- Environment variables

**Setup:**
1. Import collection into Postman
2. Set `base_url` variable: `http://localhost:8001`
3. Run requests or entire collection

---

## Monitoring & Debugging

### Access Logs

```bash
# View logs
tail -f app.log

# Filter errors
grep "ERROR" app.log

# Watch in real-time
tail -f app.log | grep "request_id"
```

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
```

Debug logs include:
- Request parameters
- Prompt sent to OpenAI
- Response parsing
- Retry attempts
- Timing information

### Health Monitoring

```bash
# Check health every 30s
watch -n 30 'curl -s http://localhost:8001/health | jq'
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY is not set"
**Solution:**
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Issue: Rate limit errors (429)
**Solution:** Automatic retry handles this. If persistent:
```bash
# Increase retry delays
BASE_DELAY=2
MAX_RETRIES=15
```

### Issue: Slow responses
**Solution:**
```bash
# Increase timeout
TIMEOUT=60

# Or use faster endpoint
curl -X POST /extract/rule-based
```

### Issue: Empty responses
**Solution:** Check logs for validation errors:
```bash
tail -f app.log | grep "validation"
```

---

## Next Steps

- **Read [Prompt Engineering Guide](PROMPT_ENGINEERING.md)** for customization
- **Review [Evaluation Report](EVALUATION_REPORT.md)** for performance details
- **Check [Setup Guide](SETUP_GUIDE.md)** for deployment options

---

**📖 For interactive testing, visit [http://localhost:8001/docs](http://localhost:8001/docs)**