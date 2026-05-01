"""Resumo dos relatos dos gerentes com IA e fallback local."""

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from app.utils.filiais import obter_nome_filial

ALERTA_SEM_RELEVANCIA = "Sem alertas relevantes"


def extrair_filial_id_email(nome_arquivo):
    """Extrai o ID da filial pelo nome do arquivo, sem delegar essa regra a IA."""
    match = re.search(r'email_(F\d{3})_marco2025\.txt', nome_arquivo)
    if not match:
        raise ValueError(f"Nome de arquivo fora do padrão: '{nome_arquivo}'. Esperado: email_FXXX_marco2025.txt")
    return match.group(1)


def gerar_resumo_com_gemini(texto_email):
    """Usa Gemini apenas para resumir texto narrativo em JSON estruturado."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não encontrada no .env")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Analise o seguinte relatório de gerente de posto de combustível e retorne exclusivamente um JSON válido no formato especificado.
Não inclua markdown, explicações ou texto adicional. Apenas o JSON.

Formato esperado:
{{
  "resumo": "síntese em 2 a 3 frases",
  "destaques": ["ponto 1", "ponto 2", "ponto 3"],
  "alertas": ["alerta 1", "alerta 2"],
  "sentimento_geral": "positivo | neutro | negativo"
}}

Regras:
- Retornar apenas JSON válido.
- Se não houver alertas, retornar lista vazia [].
- sentimento_geral deve ser apenas "positivo", "neutro" ou "negativo".
- Não inventar informações.

Relatório:
{texto_email}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        resposta_texto = response.text.strip()

        resumo_data = json.loads(resposta_texto)

        # A interface e o CSV dependem destas chaves do JSON.
        required_keys = ["resumo", "destaques", "alertas", "sentimento_geral"]
        for key in required_keys:
            if key not in resumo_data:
                raise ValueError(f"Chave obrigatória '{key}' ausente no JSON da IA")

        return resumo_data

    except Exception as e:
        print(f"Erro ao gerar resumo com Gemini: {e}")
        return gerar_resumo_fallback(texto_email)


def gerar_resumo_fallback(texto_email):
    """Aplica heuristicas locais quando a API falha ou retorna resposta invalida."""
    texto = texto_email.lower()

    alertas = []
    destaques = []

    palavras_alerta = {
        "manutenção": "manutenção",
        "atraso na entrega": "atraso na entrega",
        "atraso": "atraso",
        "queda": "queda",
        "redução": "redução",
        "impacto": "impacto",
        "bomba fora": "bomba fora",
        "fornecedor": "fornecedor",
    }

    for termo, descricao in palavras_alerta.items():
        if termo in texto and descricao not in alertas:
            alertas.append(descricao)

    if "aumento" in texto or "crescemos" in texto or "melhor março" in texto or "excepcional" in texto:
        destaques.append("aumento de volume")
    if "turista" in texto or "turistas" in texto:
        destaques.append("fluxo de turistas")
    if "transportadora" in texto or "transportadoras" in texto:
        destaques.append("fluxo de transportadoras")
    if "frota" in texto or "agrícola" in texto or "agricola" in texto:
        destaques.append("movimento de frotas agrícolas")
    if "estável" in texto or "tranquilo" in texto or "dentro do esperado" in texto:
        destaques.append("estabilidade operacional")
    if "gasolina" in texto and "destaque" in texto:
        destaques.append("produto Gasolina Comum em destaque")
    if "etanol" in texto and "destaque" in texto:
        destaques.append("produto Etanol em destaque")
    if "diesel" in texto and "destaque" in texto:
        destaques.append("produto Diesel S10 em destaque")

    destaques = list(dict.fromkeys(destaques))

    score_positivo = sum(texto.count(palavra) for palavra in ["positivo", "crescemos", "excepcional", "melhor março", "aumento", "acima do esperado", "bom movimento"])
    score_negativo = sum(texto.count(palavra) for palavra in ["queda", "redução", "atraso", "impactou", "impacto", "problema", "problemas", "fora de operação", "fraca"])
    score_neutro = sum(texto.count(palavra) for palavra in ["estável", "tranquilo", "dentro do esperado", "normal", "estabilidade"])

    if score_positivo >= score_negativo and score_positivo > 0:
        sentimento = "positivo"
    elif score_negativo > score_positivo:
        sentimento = "negativo"
    elif score_neutro > 0:
        sentimento = "neutro"
    else:
        sentimento = "neutro"

    if not destaques:
        if sentimento == "positivo":
            destaques.append("desempenho geral positivo")
        elif sentimento == "negativo":
            destaques.append("desafios operacionais")
        else:
            destaques.append("situação neutra ou estável")

    resumo_sentido = {
        "positivo": "O relato indica um período favorável, com sinais de desempenho positivo e pontos de destaque.",
        "negativo": "O relatório aponta dificuldades recentes, com problemas operacionais ou impacto em resultados.",
        "neutro": "O relatório descreve um período estável, sem mudanças significativas no desempenho.",
    }

    if alertas:
        resumo = f"Relato com alertas importantes: {', '.join(alertas)}. {resumo_sentido[sentimento]}"
    else:
        resumo = f"Relato sem alertas significativos. {resumo_sentido[sentimento]}"

    return {
        "resumo": resumo,
        "destaques": destaques,
        "alertas": alertas,
        "sentimento_geral": sentimento
    }


def formatar_alertas_csv(alertas):
    """Padroniza alertas vazios para evitar NaN no CSV final."""
    if not alertas:
        return ALERTA_SEM_RELEVANCIA

    alertas_validos = [
        str(alerta).strip()
        for alerta in alertas
        if alerta is not None and str(alerta).strip() and str(alerta).strip().lower() != "nan"
    ]

    if not alertas_validos:
        return ALERTA_SEM_RELEVANCIA

    return "; ".join(alertas_validos)


def processar_emails(caminho_pasta_emails):
    """Processa TXT dos gerentes e salva o CSV de resumo estruturado."""
    pasta = Path(caminho_pasta_emails)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta de emails não encontrada: {caminho_pasta_emails}")

    arquivos_txt = list(pasta.glob("*.txt"))
    if not arquivos_txt:
        raise ValueError("Nenhum arquivo TXT encontrado na pasta de emails.")

    resumos = []

    for arquivo in arquivos_txt:
        filial_id = extrair_filial_id_email(arquivo.name)
        filial_nome = obter_nome_filial(filial_id)

        with open(arquivo, 'r', encoding='utf-8') as f:
            texto_email = f.read()

        resumo_data = gerar_resumo_com_gemini(texto_email)

        resumo = {
            "filial_id": filial_id,
            "filial_nome": filial_nome,
            "resumo": resumo_data["resumo"],
            "destaques": "; ".join(resumo_data["destaques"]),
            "alertas": formatar_alertas_csv(resumo_data.get("alertas")),
            "sentimento_geral": resumo_data["sentimento_geral"]
        }

        resumos.append(resumo)

    import pandas as pd
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    caminho_saida = output_dir / "resumo_gerentes_marco2025.csv"
    df_resumos = pd.DataFrame(resumos)
    df_resumos.to_csv(caminho_saida, index=False)

    return resumos, str(caminho_saida)


