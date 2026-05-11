from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class IngestTicket(BaseModel):
    id: str = Field(description="Identificador único do chamado")
    
    timestamp: datetime = Field(description="Data e hora do chamado")
    
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

    @field_validator('free_text')
    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Limpa o free_text (retira espaços desnecessários, quebras de linha e tabulações, além de colocar todas as letras para minúsculas)
        """
        return " ".join(text.lower().strip().split())
