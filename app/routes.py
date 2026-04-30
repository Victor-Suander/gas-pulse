from flask import Blueprint, render_template, request

main = Blueprint("main", __name__)


@main.route("/", methods=["GET", "POST"])
def index():
    """Render the home page and receive upload form submissions.

    Nesta etapa, apenas verificamos se os campos de upload existem.
    O processamento dos arquivos será implementado na próxima etapa.
    """
    message = None
    status = None

    if request.method == "POST":
        sales_files = request.files.getlist("sales_files")
        email_files = request.files.getlist("email_files")

        if sales_files and email_files and any(f.filename for f in sales_files) and any(f.filename for f in email_files):
            message = "Arquivos recebidos. O processamento será implementado na próxima etapa."
            status = "success"
        else:
            message = "Por favor, envie arquivos CSV de vendas e TXT de emails de gerentes."
            status = "error"

    return render_template("index.html", message=message, status=status)
