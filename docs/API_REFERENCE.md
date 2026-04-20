# API Reference

## Endpoints

### POST /chat
- **Port**: 3000
- **Description**: Endpoint for chat.

#### Example: Python
```python
import requests

url = 'http://localhost:3000/chat'
response = requests.post(url, json={'message': 'Hello'})
print(response.json())
```

#### Example: JavaScript
```javascript
fetch('http://localhost:3000/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: 'Hello' })
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Example: cURL
```bash
curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{"message": "Hello"}'
```

### POST /infer
- **Port**: 5002
- **Description**: Endpoint for inference.

### POST /process
- **Port**: 5003
- **Description**: Endpoint for processing.

### POST /generate
- **Port**: 5004
- **Description**: Endpoint for generation.

### GET /health
- **Description**: Health check endpoint.

## HTTP Response Codes
- **200 OK**: Successful response.
- **400 Bad Request**: Invalid request.
- **404 Not Found**: Endpoint not found.
- **500 Internal Server Error**: Server error.

---

This document provides a complete reference for the API endpoints defined for the ARKHAN Community project.