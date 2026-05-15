from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class IngestTicket(BaseModel):
    id: str = Field(
        min_length=1,
        description="Identificador único do chamado"
    )
    
    timestamp: datetime = Field(
        min_length=1,
        description="Data e hora do chamado"
    )
    
    channel: str = Field(
        min_length=1,
        description="Canal da mensagem, ex: telefone, sistema de chamados, e-mail"
    )
    
    requester_profile: str = Field(
        min_length=1, 
        description="Perfil do usuário, ex: professor, estudante, técnico-administrativo"
    )
    
    free_text: str = Field(
        min_length=2, 
        description="Texto digitado pelo usuário"
    )
