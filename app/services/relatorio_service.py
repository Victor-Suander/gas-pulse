"""Service responsible for generating consolidated reports."""

import pandas as pd
from pathlib import Path


def gerar_ranking_faturamento(vendas_df):
    """Gera rankings de faturamento por filial e por produto e salva em CSV."""
    if vendas_df is None or vendas_df.empty:
        raise ValueError("DataFrame de vendas está vazio. Não é possível gerar ranking.")

    ranking_filial = (
        vendas_df.groupby("filial_nome")["valor_total_brl"]
        .sum()
        .reset_index()
        .sort_values("valor_total_brl", ascending=False)
        .reset_index(drop=True)
    )
    ranking_filial["tipo_ranking"] = "filial"
    ranking_filial["posicao"] = ranking_filial.index + 1
    ranking_filial = ranking_filial[["tipo_ranking", "posicao", "filial_nome", "valor_total_brl"]]
    ranking_filial = ranking_filial.rename(columns={"filial_nome": "nome"})

    ranking_produto = (
        vendas_df.groupby("produto_canonico")["valor_total_brl"]
        .sum()
        .reset_index()
        .sort_values("valor_total_brl", ascending=False)
        .reset_index(drop=True)
    )
    ranking_produto["tipo_ranking"] = "produto"
    ranking_produto["posicao"] = ranking_produto.index + 1
    ranking_produto = ranking_produto[["tipo_ranking", "posicao", "produto_canonico", "valor_total_brl"]]
    ranking_produto = ranking_produto.rename(columns={"produto_canonico": "nome"})

    ranking_df = pd.concat([ranking_filial, ranking_produto], ignore_index=True)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    caminho_saida = output_dir / "ranking_faturamento_marco2025.csv"
    ranking_df.to_csv(caminho_saida, index=False)

    return ranking_df, str(caminho_saida)


def gerar_corpo_email(vendas_df, resumo_emails_df, caminhos_arquivos):
    """Monta corpo de email profissional usando os dados de vendas e dos resumos de emails."""
    if vendas_df is None or vendas_df.empty:
        raise ValueError("DataFrame de vendas está vazio. Não é possível gerar corpo do email.")
    if resumo_emails_df is None or resumo_emails_df.empty:
        raise ValueError("DataFrame de resumo de emails está vazio. Não é possível gerar corpo do email.")

    total_geral = vendas_df["valor_total_brl"].sum()
    total_filiais = vendas_df.groupby("filial_nome")["valor_total_brl"].sum().sort_values(ascending=False)
    total_produtos = vendas_df.groupby("produto_canonico")["valor_total_brl"].sum().sort_values(ascending=False)

    alertas = resumo_emails_df["alertas"].dropna().astype(str).str.split("; ").explode().dropna().unique().tolist()
    if not alertas:
        alertas_texto = "Nenhum alerta relevante identificado nos relatórios dos gerentes."
    else:
        alertas_texto = "; ".join(alertas)

    top_filiais = ", ".join(
        [f"{nome} (R$ {valor:.2f})" for nome, valor in total_filiais.head(3).items()]
    )
    top_produtos = ", ".join(
        [f"{nome} (R$ {valor:.2f})" for nome, valor in total_produtos.head(3).items()]
    )

    corpo = [
        "Para: relatorios@redecombustiveis.com.br",
        "Assunto: Relatório Consolidado Março/2025 - Rede de Postos",
        "",
        "Prezados,",
        "",
        "Segue o relatório consolidado de março de 2025 com os resultados de faturamento e o resumo dos relatos de gerentes.",
        "",
        f"Arquivos gerados:",
        f"- Vendas consolidadas: {caminhos_arquivos.get('vendas')}",
        f"- Resumo de gerentes: {caminhos_arquivos.get('emails')}",
        f"- Ranking de faturamento: {caminhos_arquivos.get('ranking')}",
        "",
        f"Total geral faturado: R$ {total_geral:.2f}",
        "",
        "Ranking por filial:",
        f"{top_filiais}",
        "",
        "Ranking por produto:",
        f"{top_produtos}",
        "",
        "Principais alertas dos gerentes:",
        f"{alertas_texto}",
        "",
        "Observação: esta análise foi gerada automaticamente com base nos dados consolidados de vendas e nos resumos dos gerentes.",
        "",
        "Atenciosamente,",
        "Equipe de Inteligência de Dados"
    ]

    return "\n".join(corpo)
