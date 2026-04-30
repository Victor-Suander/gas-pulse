from flask import Blueprint, render_template, request, redirect, url_for
from pathlib import Path
import pandas as pd
from app.utils.arquivos import extensao_permitida, salvar_arquivos_upload
from app.services.preco_service import buscar_precos_referencia
from app.services.vendas_service import consolidar_vendas
from app.services.email_service import processar_emails
from app.services.relatorio_service import gerar_ranking_faturamento, gerar_corpo_email, gerar_pdf_relatorio

main = Blueprint("main", __name__)

VENDAS_DIR = "vendas"
EMAILS_DIR = "emails"
VENDAS_EXT = {".csv"}
EMAILS_EXT = {".txt"}


@main.route("/", methods=["GET", "POST"])
def index():
    """Render the home page and process upload submissions.

    Esta etapa salva os arquivos recebidos em disco sem processar os dados.
    """
    message = None
    status = None
    resumo_vendas = None

    if request.method == "POST":
        vendas_files = request.files.getlist("vendas_files")
        emails_files = request.files.getlist("emails_files")

        if not any(f.filename for f in vendas_files) and not any(f.filename for f in emails_files):
            message = "Nenhum arquivo enviado. Envie arquivos CSV de vendas e TXT de emails."
            status = "error"
            return render_template("index.html", message=message, status=status)

        if any(f.filename and not extensao_permitida(f.filename, VENDAS_EXT) for f in vendas_files):
            message = "Extensão inválida em arquivos de vendas. Use apenas .csv."
            status = "error"
            return render_template("index.html", message=message, status=status)

        if any(f.filename and not extensao_permitida(f.filename, EMAILS_EXT) for f in emails_files):
            message = "Extensão inválida em arquivos de email. Use apenas .txt."
            status = "error"
            return render_template("index.html", message=message, status=status)

        total_vendas, invalid_vendas = salvar_arquivos_upload(vendas_files, VENDAS_DIR, VENDAS_EXT)
        total_emails, invalid_emails = salvar_arquivos_upload(emails_files, EMAILS_DIR, EMAILS_EXT)

        if invalid_vendas or invalid_emails:
            message = "Alguns arquivos não foram salvos devido a extensões inválidas."
            status = "error"
        else:
            try:
                precos = buscar_precos_referencia()
                df_vendas, caminho_arquivo_vendas = consolidar_vendas(VENDAS_DIR, precos)
                resumos_emails, caminho_arquivo_emails = processar_emails(EMAILS_DIR)
                ranking_df, caminho_arquivo_ranking = gerar_ranking_faturamento(df_vendas)

                # Gerar resumo simples de vendas
                faturamento_por_produto = df_vendas.groupby("produto_canonico")["valor_total_brl"].sum().to_dict()
                faturamento_por_filial = df_vendas.groupby("filial_nome")["valor_total_brl"].sum().to_dict()

                # Coletar alertas dos emails
                alertas_emails = []
                for resumo in resumos_emails:
                    if resumo["alertas"]:
                        alertas_emails.extend([alerta.strip() for alerta in resumo["alertas"].split("; ") if alerta.strip()])

                resumo_emails_df = pd.DataFrame(resumos_emails)
                corpo_email = gerar_corpo_email(
                    df_vendas,
                    resumo_emails_df,
                    {
                        "vendas": caminho_arquivo_vendas,
                        "emails": caminho_arquivo_emails,
                        "ranking": caminho_arquivo_ranking
                    }
                )

                resumo_vendas = {
                    "total_registros": len(df_vendas),
                    "caminho_arquivo_vendas": caminho_arquivo_vendas,
                    "caminho_arquivo_emails": caminho_arquivo_emails,
                    "caminho_arquivo_ranking": caminho_arquivo_ranking,
                    "faturamento_por_produto": faturamento_por_produto,
                    "faturamento_por_filial": faturamento_por_filial,
                    "alertas_emails": alertas_emails,
                    "corpo_email": corpo_email,
                }

                message = f"Vendas consolidadas com {len(df_vendas)} registros. E-mails processados: {len(resumos_emails)}. Arquivos gerados: {caminho_arquivo_vendas}, {caminho_arquivo_emails}, {caminho_arquivo_ranking}"
                status = "success"
            except Exception as e:
                message = f"Arquivos salvos, mas erro ao processar: {str(e)}"
                status = "error"

    return render_template("index.html", message=message, status=status, resumo_vendas=resumo_vendas)


@main.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    """Rota para gerar PDF sob demanda após o processamento principal."""
    try:
        output_dir = Path("output")
        vendas_path = output_dir / "vendas_consolidadas_marco2025.csv"
        emails_path = output_dir / "resumo_gerentes_marco2025.csv"
        ranking_path = output_dir / "ranking_faturamento_marco2025.csv"

        # Validar se os arquivos necessários existem
        if not (vendas_path.exists() and emails_path.exists() and ranking_path.exists()):
            return {
                "status": "error",
                "message": "Processe os arquivos antes de gerar o PDF.",
            }, 400

        # Ler os DataFrames dos arquivos já gerados
        df_vendas = pd.read_csv(vendas_path)
        resumo_emails_df = pd.read_csv(emails_path)
        ranking_df = pd.read_csv(ranking_path)

        # Chamar a função que gera o PDF
        caminho_pdf = "output/relatorio_consolidado_marco2025.pdf"
        gerar_pdf_relatorio(df_vendas, resumo_emails_df, ranking_df, caminho_pdf)

        return {"status": "success", "message": f"PDF gerado com sucesso: {caminho_pdf}", "pdf_path": caminho_pdf}, 200
    except Exception as e:
        return {"status": "error", "message": f"Erro ao gerar PDF: {str(e)}"}, 500

