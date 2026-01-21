from app.agents.graph import GraphBuilder, build_chatbot_graph
from app.agents.retriever import BaseRetriever
from app.agents.database import ChromaVectorDatabase

from app.config import get_settings

from typing import Dict, TypedDict, Any, List

from threading import Lock
from fastapi import FastAPI

settings = get_settings()

_chatbot_lock = Lock()

class ChatbotResources(TypedDict):
    chatbot_graph: Any
    retriever: BaseRetriever
    vector_db: ChromaVectorDatabase


def resources_exist(chatbot_resources: ChatbotResources, attrs: List[str]):
    exist = []

    for attr in attrs:
        exist.append(chatbot_resources.get(attr, None) is not None)

    return all(exist)

def instansiate_chatbot_resources(app: FastAPI) -> ChatbotResources:
    if not resources_exist(app.state.chatbot_resources, ["chatbot_graph", "retriever", "vector_db"]):
        with _chatbot_lock:
            if not resources_exist(app.state.chatbot_resources, ["chatbot_graph", "retriever", "vector_db"]):
                chatbot_graph, retriever, vector_db = build_chatbot_graph()

                app.state.chatbot_resources["chatbot_graph"] = chatbot_graph
                app.state.chatbot_resources["retriever"] = retriever
                app.state.chatbot_resources["vector_db"] = vector_db

    return app.state.chatbot_resources


def instansiate_retriever(app: FastAPI) -> ChatbotResources:
    if not resources_exist(app.state.chatbot_resources, ["retriever"]):
        with _chatbot_lock:
            if not resources_exist(app.state.chatbot_resources, ["retriever"]):
                app.state.chatbot_resources["retriever"] = BaseRetriever(k_rerank=2)

    return app.state.chatbot_resources


def instansiate_vector_db(app: FastAPI) -> ChatbotResources:
    if not resources_exist(app.state.chatbot_resources, ["vector_db"]):
        with _chatbot_lock:
            if not resources_exist(app.state.chatbot_resources, ["vector_db"]):
                app.state.chatbot_resources["vector_db"] = ChromaVectorDatabase(
                    persist_directory=settings.VECTOR_DB_DIRECTORY, 
                    model_name=settings.EMBEDDING_MODEL
                )

    return app.state.chatbot_resources