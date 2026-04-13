from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from datetime import datetime
import time
from typing import Dict

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GENDERIZE_URL = "https://api.genderize.io"


LAST_REQUEST_TIME: Dict[str, float] = {}
RATE_LIMIT_SECONDS = 0.5  # 500 ms


def check_rate_limit(client_ip: str):
    now = time.time()
    last_time = LAST_REQUEST_TIME.get(client_ip)

    if last_time is not None and (now - last_time) < RATE_LIMIT_SECONDS:
        raise HTTPException(
            status_code=429, detail="Too many requests. Please wait before retrying."
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
            raise HTTPException(status_code=400, detail="Bad request to Genderize API")
        elif response.status_code == 422:
            raise HTTPException(status_code=422, detail="Invalid input provided")
        elif response.status_code == 429:
            raise HTTPException(
                status_code=429, detail="Genderize API rate limit exceeded"
            )
        elif response.status_code == 500:
            raise HTTPException(
                status_code=500, detail="Genderize internal server error"
            )
        elif response.status_code == 501:
            raise HTTPException(status_code=501, detail="Genderize API not implemented")
        elif response.status_code == 502:
            raise HTTPException(
                status_code=502, detail="Bad gateway from Genderize API"
            )
        elif response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail="Unexpected error from Genderize API",
            )

        data = response.json()

        probability = data.get("probability", 0)

        transformed = {
            "name": data.get("name"),
            "gender": data.get("gender"),
            "probability": probability,
            "is_confident": True if probability >= 0.7 else False,
            "sample_size": data.get("count"),
            "processed_at": datetime.utcnow().isoformat(),
        }

        return {"success": 200, "data": transformed}

    except httpx.RequestError:
        raise HTTPException(
            status_code=502, detail="Failed to connect to Genderize API"
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Genderize API request timed out")

    except ValueError:
        raise HTTPException(
            status_code=500, detail="Error parsing response from Genderize API"
        )

    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected server error")

