from flask import Blueprint, current_app, render_template, request
from datetime import datetime
from pathlib import Path
import shutil
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


def criar_pasta_exportacao():
    """Cria a pasta datada da execução atual em Documents/FuelSync."""
    data_hora = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    pasta_exportacao = Path.home() / "Documents" / "FuelSync" / f"marco2025_{data_hora}"
    pasta_exportacao.mkdir(parents=True, exist_ok=True)
    return pasta_exportacao


def limpar_pasta_uploads(pasta, extensoes):
    """Remove arquivos com as extensões informadas para que apenas o upload atual seja processado."""
    pasta_path = Path(pasta)
    if not pasta_path.exists():
        return
    for arquivo in pasta_path.iterdir():
        if arquivo.is_file() and arquivo.suffix.lower() in extensoes:
            arquivo.unlink()


def copiar_arquivos_relatorio(arquivos, pasta_exportacao):
    """Copia arquivos finais para a pasta da execução atual."""
    pasta_exportacao = Path(pasta_exportacao)
    pasta_exportacao.mkdir(parents=True, exist_ok=True)
    for arquivo in arquivos:
        arquivo = Path(arquivo)
        shutil.copy2(arquivo, pasta_exportacao / arquivo.name)


def separar_partes_email(corpo_email):
    """Separa destinatario, assunto e corpo para exibir/copiar na interface."""
    linhas = corpo_email.splitlines()
    destinatario = ""
    assunto = ""
    indice_inicio_corpo = 0

    for indice, linha in enumerate(linhas):
        if linha.startswith("Para:"):
            destinatario = linha.replace("Para:", "", 1).strip()
        elif linha.startswith("Assunto:"):
            assunto = linha.replace("Assunto:", "", 1).strip()
            indice_inicio_corpo = indice + 1
            break

    corpo = "\n".join(linhas[indice_inicio_corpo:]).strip()
    return {
        "destinatario": destinatario,
        "assunto": assunto,
        "corpo": corpo,
    }


def formatar_brl(valor):
    """Formata número no padrão monetário brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_litros(valor):
    """Formata volume estimado em litros."""
    return f"{valor:,.2f} L".replace(",", "X").replace(".", ",").replace("X", ".")


def montar_destaque_ranking(posicao):
    """Gera destaque curto baseado apenas na posicao do ranking."""
    if posicao == 1:
        return "maior faturamento geral no período."
    if posicao == 2:
        return "segunda melhor performance entre as filiais."
    if posicao == 3:
        return "presença entre as três melhores filiais do ranking."
    return ""


def alerta_sem_relevancia(alerta):
    """Identifica textos que representam ausencia de alerta operacional."""
    return alerta.strip().lower() in {"nan", "none", "sem alertas relevantes"}


@main.route("/", methods=["GET", "POST"])
def index():
    """Renderiza a tela principal e executa o fluxo ponta a ponta do case."""
    toast_tipo = None
    toast_titulo = None
    toast_mensagem = None
    toast_itens = []
    toast_arquivos = []
    toast_aviso = None
    resumo_vendas = None
    email_partes = None

    if request.method == "POST":
        vendas_files = request.files.getlist("vendas_files")
        emails_files = request.files.getlist("emails_files")

        if not any(f.filename for f in vendas_files) and not any(f.filename for f in emails_files):
            toast_tipo = "error"
            toast_titulo = "⚠ Erro no processamento"
            toast_mensagem = "Nenhum arquivo enviado. Envie arquivos CSV de vendas e TXT de emails."
            return render_template(
                "index.html",
                email_partes=email_partes,
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
                email_partes=email_partes,
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
                email_partes=email_partes,
                toast_tipo=toast_tipo,
                toast_titulo=toast_titulo,
                toast_mensagem=toast_mensagem,
                toast_itens=toast_itens,
                toast_arquivos=toast_arquivos,
                toast_aviso=toast_aviso,
            )

        limpar_pasta_uploads(VENDAS_DIR, VENDAS_EXT)
        limpar_pasta_uploads(EMAILS_DIR, EMAILS_EXT)
        total_vendas, invalid_vendas = salvar_arquivos_upload(vendas_files, VENDAS_DIR, VENDAS_EXT)
        total_emails, invalid_emails = salvar_arquivos_upload(emails_files, EMAILS_DIR, EMAILS_EXT)

        # Guarda os nomes enviados para manter o feedback visivel apos o processamento.
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
                pasta_exportacao = criar_pasta_exportacao()
                copiar_arquivos_relatorio(
                    [
                        caminho_arquivo_vendas,
                        caminho_arquivo_emails,
                        caminho_arquivo_ranking,
                    ],
                    pasta_exportacao,
                )
                current_app.config["FUELSYNC_EXPORT_DIR"] = str(pasta_exportacao)

                # Os blocos abaixo montam apenas a visao de tela; os CSVs seguem gerados pelos services.
                total_geral_faturado = df_vendas["valor_total_brl"].sum()

                ranking_produto_tela = []
                faturamento_por_produto = (
                    df_vendas.groupby("produto_canonico")["valor_total_brl"]
                    .sum()
                    .sort_values(ascending=False)
                )
                for posicao, (produto, valor) in enumerate(faturamento_por_produto.items(), start=1):
                    ranking_produto_tela.append({
                        "posicao": posicao,
                        "nome": produto,
                        "valor_formatado": formatar_brl(valor),
                    })

                ranking_filial_tela = []
                faturamento_por_filial = (
                    df_vendas.groupby("filial_nome")["valor_total_brl"]
                    .sum()
                    .sort_values(ascending=False)
                )
                for posicao, (filial, valor) in enumerate(faturamento_por_filial.items(), start=1):
                    ranking_filial_tela.append({
                        "posicao": posicao,
                        "nome": filial,
                        "valor_formatado": formatar_brl(valor),
                        "destaque": montar_destaque_ranking(posicao),
                    })

                volume_por_produto_tela = []
                volume_por_produto = df_vendas.groupby("produto_canonico")["volume_estimado_litros"].sum()
                for produto in ["Gasolina Comum", "Etanol", "Diesel S10"]:
                    if produto in volume_por_produto:
                        volume_por_produto_tela.append({
                            "nome": produto,
                            "volume_formatado": formatar_litros(volume_por_produto[produto]),
                        })

                # Exibe alertas por filial sem duplicar termos vazios ou NaN vindos do CSV.
                alertas_por_filial = []
                for resumo in resumos_emails:
                    alertas_texto = str(resumo.get("alertas") or "").strip()
                    if not alertas_texto or alerta_sem_relevancia(alertas_texto):
                        continue

                    alertas_unicos = []
                    for alerta in alertas_texto.split("; "):
                        alerta_limpo = alerta.strip()
                        if alerta_limpo and not alerta_sem_relevancia(alerta_limpo) and alerta_limpo not in alertas_unicos:
                            alertas_unicos.append(alerta_limpo)

                    for alerta in alertas_unicos:
                        alertas_por_filial.append({
                            "alerta": alerta,
                            "filial_nome": resumo["filial_nome"],
                        })

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
                email_partes = separar_partes_email(corpo_email)

                resumo_vendas = {
                    "total_registros": len(df_vendas),
                    "total_geral_faturado": formatar_brl(total_geral_faturado),
                    "caminho_arquivo_vendas": caminho_arquivo_vendas,
                    "caminho_arquivo_emails": caminho_arquivo_emails,
                    "caminho_arquivo_ranking": caminho_arquivo_ranking,
                    "nome_arquivo_vendas": Path(caminho_arquivo_vendas).name,
                    "nome_arquivo_emails": Path(caminho_arquivo_emails).name,
                    "nome_arquivo_ranking": Path(caminho_arquivo_ranking).name,
                    "arquivos_vendas_processados": arquivos_vendas_processados,
                    "arquivos_emails_processados": arquivos_emails_processados,
                    "ranking_produto": ranking_produto_tela,
                    "ranking_filial": ranking_filial_tela,
                    "volume_por_produto": volume_por_produto_tela,
                    "alertas_por_filial": alertas_por_filial,
                    "corpo_email": corpo_email,
                }

                toast_tipo = "success"
                toast_titulo = "✓ Processamento concluído"
                toast_itens = [
                    f"Vendas consolidadas: {len(df_vendas)} registros",
                    f"E-mails processados: {len(resumos_emails)}",
                    f"Cópia salva em: {pasta_exportacao}",
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
        email_partes=email_partes,
        toast_tipo=toast_tipo,
        toast_titulo=toast_titulo,
        toast_mensagem=toast_mensagem,
        toast_itens=toast_itens,
        toast_arquivos=toast_arquivos,
        toast_aviso=toast_aviso,
    )


@main.route("/gerar-pdf", methods=["POST"])
def gerar_pdf():
    """Atualiza o PDF e exporta uma copia organizada dos arquivos finais."""
    try:
        output_dir = Path("output")
        vendas_path = output_dir / "vendas_consolidadas_marco2025.csv"
        emails_path = output_dir / "resumo_gerentes_marco2025.csv"
        ranking_path = output_dir / "ranking_faturamento_marco2025.csv"
        caminho_pdf = output_dir / "relatorio_consolidado_marco2025.pdf"

        # O PDF depende dos CSVs gerados no processamento principal.
        if not (vendas_path.exists() and emails_path.exists() and ranking_path.exists()):
            return {
                "status": "error",
                "message": "Não foi possível exportar. Processe os arquivos antes de gerar o PDF.",
            }, 400

        pasta_exportacao = current_app.config.get("FUELSYNC_EXPORT_DIR")
        if not pasta_exportacao or not Path(pasta_exportacao).exists():
            return {
                "status": "error",
                "message": "Processe os arquivos antes de gerar o PDF.",
            }, 400

        df_vendas = pd.read_csv(vendas_path)
        resumo_emails_df = pd.read_csv(emails_path)
        ranking_df = pd.read_csv(ranking_path)

        gerar_pdf_relatorio(df_vendas, resumo_emails_df, ranking_df, str(caminho_pdf))

        copiar_arquivos_relatorio([caminho_pdf], pasta_exportacao)

        return {
            "status": "success",
            "message": "PDF gerado com sucesso.",
            "pdf_path": str(caminho_pdf),
            "export_path": str(pasta_exportacao),
        }, 200
    except Exception as e:
        return {"status": "error", "message": f"Erro ao exportar relatório: {str(e)}"}, 500