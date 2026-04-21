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


Aquí tienes la traducción al español de la referencia de la API, manteniendo los ejemplos de código en su formato original.

---

## Referencia de la API

### Endpoints

#### POST /chat
- **Puerto:** 3000
- **Descripción:** Endpoint para el chat.

**Ejemplo: Python**
```python
import requests

url = 'http://localhost:3000/chat'
response = requests.post(url, json={'message': 'Hola'})
print(response.json())
```

**Ejemplo: JavaScript**
```javascript
fetch('http://localhost:3000/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: 'Hola' })
})
.then(response => response.json())
.then(data => console.log(data));
```

**Ejemplo: cURL**
```bash
curl -X POST http://localhost:3000/chat -H 'Content-Type: application/json' -d '{"message": "Hola"}'
```

---

#### POST /infer
- **Puerto:** 5002
- **Descripción:** Endpoint para inferencia.

---

#### POST /process
- **Puerto:** 5003
- **Descripción:** Endpoint para procesamiento.

---

#### POST /generate
- **Puerto:** 5004
- **Descripción:** Endpoint para generación.

---

#### GET /health
- **Descripción:** Endpoint de verificación de estado.

---

### Códigos de Respuesta HTTP

- **200 OK**: Respuesta exitosa.
- **400 Bad Request**: Solicitud no válida.
- **404 Not Found**: Endpoint no encontrado.
- **500 Internal Server Error**: Error interno del servidor.

---

*Este documento proporciona una referencia completa de los endpoints de la API definidos para el proyecto ARKHAN Community.*
- **400 Bad Request**: Invalid request.
- **404 Not Found**: Endpoint not found.
- **500 Internal Server Error**: Server error.

---

This document provides a complete reference for the API endpoints defined for the ARKHAN Community project.
