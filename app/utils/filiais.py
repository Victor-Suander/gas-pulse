"""Mapa fixo das filiais usadas no case."""

FILIAIS = {
    "F001": "Posto Bandeirantes",
    "F002": "Auto Posto Central",
    "F003": "Posto São João",
    "F004": "Posto Ipiranga Express",
    "F005": "Posto Litoral Norte",
}


def obter_nome_filial(filial_id):
    """Resolve o nome da filial pelo ID extraido do nome do arquivo."""
    if filial_id not in FILIAIS:
        raise ValueError(f"Filial ID '{filial_id}' não encontrado no mapa de filiais.")
    return FILIAIS[filial_id]

