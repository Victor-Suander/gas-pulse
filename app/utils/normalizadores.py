"""Normalizacao deterministica de textos e produtos."""


def normalizar_texto(texto):
    """Limpa texto para comparacoes simples e previsiveis."""
    if texto is None:
        return ""
    return texto.strip().lower()


def normalizar_produto(nome_produto):
    """Converte variacoes conhecidas para os tres produtos canonicos do case."""
    produto_lower = normalizar_texto(nome_produto)

    # Variacoes aceitas para Gasolina Comum.
    if produto_lower in ["gasolina comum", "gas. comum", "gasolina comun", "gasolina", "gasolina c", "gc"]:
        return "Gasolina Comum"

    # Variacoes aceitas para Etanol.
    if produto_lower in ["etanol", "etanol hidratado", "etanol hid.", "etanol comum"]:
        return "Etanol"

    # Variacoes aceitas para Diesel S10.
    if produto_lower in ["diesel s10", "diesel s-10", "diesel s10 aditivado", "dsl s10", "s10"]:
        return "Diesel S10"

    raise ValueError(f"Produto desconhecido: '{nome_produto}'. Não foi possível normalizar.")

