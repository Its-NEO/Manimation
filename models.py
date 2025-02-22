from pydantic import BaseModel, Field
from enum import Enum, auto

class ChatRequest(BaseModel):
  ...

class QueryType(Enum):
  # Core animation queries
  NEW_ANIMATION = auto()
  MODIFY_ANIMATION = auto()
  
  # Help and clarification
  TECHNICAL_HELP = auto()
  CONCEPT_HELP = auto()

class CategorizeQuery(BaseModel):
  type_: QueryType = Field(title="type", description=f'''The category for the query.
    The categories include:
    GENERAL_CHAT: "A normal conversation"
    NEW_ANIMATION: "Request for a new animation or a math lesson"
    MODIFY_ANIMATION: "Request for modification for existing animation"
    TECHNICAL_HELP: "Questions about implementation or errors"
    CONCEPT_HELP: "Question about the math lesson"
    ''')