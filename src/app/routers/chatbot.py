import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request
from sqlmodel import Session

from app.database import get_db
from app.models.role import Role, UserRole
from app.models.user import User

from app.schemas.state import ChatbotState
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole

from app.agents import instansiate_chatbot_resources
from app.agents.models import GroqModel, GroqModelStructured
from app.agents.retriever import BaseRetriever

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

    graph = instansiate_chatbot_resources(request.app)["chatbot_graph"]
    result_state: ChatbotState = graph.invoke(state, config=config)
    return APIResponse(status_code=201, message="Generated response", data=result_state)