from flask import Blueprint, render_template, request
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
    toast_tipo = None
    toast_titulo = None
    toast_mensagem = None
    toast_itens = []
    toast_arquivos = []
    toast_aviso = None
    resumo_vendas = None

    if request.method == "POST":
        vendas_files = request.files.getlist("vendas_files")
        emails_files = request.files.getlist("emails_files")

        if not any(f.filename for f in vendas_files) and not any(f.filename for f in emails_files):
            toast_tipo = "error"
            toast_titulo = "⚠ Erro no processamento"
            toast_mensagem = "Nenhum arquivo enviado. Envie arquivos CSV de vendas e TXT de emails."
            return render_template(
                "index.html",
                toast_tipo=toast_tipo,
                toast_titulo=toast_titulo,
                toast_mensagem=toast_mensagem,
                toast_itens=toast_itens,
                toast_arquivos=toast_arquivos,
                toast_aviso=toast_aviso,
            )

        if any(f.filename and not extensao_permitida(f.filename, VENDAS_EXT) for f in vendas_files):
            toast_tipo = "error"
            toast_titulo = "⚠ Erro no processamento"
            toast_mensagem = "Extensão inválida em arquivos de vendas. Use apenas .csv."
            return render_template(
                "index.html",
                toast_tipo=toast_tipo,
                toast_titulo=toast_titulo,
                toast_mensagem=toast_mensagem,
                toast_itens=toast_itens,
                toast_arquivos=toast_arquivos,
                toast_aviso=toast_aviso,
            )

        if any(f.filename and not extensao_permitida(f.filename, EMAILS_EXT) for f in emails_files):
            toast_tipo = "error"
            toast_titulo = "⚠ Erro no processamento"
            toast_mensagem = "Extensão inválida em arquivos de email. Use apenas .txt."
            return render_template(
                "index.html",
                toast_tipo=toast_tipo,
                toast_titulo=toast_titulo,
                toast_mensagem=toast_mensagem,
                toast_itens=toast_itens,
                toast_arquivos=toast_arquivos,
                toast_aviso=toast_aviso,
            )

        total_vendas, invalid_vendas = salvar_arquivos_upload(vendas_files, VENDAS_DIR, VENDAS_EXT)
        total_emails, invalid_emails = salvar_arquivos_upload(emails_files, EMAILS_DIR, EMAILS_EXT)

        # Capturar nomes dos arquivos processados para exibir na interface
        arquivos_vendas_processados = [f.filename for f in vendas_files if f.filename and extensao_permitida(f.filename, VENDAS_EXT)]
        arquivos_emails_processados = [f.filename for f in emails_files if f.filename and extensao_permitida(f.filename, EMAILS_EXT)]

        if invalid_vendas or invalid_emails:
            toast_tipo = "error"
            toast_titulo = "⚠ Erro no processamento"
            toast_mensagem = "Alguns arquivos não foram salvos devido a extensões inválidas."
        else:
            try:
                precos_referencia, origem_precos = buscar_precos_referencia()
                df_vendas, caminho_arquivo_vendas = consolidar_vendas(VENDAS_DIR, precos_referencia)
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
                    "arquivos_vendas_processados": arquivos_vendas_processados,
                    "arquivos_emails_processados": arquivos_emails_processados,
                    "faturamento_por_produto": faturamento_por_produto,
                    "faturamento_por_filial": faturamento_por_filial,
                    "alertas_emails": alertas_emails,
                    "corpo_email": corpo_email,
                }

                toast_tipo = "success"
                toast_titulo = "✓ Processamento concluído"
                toast_itens = [
                    f"Vendas consolidadas: {len(df_vendas)} registros",
                    f"E-mails processados: {len(resumos_emails)}",
                ]
                toast_arquivos = [
                    Path(caminho_arquivo_vendas).name,
                    Path(caminho_arquivo_emails).name,
                    Path(caminho_arquivo_ranking).name,
                ]
                if origem_precos == "cache":
                    toast_aviso = "⚠ A URL de preços não respondeu. Foram usados os últimos preços válidos salvos em cache."
                elif origem_precos == "fallback":
                    toast_aviso = "⚠ A URL de preços não respondeu e não havia cache válido. Foram usados preços de referência padrão do case."
            except Exception as e:
                toast_tipo = "error"
                toast_titulo = "⚠ Erro no processamento"
                toast_mensagem = f"Arquivos salvos, mas houve erro ao processar: {str(e)}"

    return render_template(
        "index.html",
        resumo_vendas=resumo_vendas,
        toast_tipo=toast_tipo,
        toast_titulo=toast_titulo,
        toast_mensagem=toast_mensagem,
        toast_itens=toast_itens,
        toast_arquivos=toast_arquivos,
        toast_aviso=toast_aviso,
    )


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

