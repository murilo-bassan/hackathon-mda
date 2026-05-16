import unicodedata

def normalize_str(s: str) -> str:
    """Remove acentos, converte para minúsculas e strip."""
    s = unicodedata.normalize("NFKD", s)
    return s.encode("ascii", "ignore").decode().lower().strip()
