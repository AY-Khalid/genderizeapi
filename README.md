# Gender Classification API

A lightweight REST API that predicts the gender of a given name using the [Genderize.io](https://genderize.io) API. Built with FastAPI and deployed on Railway.

**Author:** Anidu Yakubu Khalid  
**Internship:** HNG Backend Stage 0

---

## Live URL

```
https://genderizeapi-production-bde5.up.railway.app/api/classify?name={name}
```

---

## Tech Stack

- **Python 3.13**
- **FastAPI** — web framework
- **Uvicorn** — ASGI server
- **HTTPX** — async HTTP client for calling Genderize.io
- **Railway** — deployment platform

---

## Project Structure

```
backend/
├── app.py           # Main application
├── Procfile         # Railway process configuration
└── requirements.txt # Python dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name/backend
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server locally**

   ```bash
   uvicorn app:app --reload
   ```

   The API will be available at `http://localhost:8000`.

---

## API Reference

### `GET /api/classify`

Classifies the gender of a given name.

#### Query Parameters

| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| `name`    | string | Yes      | The name to classify |

#### Example Request

```bash
curl "http://localhost:8000/api/classify?name=khalid"
```

#### Success Response `200`

```json
{
  "status": "success",
  "data": {
    "name": "khalid",
    "gender": "male",
    "probability": 0.98,
    "is_confident": true,
    "sample_size": 3456,
    "processed_at": "2025-01-01T12:00:00.000000"
  }
}
```

#### Response Fields

| Field          | Type    | Description                                      |
|----------------|---------|--------------------------------------------------|
| `name`         | string  | The name that was classified                     |
| `gender`       | string  | `"male"` or `"female"`                           |
| `probability`  | float   | Confidence score between 0 and 1                 |
| `is_confident` | boolean | `true` if probability is 0.7 or above            |
| `sample_size`  | integer | Number of records used for the prediction        |
| `processed_at` | string  | UTC timestamp of when the request was processed  |

---

## Error Responses

All errors follow this structure:

```json
{
  "status": "error",
  "message": "<error message>"
}
```

| Status Code | Cause |
|-------------|-------|
| `400` | Bad request sent to Genderize API |
| `422` | Missing or invalid `name` parameter, or no prediction available for the name |
| `429` | Rate limit exceeded (max 1 request per 500ms per IP) |
| `500` | Internal server error |
| `502` | Genderize API is unreachable or timed out |

#### Edge Case — No Prediction Available

If Genderize returns no result for a name (e.g. very rare or ambiguous names):

```json
{
  "status": "error",
  "message": "No prediction available for the provided name"
}
```

---

## Rate Limiting

The API enforces a **500ms cooldown per IP address** to prevent abuse. Exceeding this limit returns a `429` response.

---

## CORS

The API allows cross-origin requests from all origins via:

```
Access-Control-Allow-Origin: *
```

---

## Deployment

This project is deployed on **Railway** using the following `Procfile`:

```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Deploy Your Own

1. Push your code to GitHub
2. Create a new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Set the **Root Directory** to `backend` (if applicable)
5. Railway auto-detects the `Procfile` and deploys

---

## requirements.txt

```
fastapi
uvicorn
httpx
starlette
```

---

## License

