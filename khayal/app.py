"""Flask app factory for Khayal"""

from flask import Flask
from .config import get_config


def create_app(config_class=None):
    """
    Application factory pattern
    
    Args:
        config_class: Configuration class to use (defaults to environment-based)
    
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Register blueprints
    from .routes.webhook import webhook_bp
    from .routes.health import health_bp
    from .routes.scheduler import scheduler_bp
    from .routes.admin import admin_bp
    
    app.register_blueprint(webhook_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(scheduler_bp)
    app.register_blueprint(admin_bp)
    
    return app
