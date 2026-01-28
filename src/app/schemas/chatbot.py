from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from langchain_core.documents import Document

class ChatbotState(BaseModel):
    query: str = Field(..., description="Chatbot query from user")
    context: Optional[List[str]] = Field(
        default_factory=list, description="List of context documents retrieved for the query"
    )
    answer: Optional[str] = Field(None, description="Chatbot's answer to the query")
    thread_id: Optional[int] = Field(None, description="Thread id to continue from specific thread")

class ThreadItem(BaseModel):
    thread_id: int
    thread_title: str

class ThreadResponse(BaseModel):
    threads: list[ThreadItem]

class ChatRequest(BaseModel):
    thread_id: int

class ChatItem(BaseModel):
    user_query: str
    answer: str

class ChatResponse(BaseModel):
    chats: List[ChatItem]