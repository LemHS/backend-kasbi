from agents.graph import GraphBuilder, build_chatbot_graph

from threading import Lock
from fastapi import FastAPI

_chatbot_lock = Lock()

def instansiate_chatbot_resources(app: FastAPI):
    if getattr(app.state, "chatbot_resources", None) is None:
        with _chatbot_lock:
            if getattr(app.state, "chatbot_resources", None) is None:
                app.state.chatbot_resources = build_chatbot_graph()

    return app.state.chatbot_resources