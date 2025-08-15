import os
import secrets

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
import uvicorn


app = FastAPI(
    title="Clipipe Server",
    description="Temporary data storage with human-readable codes",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_PORT = os.getenv("SERVER_PORT", "8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "3600"))

redis_client = redis.from_url(REDIS_URL)


def generate_human_readable_code() -> str:
    """Generate a short, human-readable code using pronounceable patterns."""
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"

    code = ""
    for i in range(6):
        if i % 2 == 0:
            code += secrets.choice(consonants)
        else:
            code += secrets.choice(vowels)

    code += str(secrets.randbelow(100)).zfill(2)
    return code


async def ensure_unique_code() -> str:
    """Generate a unique code that doesn't already exist in Redis."""
    max_attempts = 100
    for _ in range(max_attempts):
        code = generate_human_readable_code()
        exists = await redis_client.exists(f"clipipe:{code}")
        if not exists:
            return code

    raise HTTPException(status_code=500, detail="Unable to generate unique code")


@app.post("/store")
async def store_data(request: Request):
    """Store data with a generated human-readable code."""
    try:
        data = await request.body()
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")

        code = await ensure_unique_code()
        key = f"clipipe:{code}"

        await redis_client.setex(key, TIMEOUT_SECONDS, data)

        return {"code": code, "expires_in": TIMEOUT_SECONDS}

    except redis.RedisError as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/retrieve/{code}")
async def retrieve_data(code: str):
    """Retrieve data by code."""
    try:
        key = f"clipipe:{code}"
        data = await redis_client.get(key)

        if data is None:
            raise HTTPException(status_code=404, detail="Code not found or expired")

        return Response(content=data, media_type="application/octet-stream")
    except redis.RedisError as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except redis.RedisError:
        return {"status": "unhealthy", "redis": "disconnected"}

# Website - It should be at the end to not override other routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main():
    """Main entry point for the server."""
    uvicorn.run(app, host="0.0.0.0", port=int(SERVER_PORT))


if __name__ == "__main__":
    main()
