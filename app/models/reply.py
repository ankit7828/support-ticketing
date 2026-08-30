from datetime import datetime, timezone
from app.extensions import db

class Reply(db.Model):
    __tablename__ = "replies"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket = db.relationship("Ticket", backref=db.backref("replies", lazy=True, order_by="Reply.created_at"))
    author = db.relationship("User", backref="replies")

    def __repr__(self):
        return f"<Reply {self.id} for Ticket {self.ticket_id}>"