"""Utility module for common normalization helpers."""


def normalizar_texto(texto):
    """Return a cleaned, lowercase version of the given text."""
    if texto is None:
        return ""
    return texto.strip().lower()
