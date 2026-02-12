"""Static file server for the React frontend."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.main import app as api_app

# Create combined app
app = FastAPI()

# Mount API routes
app.mount("/api", api_app)

# Get project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

print("STATIC DIR:", STATIC_DIR)
print("EXISTS:", os.path.exists(STATIC_DIR))

if os.path.exists(STATIC_DIR):

    # Serve JS/CSS assets
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
        name="assets"
    )

    # Serve main index
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    # SPA fallback
    @app.get("/{path:path}")
    async def serve_spa(path: str):
        if not path.startswith("api/"):
            return FileResponse(os.path.join(STATIC_DIR, "index.html"))
        return {"detail": "Not Found"}
