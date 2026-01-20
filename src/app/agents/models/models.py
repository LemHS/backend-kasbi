import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings

settings = get_settings()

class GroqModel():
    def __init__(
            self, 
            model, 
            temperature: float = 0.0,
    ):

        self.model = model
        self.temperature = temperature
        self.llm = ChatGroq(api_key=settings.GROQ_API_KEY, model=model, temperature=temperature)

    def invoke(
            self,
            message: str,
            system_template: str,
            user_template: str,
            prompt_format: dict = {},
    ):
        
        template = ChatPromptTemplate(
            [
                ("system", system_template),
                ("user", user_template),
            ]
        )

        prompt = template.invoke(prompt_format)

        response = self.llm.invoke(prompt)
        return response.content
    

class GroqModelStructured():
    def __init__(
            self, 
            schema,
            model, 
            temperature: float = 0.0,
    ):

        self.model = model
        self.temperature = temperature
        self.llm = ChatGroq(api_key=settings.GROQ_API_KEY, model=model, temperature=temperature)
        self.llm = self.llm.with_structured_output(schema)

    def invoke(
            self,
            message: str,
            system_template: str,
            user_template: str,
            prompt_format: dict = {},
    ):
        
        template = ChatPromptTemplate(
            [
                ("system", system_template),
                ("user", user_template),
            ]
        )

        prompt = template.invoke(prompt_format)

        response = self.llm.invoke(prompt)
        return response.content