# Khung xương của Request (input) và Response (output)
from pydantic import BaseModel
from typing import List, Optional

class SearchQuery(BaseModel):
    query: str
    top_k: int = 3

class ChatQuery(BaseModel):
    query: str
    top_k: int = 3

class SourceDoc(BaseModel):
    filename: str
    score: float
    text: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]