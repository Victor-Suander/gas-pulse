from flask import Flask


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static", template_folder="templates")

    from .routes import main
    app.register_blueprint(main)

    return app
