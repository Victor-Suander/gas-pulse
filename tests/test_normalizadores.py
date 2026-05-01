import pytest

from app.services.vendas_service import extrair_filial_id
from app.utils.normalizadores import normalizar_produto, normalizar_texto


def test_normalizar_texto_remove_espacos_e_minusculas():
    assert normalizar_texto("  Olá Mundo ") == "olá mundo"


def test_normalizar_texto_retorna_string_vazia_para_none():
    assert normalizar_texto(None) == ""


def test_normalizar_produto_mapeia_variacoes_canonicas():
    assert normalizar_produto("Gas. Comum") == "Gasolina Comum"
    assert normalizar_produto("etanol hid.") == "Etanol"
    assert normalizar_produto("DSL S10") == "Diesel S10"


def test_normalizar_produto_desconhecido_gera_erro_claro():
    with pytest.raises(ValueError, match="Produto desconhecido"):
        normalizar_produto("Querosene")


def test_extrair_filial_id_pelo_nome_do_arquivo():
    assert extrair_filial_id("vendas_F003_marco2025.csv") == "F003"


def test_extrair_filial_id_fora_do_padrao_gera_erro():
    with pytest.raises(ValueError, match="Nome de arquivo fora do padr"):
        extrair_filial_id("vendas_marco2025_F003.csv")
