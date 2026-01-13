import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks
from sqlmodel import Session

from database import get_db
from models.role import Role, UserRole
from models.user import User
from schemas.state import State

from agents.graph import GraphBuilder, build_chatbot_graph
from agents.models import GroqModel, GroqModelStructured

router = APIRouter(
    prefix="/v1/chatbot",
    tags=["chatbot"],
)

def get_session_id(session_id: Optional[str] = Cookie(None)) -> str:
    if not session_id:
        session_id = str(uuid.uuid4())
    return session_id

@router.post("/query", response_model=State)
def ask_chatbot(
    state: State,
    response: Response,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_session_id),
    db: Session = Depends(get_db),
):
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    config = {
        "configurable": {
            "llm": GroqModel(
                model="llama-3.1-8b-instant",
            ),
        }
    }

    graph = build_chatbot_graph()
    result_state = graph.invoke(state, config=config)
    return result_state