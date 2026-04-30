import os
from pathlib import Path
from werkzeug.utils import secure_filename


def extensao_permitida(filename, allowed_extensions):
    """Verifica se o arquivo tem uma extensão permitida."""
    return Path(filename).suffix.lower() in allowed_extensions


def salvar_arquivos_upload(files, destino, allowed_extensions):
    """Salva uploads em disco após validar o nome e a extensão."""
    destino_path = Path(destino)
    destino_path.mkdir(parents=True, exist_ok=True)

    salvo = 0
    invalidos = []

    for arquivo in files:
        nome = arquivo.filename
        if not nome:
            continue

        if not extensao_permitida(nome, allowed_extensions):
            invalidos.append(nome)
            continue

        nome_seguranca = secure_filename(nome)
        arquivo.save(destino_path / nome_seguranca)
        salvo += 1

    return salvo, invalidos
