import re

def match_term(term: str, text: str) -> bool:
    """
    Verifica se o termo aparece como palavra completa no texto
    (não como substring de outra palavra).
    """
    pattern = r"(?<![a-záàâãéêíóôõúç])" + re.escape(term) + r"(?![a-záàâãéêíóôõúç])"
    return bool(re.search(pattern, text, re.IGNORECASE))