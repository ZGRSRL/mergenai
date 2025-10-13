from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import health, ingest, compliance, pricing, proposal, search

app = FastAPI(
    title="ZgrBid API",
    description="RFQ/SOW Analysis and Proposal Generation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])
app.include_router(pricing.router, prefix="/api/pricing", tags=["pricing"])
app.include_router(proposal.router, prefix="/api/proposal", tags=["proposal"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.get("/")
async def root():
    return {
        "message": "ZgrBid API - RFQ/SOW Analysis and Proposal Generation",
        "version": "1.0.0",
        "docs": "/docs"
    }

