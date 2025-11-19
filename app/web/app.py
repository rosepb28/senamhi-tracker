"""Flask application factory."""

from flask import Flask, jsonify, request
from flask_cors import CORS


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Configuration
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO: Use environment variable in production
        DATABASE_URL="sqlite:///./data/weather.db",
    )

    # Register blueprints
    from app.web.routes.main import bp as main_bp
    from app.web.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Global error handler for API routes
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
        return error  # Let Flask handle non-API 404s

    return app
