from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GENDERIZE_URL = "https://api.genderize.io"


@app.get("/")
async def root():
    return {"message": "Use /api/classify?name=yourname"}


@app.get("/api/classify")
async def classify(request: Request, name: str = Query(default=None)):

    # Missing name
    if name is None:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Missing required query parameter 'name'",
            },
        )

    # Empty name
    if name.strip() == "":
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "Name cannot be empty"},
        )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(GENDERIZE_URL, params={"name": name})

        if response.status_code >= 500:
            raise HTTPException(
                status_code=502,
                detail={
                    "status": "error",
                    "message": "Genderize API is currently unavailable",
                },
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "message": "Genderize API rate limit exceeded",
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

        # Edge case — no prediction available
        if data.get("gender") is None or data.get("count", 0) == 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "error",
                    "message": "No prediction available for the provided name",
                },
            )

        probability = data.get("probability", 0)
        sample_size = data.get("count", 0)

        return {
            "status": "success",
            "data": {
                "name": data.get("name"),
                "gender": data.get("gender"),
                "probability": probability,
                "sample_size": sample_size,
                "is_confident": probability >= 0.7
                and sample_size >= 100,  # ✅ both conditions
                "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }

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

    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": "Unexpected server error"},
        )
