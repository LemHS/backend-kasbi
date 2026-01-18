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