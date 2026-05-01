from flask import Flask
from pathlib import Path


ARQUIVOS_OUTPUT_INICIAL = [
    "vendas_consolidadas_marco2025.csv",
    "resumo_gerentes_marco2025.csv",
    "ranking_faturamento_marco2025.csv",
    "relatorio_consolidado_marco2025.pdf",
    "precos_referencia_marco2025.json",
]


def limpar_output_inicial():
    """Remove saídas antigas sem tocar no cache interno da aplicação."""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    for nome_arquivo in ARQUIVOS_OUTPUT_INICIAL:
        caminho = output_dir / nome_arquivo
        if caminho.exists():
            caminho.unlink()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["FUELSYNC_EXPORT_DIR"] = None
    limpar_output_inicial()

    from .routes import main
    app.register_blueprint(main)

    return app
