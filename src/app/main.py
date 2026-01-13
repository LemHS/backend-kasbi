from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chatbot

from config import get_settings

settings = get_settings()

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

app.include_router(chatbot.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)