import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request
from sqlmodel import Session

from database import get_db
from models.role import Role, UserRole
from models.user import User

from schemas.state import ChatbotState
from schemas.common import APIResponse

from security.permissions import RequireRole

from agents import instansiate_chatbot_resources
from agents.models import GroqModel, GroqModelStructured
from agents.retriever import BaseRetriever

router = APIRouter(
    prefix="/v1/chatbot",
    tags=["chatbot"],
)

def get_session_id(session_id: Optional[str] = Cookie(None)) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/query", response_model=APIResponse[ChatbotState])
def ask_chatbot(
    state: ChatbotState,
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
) -> APIResponse[ChatbotState]:
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    config = {
        "configurable": {
            "llm": GroqModel(
                model="llama-3.1-8b-instant",
            ),
        }
    }

    graph, retriever, vector_db = instansiate_chatbot_resources(request.app)
    result_state: ChatbotState = graph.invoke(state, config=config)
    return APIResponse(status_code=201, message="Generated response", data=result_state)