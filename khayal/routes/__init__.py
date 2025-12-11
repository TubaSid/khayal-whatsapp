"""
Routes package - API endpoints
"""

def register_routes(app):
    """Register all routes with the Flask app"""
    from . import webhook, health, scheduler, admin
    
    # Health check endpoints
    health.health_bp.app = app
    app.register_blueprint(health.health_bp)
    
    # Webhook endpoint (main)
    webhook.webhook_bp.app = app
    app.register_blueprint(webhook.webhook_bp)
    
    # Scheduler endpoint
    scheduler.scheduler_bp.app = app
    app.register_blueprint(scheduler.scheduler_bp)
    
    # Admin endpoints
    admin.admin_bp.app = app
    app.register_blueprint(admin.admin_bp)


__all__ = ["register_routes"]