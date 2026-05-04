"""Geracao de rankings, corpo de email e PDF consolidado."""

import pandas as pd
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle


def formatar_brl(valor):
    """Formata valores monetarios no padrao brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_ranking_faturamento(vendas_df):
    """Agrupa faturamento por filial/produto e salva o ranking do case."""
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


def gerar_pdf_relatorio(vendas_df, resumo_emails_df, ranking_df, caminho_saida):
    """Gera o PDF adicional sem substituir os CSVs obrigatorios."""
    output_path = Path(caminho_saida)
    output_path.parent.mkdir(exist_ok=True)

    total_geral = vendas_df["valor_total_brl"].sum()
    alertas = (
        resumo_emails_df["alertas"].dropna()
        .astype(str)
        .str.split("; ")
        .explode()
        .dropna()
        .unique()
        .tolist()
    )
    if not alertas:
        alertas = ["Nenhum alerta relevante identificado nos relatos dos gerentes."]

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=22,
        spaceAfter=12,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=14,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=18,
    )
    normal_style = styles["Normal"]
    normal_style.spaceAfter = 8

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elements = []
    elements.append(Paragraph("FuelSync", title_style))
    elements.append(Paragraph("Relatório Consolidado - Março/2025", subtitle_style))
    elements.append(Paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Total geral faturado: R$ {total_geral:.2f}", normal_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("Ranking de faturamento por filial", styles["Heading3"]))
    ranking_filial = ranking_df[ranking_df["tipo_ranking"] == "filial"][ ["posicao", "nome", "valor_total_brl"] ]
    filial_data = [["Posição", "Filial", "Faturamento (R$)"]]
    filial_data += [[int(row.posicao), row.nome, f"{row.valor_total_brl:.2f}"] for row in ranking_filial.itertuples(index=False)]
    filial_table = Table(filial_data, hAlign="LEFT", colWidths=[50, 250, 130])
    filial_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    elements.append(filial_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Ranking de faturamento por produto", styles["Heading3"]))
    ranking_produto = ranking_df[ranking_df["tipo_ranking"] == "produto"][ ["posicao", "nome", "valor_total_brl"] ]
    produto_data = [["Posição", "Produto", "Faturamento (R$)"]]
    produto_data += [[int(row.posicao), row.nome, f"{row.valor_total_brl:.2f}"] for row in ranking_produto.itertuples(index=False)]
    produto_table = Table(produto_data, hAlign="LEFT", colWidths=[50, 250, 130])
    produto_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    elements.append(produto_table)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Principais alertas dos gerentes", styles["Heading3"]))
    for alerta in alertas:
        elements.append(Paragraph(f"- {alerta}", normal_style))
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("Arquivos gerados", styles["Heading3"]))
    for arquivo in [
        "- vendas_consolidadas_marco2025.csv",
        "- resumo_gerentes_marco2025.csv",
        "- ranking_faturamento_marco2025.csv",
    ]:
        elements.append(Paragraph(arquivo, normal_style))

    doc.build(elements)


def gerar_corpo_email(vendas_df, resumo_emails_df, caminhos_arquivos):
    """Monta o texto sugerido para envio a sede com os dados consolidados."""
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

    top_filiais = "\n".join(
        [f"  - {nome}: {formatar_brl(valor)}" for nome, valor in total_filiais.head(3).items()]
    )
    top_produtos = "\n".join(
        [f"  - {nome}: {formatar_brl(valor)}" for nome, valor in total_produtos.head(3).items()]
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
        f"Total geral faturado: {formatar_brl(total_geral)}",
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
