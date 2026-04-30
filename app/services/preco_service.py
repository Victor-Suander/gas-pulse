"""Service responsible for reference price handling and validation."""

import requests
from bs4 import BeautifulSoup


def buscar_precos_referencia(url="https://bridgenoc.github.io/case-postos/precos_marco2025.html"):
    """Coleta preços de referência automaticamente via requisição HTTP.

    Usa User-Agent para evitar bloqueios ou recusas de requisições automatizadas simples.
    Faz parse do HTML da página para extrair tabela de preços.
    Retorna mapa produto → preço médio.
    """
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f"Erro ao acessar URL de preços: {str(e)}")

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        tabela = soup.find('table')
        if not tabela:
            raise Exception("Tabela de preços não encontrada na página")

        precos = {}
        linhas = tabela.find_all('tr')[1:]  # Pular cabeçalho

        for linha in linhas:
            colunas = linha.find_all('td')
            if len(colunas) >= 2:
                produto = colunas[0].get_text(strip=True)
                preco_str = colunas[1].get_text(strip=True)

                try:
                    preco = float(preco_str.replace(',', '.'))
                    precos[produto] = preco
                except ValueError:
                    raise Exception(f"Preço inválido para {produto}: {preco_str}")

        if not precos:
            raise Exception("Nenhum preço encontrado na tabela")

        return precos

    except Exception as e:
        raise Exception(f"Erro ao processar tabela de preços: {str(e)}")


def carregar_precos_referencia(caminho_arquivo):
    """Placeholder to load reference prices."""
    return {}
