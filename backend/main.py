"""
Lookout - Marketplace Research Agent MVP
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_db
from routes import auth_routes, session_routes, listing_routes, message_routes, agent_routes

# Initialize database
init_db()

app = FastAPI(
    title="Lookout API",
    description="Marketplace Research Agent - helps evaluate and compare online listings",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(session_routes.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(listing_routes.router, prefix="/api/sessions/{session_id}/listings", tags=["listings"])
app.include_router(message_routes.router, prefix="/api/sessions/{session_id}", tags=["messages"])
app.include_router(message_routes.clarification_router, prefix="/api/sessions/{session_id}", tags=["clarifications"])
app.include_router(agent_routes.router, prefix="/agent", tags=["agent-interface"])

@app.get("/")
async def root():
    return {
        "message": "Lookout API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
