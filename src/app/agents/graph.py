from langgraph.graph import StateGraph, START, END
from app.agents.prompts import GROQ_SYSTEM_TEMPLATE, GROQ_USER_TEMPLATE
from app.agents.retriever import BaseRetriever

from app.schemas.state import ChatbotState


class GraphBuilder():
    def __init__(
            self,
            config: dict = None,
    ):
        
        self.config = config
        self.graph_builder = StateGraph(ChatbotState)
        self.retriever = BaseRetriever(k_rerank=2)

    def compile_graph(self):
        return self.graph_builder.compile()

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

    def simple_node(
            self,
            state: ChatbotState,
            config
    ):
        message = state.query
        system_template = GROQ_SYSTEM_TEMPLATE
        user_template = GROQ_USER_TEMPLATE
        
        context = self.retriever.semantic_retrieve(message, rerank=True)
        context_str = "\n\n".join(context)

        response = config["configurable"]["llm"].invoke(
            message, 
            system_template, 
            user_template, 
            {"context": context_str, "question": message}
        )

        return {"answer": response, "context": context}
    
    def invoke_graph(self, initial_state: ChatbotState):
        return self.graph_builder.invoke(initial_state)
    

def build_chatbot_graph(config: dict = None) -> StateGraph:
    graph_builder = GraphBuilder(config=config)
    graph_builder.add_node("simple_node", "simple_node", "This is a custom state.")
    graph_builder.add_edge(START, "simple_node")
    graph_builder.add_edge("simple_node", END)
    graph = graph_builder.compile_graph()

    return graph, graph_builder.retriever, graph_builder.retriever.vector_db