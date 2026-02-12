"""FastAPI application for Monday.com BI Agent."""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os

from app.core.config import settings
from app.services.bi_agent import MondayBIAgent, BIResponse
from app.services.monday_client import MondayClient


# Create FastAPI app
app = FastAPI(
    title="Monday.com BI Agent",
    description="Business Intelligence Agent for analyzing Monday.com data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
static_path = os.path.join(os.path.dirname(__file__), "../static")
if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="assets")


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for BI queries."""
    query: str
    api_token: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for BI queries."""
    executive_summary: str
    key_metrics: Dict[str, Any]
    data_quality: Dict[str, Any]
    implications: List[str]


class BoardInfo(BaseModel):
    """Board information model."""
    id: str
    name: str
    description: Optional[str]
    state: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    monday_connected: bool


# Dependency to get BI agent
def get_bi_agent(api_token: Optional[str] = None) -> MondayBIAgent:
    """Get BI agent instance with optional API token override."""
    token = api_token or settings.MONDAY_API_TOKEN
    if not token:
        raise HTTPException(status_code=401, detail="Monday.com API token required")
    return MondayBIAgent(token)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    monday_connected = bool(settings.MONDAY_API_TOKEN)
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        monday_connected=monday_connected
    )


@app.get("/")
async def serve_index():
    """Serve the React frontend."""
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        monday_connected=bool(settings.MONDAY_API_TOKEN)
    )


@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve the React frontend for SPA routing."""
    # Don't intercept API routes
    if path.startswith("api/") or path == "health":
        return {"detail": "Not found"}
    
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Not found"}


@app.get("/api/boards", response_model=List[BoardInfo])
async def list_boards(api_token: Optional[str] = None):
    """List all accessible Monday.com boards."""
    token = api_token or settings.MONDAY_API_TOKEN
    if not token:
        raise HTTPException(status_code=401, detail="Monday.com API token required")
    
    try:
        client = MondayClient(token)
        boards = await client.get_boards()
        return [
            BoardInfo(
                id=board.get("id"),
                name=board.get("name"),
                description=board.get("description"),
                state=board.get("state", "active")
            )
            for board in boards
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch boards: {str(e)}")


@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a business intelligence query."""
    try:
        agent = get_bi_agent(request.api_token)
        response = await agent.answer_query(request.query)
        
        return QueryResponse(
            executive_summary=response.executive_summary,
            key_metrics=response.key_metrics,
            data_quality=response.data_quality,
            implications=response.implications
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/api/leadership-update")
async def generate_leadership_update(api_token: Optional[str] = None):
    """Generate a comprehensive leadership update."""
    try:
        agent = get_bi_agent(api_token)
        response = await agent.answer_query("Give me a leadership update")
        
        return {
            "executive_summary": response.executive_summary,
            "key_metrics": response.key_metrics,
            "data_quality": response.data_quality,
            "implications": response.implications
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate update: {str(e)}")


@app.get("/api/config")
async def get_config():
    """Get current configuration (without sensitive data)."""
    return {
        "deals_board_name": settings.DEALS_BOARD_NAME,
        "work_orders_board_name": settings.WORK_ORDERS_BOARD_NAME,
        "api_configured": bool(settings.MONDAY_API_TOKEN)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)