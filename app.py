from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.base import BaseHTTPMiddleware
import httpx
from datetime import datetime
import time
from typing import Dict

app = FastAPI()


class SimpleCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response


app.add_middleware(SimpleCORSMiddleware)

GENDERIZE_URL = "https://api.genderize.io"

LAST_REQUEST_TIME: Dict[str, float] = {}
RATE_LIMIT_SECONDS = 0.5


def check_rate_limit(client_ip: str):
    now = time.time()
    last_time = LAST_REQUEST_TIME.get(client_ip)

    if last_time is not None and (now - last_time) < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=429,
            detail={
                "status": "error",
                "message": "Too many requests. Please wait before retrying.",
            },
        )

    LAST_REQUEST_TIME[client_ip] = now


@app.get("/api/classify")
async def classify(request: Request, name: str = Query(..., min_length=1)):
    client_ip = request.client.host

    check_rate_limit(client_ip)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(GENDERIZE_URL, params={"name": name})

        if response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail={"status": "error", "message": "Bad request to Genderize API"},
            )
        elif response.status_code == 422:
            raise HTTPException(
                status_code=422,
                detail={"status": "error", "message": "Invalid input provided"},
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "message": "Genderize API rate limit exceeded",
                },
            )
        elif response.status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail={
                    "status": "error",
                    "message": "Genderize API is currently unavailable",
                },
            )
        elif response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    "status": "error",
                    "message": "Unexpected error from Genderize API",
                },
            )

        data = response.json()

        # Edge case: no prediction available
        if data.get("gender") is None or data.get("count") == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "error",
                    "message": "No prediction available for the provided name",
                },
            )

        probability = data.get("probability", 0)

        transformed = {
            "name": data.get("name"),
            "gender": data.get("gender"),
            "probability": probability,
            "is_confident": probability >= 0.7,
            "sample_size": data.get("count"),
            "processed_at": datetime.utcnow().isoformat(),
        }

        return {"status": "success", "data": transformed}

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=502,
            detail={"status": "error", "message": "Genderize API request timed out"},
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail={"status": "error", "message": "Failed to connect to Genderize API"},
        )

    except ValueError:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Error parsing response from Genderize API",
            },
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Unexpected server error"},
        )
