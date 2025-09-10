from enum import Enum
from typing import Any, List

from pydantic import BaseModel


class ScriptCategory(str, Enum):
    VALIDATION = "validation"
    FIXING = "fixing"
    RESTRUCTURING = "restructuring"
    OTHER = "other"

class ScriptArgument(BaseModel):
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    replaceable: bool = False

class ScriptExample(BaseModel):
    command: str
    description: str

class Script(BaseModel):
    id: str
    name: str
    description: str
    path: str
    category: ScriptCategory
    production_ready: bool
    arguments: List[ScriptArgument]
    examples: List[ScriptExample]
