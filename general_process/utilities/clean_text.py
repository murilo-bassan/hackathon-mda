import re
import unicodedata

def clean_text(text: str) -> str:
    """
    Remove emojis, caracteres invisíveis e normaliza o texto.
    """

    if not text:
        return ""

    # Normaliza caracteres unicode
    text = unicodedata.normalize("NFKD", text)

    # Remove emojis
    text = re.sub(
        r'[\U00010000-\U0010ffff]',
        '',
        text
    )

    # Remove caracteres invisíveis/especiais
    text = re.sub(r'[\r\n\t]', ' ', text)

    # Remove múltiplos espaços
    text = re.sub(r'\s+', ' ', text)

    return text.strip()