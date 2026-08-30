from datetime import datetime, timezone
from app.extensions import db

class TicketStatusHistory(db.Model):
    __tablename__ = "ticket_status_history"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = db.Column(db.String(20), nullable=True)
    to_status = db.Column(db.String(20), nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    changed_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket = db.relationship("Ticket", backref=db.backref("status_history", lazy=True))
    changed_by = db.relationship("User", backref="status_changes")

    def __repr__(self):
        return f"<TicketStatusHistory {self.id}: {self.from_status} -> {self.to_status}>"