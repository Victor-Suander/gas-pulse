"""Service responsible for fuel station sales data processing."""

import os
import re
import pandas as pd
from pathlib import Path
from app.utils.filiais import obter_nome_filial
from app.utils.normalizadores import normalizar_produto


def extrair_filial_id(nome_arquivo):
    """Extrai o ID da filial do nome do arquivo (ex: vendas_F001_marco2025.csv -> F001)."""
    match = re.search(r'vendas_(F\d{3})_marco2025\.csv', nome_arquivo)
    if not match:
        raise ValueError(f"Nome de arquivo fora do padrão: '{nome_arquivo}'. Esperado: vendas_FXXX_marco2025.csv")
    return match.group(1)


def consolidar_vendas(caminho_pasta_vendas, precos_referencia):
    """Consolida vendas de múltiplos CSVs em uma tabela única."""
    pasta = Path(caminho_pasta_vendas)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta de vendas não encontrada: {caminho_pasta_vendas}")

    arquivos_csv = list(pasta.glob("*.csv"))
    if not arquivos_csv:
        raise ValueError("Nenhum arquivo CSV encontrado na pasta de vendas.")

    dados_consolidados = []

    for arquivo in arquivos_csv:
        filial_id = extrair_filial_id(arquivo.name)
        filial_nome = obter_nome_filial(filial_id)

        df = pd.read_csv(arquivo)

        # Validar colunas obrigatórias
        colunas_obrigatorias = ["data", "produto", "valor_total_brl"]
        for col in colunas_obrigatorias:
            if col not in df.columns:
                raise ValueError(f"Coluna obrigatória '{col}' não encontrada no arquivo {arquivo.name}")

        # Converter valor_total_brl para float
        df["valor_total_brl"] = pd.to_numeric(df["valor_total_brl"], errors="coerce")
        if df["valor_total_brl"].isna().any():
            raise ValueError(f"Valores inválidos em 'valor_total_brl' no arquivo {arquivo.name}")

        # Normalizar produtos
        df["produto_canonico"] = df["produto"].apply(normalizar_produto)

        # Adicionar colunas de filial
        df["filial_id"] = filial_id
        df["filial_nome"] = filial_nome

        # Adicionar preço médio e calcular volume
        df["preco_medio_litro_brl"] = df["produto_canonico"].map(precos_referencia)
        if df["preco_medio_litro_brl"].isna().any():
            produtos_sem_preco = df[df["preco_medio_litro_brl"].isna()]["produto_canonico"].unique()
            raise ValueError(f"Preços não encontrados para produtos: {list(produtos_sem_preco)}")

        df["volume_estimado_litros"] = df["valor_total_brl"] / df["preco_medio_litro_brl"]

        # Selecionar colunas finais
        colunas_finais = ["data", "filial_id", "filial_nome", "produto_canonico", "valor_total_brl", "preco_medio_litro_brl", "volume_estimado_litros"]
        df_final = df[colunas_finais]

        dados_consolidados.append(df_final)

    # Juntar todos os dados
    df_consolidado = pd.concat(dados_consolidados, ignore_index=True)

    # Salvar arquivo consolidado
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    caminho_saida = output_dir / "vendas_consolidadas_marco2025.csv"
    df_consolidado.to_csv(caminho_saida, index=False)

    return df_consolidado, str(caminho_saida)


def carregar_vendas(caminho_csv):
    """Placeholder to load and normalize sales data."""
    return []

