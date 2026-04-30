from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """Render the home page for the Gas Pulse application."""
    return render_template("index.html")
