from pydantic import BaseModel, Field
from datetime import datetime

class IncidentTicket(BaseModel):
    id: str = Field(
        description="Identificador único do chamado"
    )
    
    timestamp: datetime = Field(
        description="Data e hora do chamado"
    )
    
    free_text: str = Field(
        min_length=2, 
        description="Texto digitado pelo usuário"
    )
