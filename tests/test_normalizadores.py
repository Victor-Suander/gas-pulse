from app.utils.normalizadores import normalizar_texto


def test_normalizar_texto_remove_espacos_e_minusculas():
    assert normalizar_texto("  Olá Mundo ") == "olá mundo"


def test_normalizar_texto_retorna_string_vazia_para_none():
    assert normalizar_texto(None) == ""
