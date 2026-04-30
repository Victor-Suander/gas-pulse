"""Utility module for branch definitions and metadata."""

FILIAIS = {
    "F001": "Posto Bandeirantes",
    "F002": "Auto Posto Central",
    "F003": "Posto São João",
    "F004": "Posto Ipiranga Express",
    "F005": "Posto Litoral Norte",
}


def obter_nome_filial(filial_id):
    """Retorna o nome da filial pelo ID ou lança erro se não encontrado."""
    if filial_id not in FILIAIS:
        raise ValueError(f"Filial ID '{filial_id}' não encontrado no mapa de filiais.")
    return FILIAIS[filial_id]

