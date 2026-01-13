from langgraph.graph import StateGraph, START, END
from agents.prompts import GROQ_PROMPT_TEMPLATE

from schemas.state import State

class GraphBuilder():
    def __init__(
            self,
            config: dict = None,
    ):
        
        self.config = config
        self.graph_builder = StateGraph(State)

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
            state: State,
            config
    ):
        message = state.query
        prompt_template = GROQ_PROMPT_TEMPLATE
        prompt_format = config["configurable"].get("prompt_format", {})

        response = config["configurable"]["llm"].invoke(message, prompt_template, prompt_format)

        return {"answer": response}
    
    def invoke_graph(self, initial_state: State):
        return self.graph_builder.invoke(initial_state)
    

def build_chatbot_graph(config: dict = None) -> StateGraph:
    graph_builder = GraphBuilder(config=config)
    graph_builder.add_node("simple_node", "simple_node", "This is a custom state.")
    graph_builder.add_edge(START, "simple_node")
    graph_builder.add_edge("simple_node", END)
    graph = graph_builder.compile_graph()

    return graph