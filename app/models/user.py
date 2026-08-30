from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="agent")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    collaboration_links = db.relationship("TicketCollaborator", back_populates="user", cascade="all, delete-orphan")

    # Password Methods
    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # Role Helpers
    def is_supervisor(self):
        """Return True if the user is a supervisor."""
        return self.role == "supervisor"

    def is_agent(self):
        """Return True if the user is an agent."""
        return self.role == "agent"

    # Representation
    def __repr__(self):
        return f"<User {self.email}>"