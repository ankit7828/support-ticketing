from datetime import datetime, timezone
from app.extensions import db

class TicketCollaborator(db.Model):
    __tablename__ = "ticket_collaborators"

    # Primary Key: ticket + user
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Timestamp
    added_at = db.Column(db.DateTime(timezone=True),nullable=False,default=lambda: datetime.now(timezone.utc))

    # Relationships
    ticket = db.relationship("Ticket", back_populates="collaborator_links")
    user = db.relationship("User", back_populates="collaboration_links")

    # Representation
    def __repr__(self):
        return (
            f"<TicketCollaborator "
            f"ticket={self.ticket_id} "
            f"user={self.user_id}>"
        )