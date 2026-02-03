from langgraph.graph import StateGraph, START, END
from app.agents.prompts import GROQ_SYSTEM_TEMPLATE, GROQ_USER_TEMPLATE
from app.agents.database import VectorDatabase
from app.agents.retriever import BaseRetriever, HybridRetriever, RerankRetriever

from app.schemas.chatbot import ChatbotState

from app.config import get_settings

# MemorySaver unutk checkpoint di RAM, FINALnya nanti pakai database
from langgraph.checkpoint.memory import MemorySaver

# Placeholder import database (PostgreSQL):
# from langgraph.checkpoint.postgres import PostgresSaver
# from psycopg_pool import ConnectionPool

import numpy as np
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"[TIMER] {name}: {(end - start)*1000:.2f} ms")

class GraphBuilder():
    def __init__(
            self,
            config: dict = None,
    ):
        
        self.config = config
        self.graph_builder = StateGraph(ChatbotState)
        self.retriever = RerankRetriever(k=15, k_rerank=2)

        # INITIALIZE checkpointer
        self.checkpointer = MemorySaver()

        # PLACEHOLDER PostGre
        # DB_URI = "postgresql://user:password@localhost:5432/namadatabase"
        # pool = ConnectionPool(conninfo=DB_URI, max_size=20)
        # self.checkpointer = PostgresSaver(pool)

    def compile_graph(self):
        return self.graph_builder.compile(checkpointer=self.checkpointer)

    def add_node(
            self,
            node_name: str,
            node_function: str,
            node_description: str = "",
    ):
        
        node_function = getattr(self, node_function, None)

        if node_function:
            self.graph_builder.add_node(
                node_name,
                node_function,
                metadata={"description":node_description}
            )
        else:
            raise ValueError(f"State '{node_name}' not found in GraphBuilder.")
        
    def add_edge(
            self,
            from_node: str,
            to_node: str,
    ):
        
        self.graph_builder.add_edge(
            from_node,
            to_node,
        )

    # def simple_node(
    #         self,
    #         state: ChatbotState,
    #         config
    # ):
    #     message = state.query
    #     system_template = GROQ_SYSTEM_TEMPLATE
    #     user_template = GROQ_USER_TEMPLATE
        
    #     context = self.retriever.semantic_retrieve(message, rerank=True)
    #     context_str = "\n\n".join(context)

    #     response = config["configurable"]["llm"].invoke(
    #         message, 
    #         system_template, 
    #         user_template, 
    #         {"context": context_str, "question": message}
    #     )

    #     return {"answer": response, "context": context}

    def simple_node(
            self, 
            state: ChatbotState, 
            config
    ):
        message = state.query
        session = config["configurable"]["session"]
        llm = config["configurable"]["llm"]

        # --- 1. DEFINISI PROMPT ROUTER ---

        router_system_template = """
        Tugas Anda adalah mengklasifikasikan intent (tujuan) dari pertanyaan pengguna.
        
        Kategori Label:
        1. "SEARCH": Jika pertanyaan berkaitan dengan Data Pendidikan, BPMP Papua, Kurikulum, Sekolah, Guru, Regulasi, Dapodik, atau Layanan Kantor.
        2. "CHAT": Jika pengguna menyapa (Halo, Hai), bertanya identitas bot (Siapa kamu, Siapa Kasbi), atau bertanya cara penggunaan bot.
        3. "OOT": Jika pertanyaan di luar topik pendidikan/kantor (misal: Politik, Resep Masakan, Film, Koding, Curhat Pribadi).

        Instruksi Output:
        Hanya berikan satu kata sebagai jawaban: SEARCH, CHAT, atau OOT.
        Jangan berikan penjelasan tambahan.
        """

        # Template user untuk router cukup placeholder sederhana
        router_user_template = "{question}"

        # --- 2. EKSEKUSI ROUTER ---
        # Memanggil llm.invoke sesuai struktur di models.py
        try:
            with timer("classification_llm"):
                classification = llm.invoke(
                    message=message,                        # Argumen 1: message (formalitas)
                    system_template=router_system_template, # Argumen 2: Aturan Router
                    user_template=router_user_template,     # Argumen 3: Template Input
                    prompt_format={"question": message}     # Argumen 4: Data Input
                )
            
            # standarisasi hasil
            classification = classification.strip().upper()
            
            # Safety check: paksa ke salah satu kategori valid
            if "SEARCH" in classification: classification = "SEARCH"
            elif "CHAT" in classification: classification = "CHAT"
            elif "OOT" in classification: classification = "OOT"
            else: classification = "SEARCH" # Default fallback

        except Exception as e:
            print(f"Router Error: {e}")
            classification = "SEARCH" # Fallback jika error


        # --- 3. LOGIKA PERCABANGAN (IF-ELSE) ---
        context = []
        
        # CASE A: Out of Topic (OOT)
        if classification == "OOT":
            return {
                "answer": "Mohon maaf, Kasbi hanya bisa menjawab pertanyaan seputar layanan BPMP Papua dan dunia pendidikan. Ada yang bisa dibantu terkait hal tersebut? 🙏", 
                "context": []
            }

        # CASE B: Butuh Data (SEARCH)
        elif classification == "SEARCH":
            # Panggil Retrieval teman Anda
            context = self.retriever.retrieve(session, message)
        
        # CASE C: Chat Santai (CHAT) -> Context dibiarkan kosong []
        
        
        # --- 4. GENERATE JAWABAN AKHIR ---
        # Siapkan string context
        if context:
            context_str = "\n\n".join(context)
        else:
            # Jika kategori CHAT, beri sinyal ke LLM bahwa tidak ada dokumen, 
            # tapi dia boleh menjawab menggunakan pengetahuannya tentang dirinya sendiri (System Prompt)
            context_str = "Tidak ada dokumen relevan. Jawablah berdasarkan identitas Anda sebagai Kasbi."
        
        # Panggil LLM lagi untuk jawaban final
        with timer("answer_llm"):
            response = llm.invoke(
                message=message,
                system_template=GROQ_SYSTEM_TEMPLATE, # Identitas Kasbi yang sudah Anda buat
                user_template=GROQ_USER_TEMPLATE,     # Template Sandwich Defense
                prompt_format={"context": context_str, "question": message}
            )

        return {"answer": response, "context": context}
    
    def invoke_graph(self, initial_state: ChatbotState):
        return self.graph_builder.invoke(initial_state)
    

def build_chatbot_graph(config: dict = None) -> StateGraph:
    settings = get_settings()

    vector_db = VectorDatabase(model_name=settings.EMBEDDING_MODEL)
    graph_builder = GraphBuilder(config=config)
    graph_builder.add_node("simple_node", "simple_node", "This is a custom state.")
    graph_builder.add_edge(START, "simple_node")
    graph_builder.add_edge("simple_node", END)
    graph = graph_builder.compile_graph()

    return graph, graph_builder.retriever, vector_db