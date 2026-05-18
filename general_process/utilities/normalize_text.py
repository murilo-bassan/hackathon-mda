import re
from general_process.utilities.clean_text import clean_text
import unicodedata

def normalize_text(text: str) -> str:
    """
    Executa normalização textual leve
    sem alterar significado semântico.
    """

    if not text:
        return ""

    # limpeza base
    text = clean_text(text)

    # lowercase
    text = text.lower()

    # reduz pontuação exagerada
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"\.{2,}", ".", text)

    # reduz repetição exagerada de letras
    text = re.sub(r"(.)\1{3,}", r"\1\1", text)

    return text.strip()

def normalize_str(s: str) -> str:
    """Remove acentos, converte para minúsculas e strip."""
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode().lower().strip()
