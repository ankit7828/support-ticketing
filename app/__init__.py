from flask import Flask
from flask_login import current_user
from app.config import Config
from app.models import SLAAlert
from app.extensions import db, migrate, login_manager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # EXTENSIONS
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # IMPORT MODELS
    from app.models import User, Ticket, Reply, TicketCollaborator, TicketHistory, TicketStatusHistory, SLAAlert

    # AUTHENTICATION ROUTES
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # DASHBOARD ROUTES
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    # TICKET ROUTES
    from app.routes.tickets import tickets_bp
    app.register_blueprint(tickets_bp)

    # SLA ALERT ROUTES
    from app.routes.alerts import alerts_bp
    app.register_blueprint(alerts_bp)

    # SLA ALERT COUNT
    @app.context_processor
    def inject_sla_alert_count():
        count = 0
        if current_user.is_authenticated:
            query = SLAAlert.query.filter_by(acknowledged=False)

            # Agents only see alerts for their own tickets.
            # Supervisors see all active alerts.
            if current_user.role == "agent":
                query = query.filter(SLAAlert.ticket.has(primary_assignee_id=current_user.id))

            count = query.count()

        return {"active_sla_alert_count": count}

    # FLASK-LOGIN USER LOADER
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return None

    return app