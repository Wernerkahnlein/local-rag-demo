from pydantic import BaseModel

class Message(BaseModel):
    content: str
    system_prompt: str = None
