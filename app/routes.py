from flask import Blueprint, render_template, request
from app.utils.arquivos import extensao_permitida, salvar_arquivos_upload
from app.services.preco_service import buscar_precos_referencia
from app.services.vendas_service import consolidar_vendas

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
                df_vendas, caminho_arquivo = consolidar_vendas(VENDAS_DIR, precos)

                # Gerar resumo simples
                faturamento_por_produto = df_vendas.groupby("produto_canonico")["valor_total_brl"].sum().to_dict()
                faturamento_por_filial = df_vendas.groupby("filial_nome")["valor_total_brl"].sum().to_dict()

                resumo_vendas = {
                    "total_registros": len(df_vendas),
                    "caminho_arquivo": caminho_arquivo,
                    "faturamento_por_produto": faturamento_por_produto,
                    "faturamento_por_filial": faturamento_por_filial
                }

                message = f"Arquivos salvos com sucesso. Vendas consolidadas com {len(df_vendas)} registros. Arquivo gerado: {caminho_arquivo}"
                status = "success"
            except Exception as e:
                message = f"Arquivos salvos, mas erro ao processar vendas: {str(e)}"
                status = "error"

    return render_template("index.html", message=message, status=status, resumo_vendas=resumo_vendas)

