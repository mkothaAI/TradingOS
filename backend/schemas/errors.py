from pydantic import BaseModel
from typing import Optional, Dict


class ErrorItem(BaseModel):
    code: str
    message: str
    details: Optional[Dict] = None
