from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

import logging

from security.jwt import decode_token

from routers import chatbot, auth

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KASBI API",
    description="API untuk chatbot KASBI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)