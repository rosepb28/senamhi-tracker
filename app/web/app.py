"""Flask application factory."""

from flask import Flask, jsonify, request
from flask_cors import CORS
from config.settings import settings


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    if settings.debug:
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    else:
        allowed_origins = settings.get_cors_origins()
        CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    app.config.from_mapping(
        SECRET_KEY=settings.secret_key,
        DATABASE_URL=settings.database_url,
        DEBUG=settings.debug,
    )

    from app.web.routes.main import bp as main_bp
    from app.web.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def handle_404(error):
        """Return JSON for API 404s, HTML for others."""
        if request.path.startswith("/api/"):
            return (
                jsonify(
                    {
                        "error": "Not found",
                        "message": "The requested endpoint does not exist",
                        "path": request.path,
                    }
                ),
                404,
            )
        return error

    return app
