from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Ticket, User

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

def utc_now():
    return datetime.now(timezone.utc)

def make_aware(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value

@dashboard_bp.route("/")
@login_required
def index():
    now = utc_now()

    # HEADLINE NUMBERS
    open_tickets = Ticket.query.filter_by(status="open", archived_at=None).count()
    pending_tickets = Ticket.query.filter_by(status="pending", archived_at=None).count()

    # Resolved this week
    week_start = now - timedelta(days=7)
    resolved_this_week = Ticket.query.filter(Ticket.status == "resolved", Ticket.updated_at >= week_start, Ticket.archived_at.is_(None)).count()

    # SLA breaches
    breaching_tickets = Ticket.query.filter(Ticket.response_breached.is_(True), Ticket.status.notin_(["closed"]), Ticket.archived_at.is_(None)).count()

    # STATUS BREAKDOWN
    status_rows = db.session.query(Ticket.status, func.count(Ticket.id)).filter(Ticket.archived_at.is_(None)).group_by(Ticket.status).all()
    status_breakdown = {"new": 0, "open": 0, "pending": 0, "resolved": 0, "closed": 0}

    for ticket_status, count in status_rows:
        if ticket_status in status_breakdown:
            status_breakdown[ticket_status] = count

    # AGENT BREAKDOWN
    agent_rows = db.session.query(User.name, func.count(Ticket.id)).outerjoin(Ticket, (Ticket.primary_assignee_id == User.id) & (Ticket.archived_at.is_(None))).filter(User.role == "agent").group_by(User.id, User.name).order_by(User.name.asc()).all()
    agent_breakdown = [{"name": name, "count": count} for name, count in agent_rows]

    # RESOLVED PER WEEK - LAST 8 WEEKS
    weekly_resolved = []

    # Start from the beginning of the current week.
    current_week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    for weeks_ago in range(7, -1, -1):
        start = current_week_start - timedelta(weeks=weeks_ago)
        end = start + timedelta(weeks=1)
        count = Ticket.query.filter(Ticket.status == "resolved", Ticket.updated_at >= start, Ticket.updated_at < end).count()
        weekly_resolved.append({"label": start.strftime("%d %b"), "count": count})

    # RECENT TICKETS
    recent_tickets = Ticket.query.filter(Ticket.archived_at.is_(None)).order_by(Ticket.created_at.desc()).limit(10).all()

    # MY TICKETS
    my_assigned_tickets = Ticket.query.filter(Ticket.primary_assignee_id == current_user.id, Ticket.archived_at.is_(None)).count()
    my_open_tickets = Ticket.query.filter(Ticket.primary_assignee_id == current_user.id, Ticket.status.in_(["new", "open", "pending"]), Ticket.archived_at.is_(None)).count()

    # COLLABORATOR TICKETS
    my_collaborator_tickets = 0
    my_collaborator_open_tickets = 0

    if current_user.role == "agent":
        my_collaborator_tickets = Ticket.query.filter(Ticket.collaborator_links.any(user_id=current_user.id), Ticket.archived_at.is_(None)).count()
        my_collaborator_open_tickets = Ticket.query.filter(Ticket.collaborator_links.any(user_id=current_user.id), Ticket.status.in_(["new", "open", "pending"]), Ticket.archived_at.is_(None)).count()

    # SUPERVISOR AGENT WORKLOAD
    agent_workload = []

    if current_user.role == "supervisor":
        agents = User.query.filter_by(role="agent").order_by(User.name.asc()).all()

        for agent in agents:
            assigned_total = Ticket.query.filter(Ticket.primary_assignee_id == agent.id, Ticket.archived_at.is_(None)).count()
            assigned_open = Ticket.query.filter(Ticket.primary_assignee_id == agent.id, Ticket.status.in_(["new", "open", "pending"]), Ticket.archived_at.is_(None)).count()
            agent_workload.append({"agent": agent, "total": assigned_total, "open": assigned_open})

    # RENDER
    return render_template("dashboard/index.html", open_tickets=open_tickets, pending_tickets=pending_tickets, resolved_this_week=resolved_this_week, breaching_tickets=breaching_tickets, status_breakdown=status_breakdown, agent_breakdown=agent_breakdown, weekly_resolved=weekly_resolved, recent_tickets=recent_tickets, my_assigned_tickets=my_assigned_tickets, my_open_tickets=my_open_tickets, my_collaborator_tickets=my_collaborator_tickets, my_collaborator_open_tickets=my_collaborator_open_tickets, agent_workload=agent_workload)