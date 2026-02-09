from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from threading import Lock

import logging

from app.security.jwt import decode_token

from app.agents import instansiate_chatbot_resources

from app.routers import chatbot, auth, admin

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chatbot_resources = {}
    instansiate_chatbot_resources(app)

    yield


app = FastAPI(
    root_path="/api",
    title="KASBI API",
    description="API untuk chatbot KASBI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def attach_jwt_claims(request: Request, call_next):
    request.state.claims = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            claims = decode_token(token)
            request.state.claims = claims
        except Exception:  # pragma: no cover - best effort
            logger.debug("Failed to decode token in middleware")
    response = await call_next(request)
    return response

app.include_router(chatbot.router)
app.include_router(auth.router)
app.include_router(admin.admin_router)
app.include_router(admin.super_admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)