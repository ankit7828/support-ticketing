from datetime import datetime, timezone
from app.extensions import db

class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requester_name = db.Column(db.String(100), nullable=False)
    requester_email = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="new")
    primary_assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    archived_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # SLA / RESPONSE CLOCK
    response_started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    response_target_minutes = db.Column(db.Integer, nullable=False, default=240)
    response_paused_at = db.Column(db.DateTime(timezone=True), nullable=True)
    response_paused_seconds = db.Column(db.Integer, nullable=False, default=0)
    response_breached = db.Column(db.Boolean, nullable=False, default=False)

    # RELATIONSHIPS
    primary_assignee = db.relationship("User", foreign_keys=[primary_assignee_id], backref="assigned_tickets")
    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="created_tickets")
    collaborator_links = db.relationship("TicketCollaborator", back_populates="ticket", cascade="all, delete-orphan")

    # REPRESENTATION
    def __repr__(self):
        return f"<Ticket {self.id}: {self.subject}>"