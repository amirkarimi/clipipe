import os
import secrets
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from storage_backend import DiskStorageBackend

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
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "3600"))

storage_backend = DiskStorageBackend(STORAGE_DIR, TIMEOUT_SECONDS)


@app.post("/store")
async def store_data(request: Request):
    """Store data with a generated human-readable code."""
    try:
        data = await request.body()
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        code = await storage_backend.store_data(data)
        return {"code": code, "expires_in": TIMEOUT_SECONDS}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/retrieve/{code}")
async def retrieve_data(code: str):
    """Retrieve data by code."""
    try:
        data = await storage_backend.retrieve_data(code)
        if data is None:
            raise HTTPException(status_code=404, detail="Code not found or expired")
        return Response(content=data, media_type="application/octet-stream")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
async def health_check() -> str:
    """Health check endpoint."""
    return "OK"


# Website - It should be at the end to not override other routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")


def main():
    """Main entry point for the server."""
    uvicorn.run(app, host="0.0.0.0", port=int(SERVER_PORT))


if __name__ == "__main__":
    main()
