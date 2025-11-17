"""Flask application factory."""

from flask import Flask


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config.from_mapping(
        SECRET_KEY="dev",  # TODO: Use environment variable in production
        DATABASE_URL="sqlite:///./data/weather.db",
    )

    # Register blueprints
    from app.web.routes.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app
