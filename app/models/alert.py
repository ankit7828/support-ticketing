from datetime import datetime, timezone
from app.extensions import db

class SLAAlert(db.Model):
    __tablename__ = "sla_alerts"
    id = db.Column(db.Integer, primary_key=True)
    
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)

    alert_type = db.Column(db.String(20), nullable=False)

    acknowledged = db.Column(db.Boolean, nullable=False, default=False)

    acknowledged_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    acknowledged_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    ticket = db.relationship("Ticket", backref=db.backref("sla_alerts", lazy=True))

    acknowledged_by = db.relationship("User", backref="acknowledged_alerts")

    def __repr__(self):
        return f"<SLAAlert {self.id} - {self.alert_type}>"