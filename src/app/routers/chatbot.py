import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response, BackgroundTasks, Request
from sqlmodel import Session, select, func

from app.database import get_db
from app.models.role import Role, UserRole
from app.models.user import User
from app.models.history import Thread, Chat

from app.schemas.chatbot import ChatbotState, ThreadResponse, ChatRequest, ChatResponse
from app.schemas.common import APIResponse

from app.security.permissions import RequireRole
from app.security.dependencies import GetUser

from app.agents import instansiate_chatbot_resources
from app.agents.models import GroqModel, GroqModelStructured, OpenRouterModel
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
    payload: ChatbotState,
    response: Response,
    background_tasks: BackgroundTasks,
    request: Request,
    session_id: str = Depends(get_session_id),
    session: Session = Depends(get_db),
    user: User = Depends(GetUser())
) -> APIResponse[ChatbotState]:
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    if payload.thread_id is None:
        max_thread_id = session.exec(
            select(func.max(Thread.thread_id))
            .where(Thread.user_id == user.id)
        ).one()

        next_thread_id = (max_thread_id or 0) + 1
        thread = Thread(
            thread_title=payload.query,
            user_id=user.id,
            thread_id=next_thread_id
        )

        session.add(thread)
        session.commit()

        payload.thread_id = next_thread_id

    user_chat = Chat(
        role="user",
        message=payload.query,
        thread_id=payload.thread_id,
        user_id=user.id
    )

    session.add(user_chat)
    session.commit()

    config = {
        "configurable": {
            "llm": OpenRouterModel(
                model="arcee-ai/trinity-mini:free",
            ),
            "session": session,

            # ID buat checkpointing
            "thread_id": str(payload.thread_id)
        }
    }

    graph = instansiate_chatbot_resources(request.app)["chatbot_graph"]
    result_state: ChatbotState = graph.invoke(payload, config=config)
    chatbot_chat = Chat(
        role="chatbot",
        message=result_state["answer"],
        thread_id=payload.thread_id,
        user_id=user.id
    )

    session.add(chatbot_chat)
    session.commit()

    return APIResponse(status_code=201, message="Generated response", data=result_state)


@router.get("/threads", response_model=APIResponse[ThreadResponse])
def get_threads(
    response: Response,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_session_id),
    session: Session = Depends(get_db),
    user: User = Depends(GetUser()),
) -> APIResponse[ThreadResponse]:
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    threads = session.exec(select(Thread).where(Thread.user_id == user.id).order_by(Thread.thread_id)).all()
    return APIResponse(
        status_code=200, 
        message="Thread returned successfully", 
        data={
            "threads": [
                {"thread_id": thread.id, "thread_title": thread.thread_title}
                for thread in threads
            ]
        })


@router.get("/history", response_model=APIResponse[ChatResponse])
def chat_history(
    thread_id: int,
    response: Response,
    session_id: str = Depends(get_session_id),
    session: Session = Depends(get_db),
    user: User = Depends(GetUser()),
) -> APIResponse[ChatResponse]:
    
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    thread = session.exec(select(Thread).where(Thread.thread_id == thread_id, Thread.user_id == user.id)).one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail={"error_code": "invalid_thread", "message": "Thread not found"})
    
    chats = session.exec(select(Chat).where(Chat.thread_id == thread_id, Chat.user_id == user.id).order_by(Chat.id)).all()
    
    return APIResponse(
        status_code=200, 
        message="Chat histories returned successfully", 
        data={
            "chats": [
                {"role": chat.role, "message": chat.message, "created_at": chat.created_at}
                for chat in chats
            ]
        })