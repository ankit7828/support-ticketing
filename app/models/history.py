from datetime import datetime, timezone
from app.extensions import db

class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)

    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    event_type = db.Column(db.String(50), nullable=False)

    old_value = db.Column(db.Text, nullable=True)

    new_value = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    ticket = db.relationship("Ticket", backref=db.backref("history", lazy=True))

    actor = db.relationship("User", backref="ticket_history")

    def __repr__(self):
        return f"<TicketHistory {self.id} - {self.event_type}>"