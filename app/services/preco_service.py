"""Coleta, cache e fallback dos precos de referencia do case."""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup


PRODUTOS_OBRIGATORIOS = ["Gasolina Comum", "Etanol", "Diesel S10"]
CACHE_PRECOS_PATH = Path("app") / "cache" / "precos_referencia_marco2025.json"
PRECOS_REFERENCIA_FALLBACK = {
    "Gasolina Comum": 6.29,
    "Etanol": 4.11,
    "Diesel S10": 6.54,
}


def validar_precos(precos):
    """Valida se o mapa tem os produtos obrigatórios com preços numéricos."""
    if not isinstance(precos, dict):
        return False

    for produto in PRODUTOS_OBRIGATORIOS:
        preco = precos.get(produto)
        if not isinstance(preco, (int, float)):
            return False

    return True


def extrair_precos_html(conteudo_html):
    """Extrai preços da tabela HTML da página do case."""
    soup = BeautifulSoup(conteudo_html, "html.parser")
    tabela = soup.find("table")
    if not tabela:
        raise Exception("Tabela de preços não encontrada na página")

    precos = {}
    linhas = tabela.find_all("tr")[1:]  # Pular cabeçalho

    for linha in linhas:
        colunas = linha.find_all("td")
        if len(colunas) >= 2:
            produto = colunas[0].get_text(strip=True)
            preco_str = colunas[1].get_text(strip=True)

            try:
                precos[produto] = float(preco_str.replace(",", "."))
            except ValueError:
                raise Exception(f"Preço inválido para {produto}: {preco_str}")

    if not validar_precos(precos):
        raise Exception("Preços obrigatórios ausentes ou inválidos na tabela")

    return {produto: float(precos[produto]) for produto in PRODUTOS_OBRIGATORIOS}


def salvar_cache_precos(precos, caminho_cache=CACHE_PRECOS_PATH):
    """Salva os últimos preços válidos coletados via web."""
    caminho_cache.parent.mkdir(parents=True, exist_ok=True)
    if caminho_cache.exists():
        caminho_cache.unlink()

    payload = {
        "data_hora_atualizacao": datetime.now().replace(microsecond=0).isoformat(),
        "precos": precos,
    }

    with open(caminho_cache, "w", encoding="utf-8") as arquivo:
        json.dump(payload, arquivo, ensure_ascii=False, indent=2)


def carregar_cache_precos_valido(caminho_cache=CACHE_PRECOS_PATH):
    """Carrega o cache apenas se ele existir, estiver íntegro e tiver até 24h."""
    if not caminho_cache.exists():
        return None

    try:
        with open(caminho_cache, "r", encoding="utf-8") as arquivo:
            payload = json.load(arquivo)

        data_atualizacao = datetime.fromisoformat(payload["data_hora_atualizacao"])
        if datetime.now() - data_atualizacao > timedelta(hours=24):
            return None

        precos = payload["precos"]
        if not validar_precos(precos):
            return None

        return {produto: float(precos[produto]) for produto in PRODUTOS_OBRIGATORIOS}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError):
        return None


def buscar_precos_referencia(url="https://bridgenoc.github.io/case-postos/precos_marco2025.html"):
    """Coleta preços de referência automaticamente via requisição HTTP.

    Prioridade: web -> cache recente -> fallback padrao do case.
    Retorna mapa produto → preço médio e a origem usada.
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        "Connection": "close",
    }

    intervalos_retry = [1, 2, 3]
    ultimo_erro = None
    session = requests.Session()
    session.headers.update(headers)

    for tentativa in range(4):
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()

            precos = extrair_precos_html(response.content)
            try:
                salvar_cache_precos(precos)
            except OSError as e:
                print(f"Preços coletados via web, mas não foi possível salvar cache: {e}")
            session.close()
            return precos, "web"

        except (requests.RequestException, Exception) as e:
            ultimo_erro = e
            if tentativa < len(intervalos_retry):
                time.sleep(intervalos_retry[tentativa])

    session.close()

    precos_cache = carregar_cache_precos_valido()
    if precos_cache:
        print(f"Falha ao acessar/processar URL de preços. Usando cache local: {ultimo_erro}")
        return precos_cache, "cache"

    print(f"Falha ao acessar/processar URL de preços. Usando fallback do case: {ultimo_erro}")
    return PRECOS_REFERENCIA_FALLBACK.copy(), "fallback"


def carregar_precos_referencia(caminho_arquivo):
    """Placeholder to load reference prices."""
    return {}
