"""Utility module for common normalization helpers."""


def normalizar_texto(texto):
    """Return a cleaned, lowercase version of the given text."""
    if texto is None:
        return ""
    return texto.strip().lower()


def normalizar_produto(nome_produto):
    """Normaliza variações de produtos para nomes canônicos."""
    produto_lower = normalizar_texto(nome_produto)

    # Mapeamentos para Gasolina Comum
    if produto_lower in ["gasolina comum", "gas. comum", "gasolina comun", "gasolina", "gasolina c", "gc"]:
        return "Gasolina Comum"

    # Mapeamentos para Etanol
    if produto_lower in ["etanol", "etanol hidratado", "etanol hid.", "etanol comum"]:
        return "Etanol"

    # Mapeamentos para Diesel S10
    if produto_lower in ["diesel s10", "diesel s-10", "diesel s10 aditivado", "dsl s10", "s10"]:
        return "Diesel S10"

    raise ValueError(f"Produto desconhecido: '{nome_produto}'. Não foi possível normalizar.")

