import csv
import io

from flask import Response
from datetime import datetime, timezone, timedelta

from flask import ( Blueprint, render_template, request, redirect, url_for, flash )
from flask_login import login_required, current_user
from sqlalchemy import or_, case

from app.extensions import db
from app.models import ( Ticket, User, Reply, TicketCollaborator, TicketHistory, TicketStatusHistory, SLAAlert )

tickets_bp = Blueprint( "tickets", __name__, url_prefix="/tickets" )

# PERMISSION
def can_access_ticket(ticket):
    if current_user.role == "supervisor":
        return True

    if current_user.role != "agent":
        return False

    if ticket.primary_assignee_id == current_user.id:
        return True

    for link in ticket.collaborator_links:
        if link.user_id == current_user.id:
            return True
    return False

# SLA
SLA_TARGETS = { "urgent": 60, "high": 240, "medium": 480, "low": 1440 }

def get_sla_target(priority):
    return SLA_TARGETS.get( priority, SLA_TARGETS["medium"] )

def utc_now():
    return datetime.now(timezone.utc)

def make_aware(value):
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace( tzinfo=timezone.utc )
    return value

def ensure_sla_started(ticket):
    if ticket.response_started_at is None:
        ticket.response_started_at = ( make_aware(ticket.created_at) or utc_now() )

    ticket.response_target_minutes = ( get_sla_target(ticket.priority) )

    if ticket.response_paused_seconds is None:
        ticket.response_paused_seconds = 0

    if ticket.response_breached is None:
        ticket.response_breached = False

def pause_sla(ticket):
    ensure_sla_started(ticket)
    if ticket.response_paused_at is None:
        ticket.response_paused_at = utc_now()

def resume_sla(ticket):
    if ticket.response_paused_at is None:
        return

    now = utc_now()
    paused_at = make_aware( ticket.response_paused_at )
    paused_seconds = int( (now - paused_at).total_seconds() )
    ticket.response_paused_seconds = ( ticket.response_paused_seconds or 0 ) + max( paused_seconds, 0 )
    ticket.response_paused_at = None

def update_sla_status(ticket):
    ensure_sla_started(ticket)
    # Pending means waiting for customer.
    # SLA clock remains paused.
    if ticket.status == "pending":
        return

    # Closed tickets do not continue running.
    if ticket.status == "closed":
        return

    now = utc_now()
    started_at = make_aware( ticket.response_started_at )
    elapsed_seconds = ( now - started_at ).total_seconds()
    paused_seconds = ( ticket.response_paused_seconds or 0 )
    active_seconds = ( elapsed_seconds - paused_seconds )
    target_seconds = ( ticket.response_target_minutes * 60 )
    ticket.response_breached = ( active_seconds >= target_seconds )

def sla_remaining_seconds(ticket):
    ensure_sla_started(ticket)
    if ticket.status == "pending":
        return None

    if ticket.status == "closed":
        return None

    now = utc_now()
    started_at = make_aware( ticket.response_started_at )
    elapsed_seconds = ( now - started_at ).total_seconds()
    paused_seconds = ( ticket.response_paused_seconds or 0 )
    active_seconds = ( elapsed_seconds - paused_seconds )
    target_seconds = ( ticket.response_target_minutes * 60 )
    return int( target_seconds - active_seconds )

# SLA ALERTS
SLA_WARNING_MINUTES = 15
def update_sla_alert(ticket):
    """Create an SLA warning/breach alert for the ticket when needed."""
    if ticket.archived_at is not None:
        return

    if ticket.primary_assignee_id is None:
        return

    if ticket.status in {"pending", "closed"}:
        return

    ensure_sla_started(ticket)
    update_sla_status(ticket)
    remaining = sla_remaining_seconds(ticket)

    if remaining is None:
        return

    if remaining <= 0:
        alert_type = "breach"
    elif remaining <= SLA_WARNING_MINUTES * 60:
        alert_type = "warning"
    else:
        return

    existing = SLAAlert.query.filter_by( ticket_id=ticket.id, alert_type=alert_type, acknowledged=False ).first()
    if existing:
        return

    db.session.add( SLAAlert( ticket_id=ticket.id, alert_type=alert_type, acknowledged=False ) )

# TICKET LIST
@tickets_bp.route("/")
@login_required
def list_tickets():
    search = request.args.get( "search", "" ).strip()
    status = request.args.get( "status", "" ).strip().lower()
    priority = request.args.get( "priority", "" ).strip().lower()
    category = request.args.get( "category", "" ).strip()
    assignee = request.args.get( "assignee", "" ).strip()
    sort = request.args.get( "sort", "created" ).strip().lower()
    page = request.args.get( "page", 1, type=int )

    if page < 1:
        page = 1

    per_page = 10
    # Default queue excludes archived tickets
    query = Ticket.query.filter( Ticket.archived_at.is_(None) )

    # Agent visibility
    if current_user.role == "agent":
        query = query.filter( or_( Ticket.primary_assignee_id == current_user.id, Ticket.collaborator_links.any( user_id=current_user.id ) ) )

    # Search
    if search:
        pattern = f"%{search}%"
        query = query.filter( or_( Ticket.subject.ilike(pattern), Ticket.description.ilike(pattern) ) )

    # Status
    if status in { "new", "open", "pending", "resolved", "closed" }:
        query = query.filter( Ticket.status == status )

    # Priority
    if priority in { "low", "medium", "high", "urgent" }:
        query = query.filter( Ticket.priority == priority )

    # Category
    if category:
        query = query.filter( Ticket.category == category )

    # Assignee
    if assignee:
        try:
            assignee_id = int( assignee )
            query = query.filter( Ticket.primary_assignee_id == assignee_id )
        except ValueError:
            pass

    # Sorting
    if sort == "priority":
        priority_order = case( (Ticket.priority == "urgent", 1), (Ticket.priority == "high", 2), (Ticket.priority == "medium", 3), (Ticket.priority == "low", 4), else_=5 )
        query = query.order_by( priority_order, Ticket.created_at.desc() )
    elif sort == "updated":
        query = query.order_by( Ticket.updated_at.desc() )
    else:
        query = query.order_by( Ticket.created_at.desc() )

    # Pagination
    pagination = query.paginate( page=page, per_page=per_page, error_out=False )
    tickets = pagination.items

    # Update SLA status for displayed tickets
    for ticket in tickets:
        update_sla_status(ticket)
        update_sla_alert(ticket)

    db.session.commit()
    # Filter data
    agents = User.query.filter_by( role="agent" ).order_by( User.name.asc() ).all()
    category_rows = db.session.query( Ticket.category ).distinct().order_by( Ticket.category.asc() ).all()
    categories = [ row[0] for row in category_rows if row[0] ]
    return render_template( "tickets/list.html", tickets=tickets, pagination=pagination, total_matches=pagination.total, agents=agents, categories=categories, search=search, status=status, priority=priority, category=category, assignee=assignee, sort=sort )

# CREATE TICKET
@tickets_bp.route( "/create", methods=["GET", "POST"] )
@login_required
def create_ticket():
    agents = User.query.filter_by( role="agent" ).order_by( User.name.asc() ).all()
    if request.method == "POST":
        subject = request.form.get( "subject", "" ).strip()
        description = request.form.get( "description", "" ).strip()
        requester_name = request.form.get( "requester_name", "" ).strip()
        requester_email = request.form.get( "requester_email", "" ).strip()
        priority = request.form.get( "priority", "medium" ).strip().lower()
        category = request.form.get( "category", "" ).strip()
        primary_assignee_id = ( request.form.get( "primary_assignee_id" ) or None )

        # Validation
        if not subject:
            flash( "Subject is required.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        if not description:
            flash( "Description is required.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        if not requester_name:
            flash( "Requester name is required.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        if not requester_email:
            flash( "Requester email is required.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        if not category:
            flash( "Category is required.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        if priority not in { "low", "medium", "high", "urgent" }:
            flash( "Invalid priority.", "danger" )
            return render_template( "tickets/create.html", agents=agents )

        # Validate assignee
        if primary_assignee_id:
            try:
                primary_assignee_id = int( primary_assignee_id )
            except ValueError:
                flash( "Invalid assignee.", "danger" )
                return render_template( "tickets/create.html", agents=agents )

            agent = User.query.filter_by( id=primary_assignee_id, role="agent" ).first()
            if not agent:
                flash( "Selected assignee is not a valid agent.", "danger" )
                return render_template( "tickets/create.html", agents=agents )

        # Create
        now = utc_now()
        ticket = Ticket( subject=subject, description=description, requester_name=requester_name, requester_email=requester_email, priority=priority, category=category, status="new", primary_assignee_id=primary_assignee_id, created_by_id=current_user.id, response_started_at=now, response_target_minutes=get_sla_target( priority ), response_paused_at=None, response_paused_seconds=0, response_breached=False )
        db.session.add(ticket)
        db.session.flush()

        history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_created", old_value=None, new_value="new" )
        status_history = TicketStatusHistory( ticket_id=ticket.id, from_status=None, to_status="new", changed_by_id=current_user.id )
        db.session.add(history)
        db.session.add(status_history)
        db.session.commit()

        flash( "Ticket created successfully.", "success" )
        return redirect( url_for( "tickets.list_tickets" ) )
    return render_template( "tickets/create.html", agents=agents )

# TICKET DETAIL + REPLY
@tickets_bp.route( "/<int:ticket_id>", methods=["GET", "POST"] )
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if not can_access_ticket(ticket):
        flash( "You do not have permission to access this ticket.", "danger" )
        return redirect( url_for( "tickets.list_tickets" ) )

    agents = User.query.filter_by( role="agent" ).order_by( User.name.asc() ).all()

    # Update SLA when opening ticket
    update_sla_status(ticket)
    update_sla_alert(ticket)

    if request.method == "POST":
        body = request.form.get( "body", "" ).strip()
        is_internal = ( request.form.get( "is_internal" ) == "true" )
        if not body:
            flash( "Reply cannot be empty.", "danger" )
            return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

        # Customer-visible reply from Pending
        # resumes the SLA clock.
        if ( ticket.status == "pending" and not is_internal ):
            resume_sla(ticket)
            old_status = ticket.status
            ticket.status = "open"
            status_history = TicketStatusHistory( ticket_id=ticket.id, from_status=old_status, to_status="open", changed_by_id=current_user.id )

            status_event = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="status_changed", old_value=old_status, new_value="open" )

            db.session.add(status_history)
            db.session.add(status_event)

        reply = Reply( ticket_id=ticket.id, author_id=current_user.id, body=body, is_internal=is_internal )
        db.session.add(reply)
        history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type=( "internal_note_added" if is_internal else "reply_added" ), old_value=None, new_value=body )

        db.session.add(history)
        update_sla_status(ticket)
        db.session.commit()
        flash( "Reply added successfully.", "success" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )
    return render_template( "tickets/detail.html", ticket=ticket, agents=agents, sla_remaining_seconds=sla_remaining_seconds(ticket) )

# EDIT TICKET
@tickets_bp.route( "/<int:ticket_id>/edit", methods=["GET", "POST"] )
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if not can_access_ticket(ticket):
        flash( "You do not have permission to edit this ticket.", "danger" )
        return redirect( url_for( "tickets.list_tickets" ) )

    agents = User.query.filter_by( role="agent" ).order_by( User.name.asc() ).all()
    if request.method == "POST":
        old_subject = ticket.subject
        old_priority = ticket.priority
        old_category = ticket.category

        subject = request.form.get( "subject", "" ).strip()
        description = request.form.get( "description", "" ).strip()
        requester_name = request.form.get( "requester_name", "" ).strip()
        requester_email = request.form.get( "requester_email", "" ).strip()
        priority = request.form.get( "priority", "medium" ).strip().lower()
        category = request.form.get( "category", "" ).strip()

        if not subject:
            flash( "Subject is required.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        if not description:
            flash( "Description is required.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        if not requester_name:
            flash( "Requester name is required.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        if not requester_email:
            flash( "Requester email is required.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        if not category:
            flash( "Category is required.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        if priority not in { "low", "medium", "high", "urgent" }:
            flash( "Invalid priority.", "danger" )
            return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

        ticket.subject = subject
        ticket.description = description
        ticket.requester_name = requester_name
        ticket.requester_email = requester_email
        ticket.priority = priority
        ticket.category = category

        # Keep SLA target synchronized with priority
        ticket.response_target_minutes = ( get_sla_target(priority) )
        changes = []

        if old_subject != subject:
            changes.append( f"subject: {old_subject} -> {subject}" )

        if old_priority != priority:
            changes.append( f"priority: {old_priority} -> {priority}" )

        if old_category != category:
            changes.append( f"category: {old_category} -> {category}" )

        if changes:
            history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_updated", old_value=None, new_value="; ".join(changes) )
            db.session.add(history)

        update_sla_status(ticket)
        db.session.commit()
        flash( "Ticket updated successfully.", "success" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )
    return render_template( "tickets/edit.html", ticket=ticket, agents=agents )

# CHANGE STATUS
@tickets_bp.route( "/<int:ticket_id>/status", methods=["POST"] )
@login_required
def change_status(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if not can_access_ticket(ticket):
        flash( "You do not have permission to change this ticket.", "danger" )
        return redirect( url_for( "tickets.list_tickets" ) )

    new_status = request.form.get( "status", "" ).strip().lower()
    current_status = ticket.status
    allowed_transitions = { "new": ["open"], "open": ["pending", "resolved"], "pending": ["open", "resolved"], "resolved": ["closed", "open"], "closed": ["open"] }
    valid_statuses = { "new", "open", "pending", "resolved", "closed" }

    if new_status not in valid_statuses:
        flash( "Invalid ticket status.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    # Closed -> Open
    if ( current_status == "closed" and new_status == "open" ):
        if not ticket.closed_at:
            flash( "Closed ticket cannot be reopened because " "its close time is missing.", "danger" )
            return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

        closed_at = make_aware( ticket.closed_at )
        reopen_deadline = ( closed_at + timedelta(days=7) )
        if utc_now() > reopen_deadline:
            flash( "This ticket can no longer be reopened. " "The 7-day reopening window has expired.", "danger" )
            return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

        old_status = ticket.status
        ticket.status = "open"
        ticket.closed_at = None

        # A reopened ticket starts/resumes its SLA clock.
        resume_sla(ticket)
        status_history = TicketStatusHistory( ticket_id=ticket.id, from_status=old_status, to_status="open", changed_by_id=current_user.id )
        history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="status_changed", old_value=old_status, new_value="open" )
        db.session.add(status_history)
        db.session.add(history)

        update_sla_status(ticket)
        db.session.commit()
        flash( "Ticket reopened successfully.", "success" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    # Normal transitions
    if new_status not in allowed_transitions.get( current_status, [] ):
        flash( f"Cannot change status from " f"{current_status.capitalize()} to " f"{new_status.capitalize()}.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    # SLA handling
    if ( current_status != "pending" and new_status == "pending" ):
        pause_sla(ticket)
    elif ( current_status == "pending" and new_status != "pending" ):
        resume_sla(ticket)

    # History
    status_history = TicketStatusHistory( ticket_id=ticket.id, from_status=current_status, to_status=new_status, changed_by_id=current_user.id )

    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="status_changed", old_value=current_status, new_value=new_status )

    db.session.add(status_history)
    db.session.add(history)

    # Close
    if new_status == "closed":
        ticket.closed_at = utc_now()
    else:
        ticket.closed_at = None

    ticket.status = new_status
    update_sla_status(ticket)
    db.session.commit()
    flash( f"Ticket status changed to " f"{new_status.capitalize()}.", "success" )
    return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

# ARCHIVE
@tickets_bp.route( "/<int:ticket_id>/archive", methods=["POST"] )
@login_required
def archive_ticket(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if not can_access_ticket(ticket):
        flash( "You do not have permission to archive this ticket.", "danger" )
        return redirect( url_for( "tickets.list_tickets" ) )

    if ticket.archived_at is not None:
        flash( "Ticket is already archived.", "warning" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    ticket.archived_at = utc_now()
    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_archived", old_value=None, new_value="archived" )

    db.session.add(history)
    db.session.commit()

    flash( "Ticket archived successfully.", "success" )
    return redirect( url_for( "tickets.list_tickets" ) )

# RESTORE
@tickets_bp.route( "/<int:ticket_id>/restore", methods=["POST"] )
@login_required
def restore_ticket(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if not can_access_ticket(ticket):
        flash( "You do not have permission to restore this ticket.", "danger" )
        return redirect( url_for( "tickets.list_tickets" ) )

    if ticket.archived_at is None:
        flash( "Ticket is not archived.", "warning" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    ticket.archived_at = None
    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_restored", old_value="archived", new_value="active" )

    db.session.add(history)
    db.session.commit()

    flash( "Ticket restored successfully.", "success" )
    return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

# REASSIGN
@tickets_bp.route( "/<int:ticket_id>/reassign", methods=["POST"] )
@login_required
def reassign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if current_user.role != "supervisor":
        flash( "Only supervisors can reassign tickets.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    agent_id = request.form.get( "agent_id" )
    if not agent_id:
        flash( "Please select an agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    try:
        agent_id = int(agent_id)
    except ValueError:
        flash( "Invalid agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    agent = User.query.filter_by( id=agent_id, role="agent" ).first()
    if not agent:
        flash( "Selected user is not a valid agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    old_assignee_id = ticket.primary_assignee_id
    if old_assignee_id == agent.id:
        flash( "Ticket is already assigned to this agent.", "warning" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    old_agent = None
    if old_assignee_id:
        old_agent = User.query.get( old_assignee_id )

    ticket.primary_assignee_id = agent.id
    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_reassigned", old_value=( old_agent.name if old_agent else "Unassigned" ), new_value=agent.name )

    db.session.add(history)
    db.session.commit()

    flash( f"Ticket reassigned to {agent.name}.", "success" )
    return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

# ADD COLLABORATOR
@tickets_bp.route( "/<int:ticket_id>/collaborators/add", methods=["POST"] )
@login_required
def add_collaborator(ticket_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if current_user.role != "supervisor":
        flash( "Only supervisors can manage collaborators.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    user_id = request.form.get( "user_id" )
    if not user_id:
        flash( "Please select an agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    try:
        user_id = int(user_id)
    except ValueError:
        flash( "Invalid agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    agent = User.query.filter_by( id=user_id, role="agent" ).first()
    if not agent:
        flash( "Selected user is not a valid agent.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    if ticket.primary_assignee_id == agent.id:
        flash( "The primary assignee cannot also be a collaborator.", "warning" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    existing = TicketCollaborator.query.filter_by( ticket_id=ticket.id, user_id=agent.id ).first()
    if existing:
        flash( "This agent is already a collaborator.", "warning" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    collaborator = TicketCollaborator( ticket_id=ticket.id, user_id=agent.id )
    db.session.add(collaborator)
    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="collaborator_added", old_value=None, new_value=agent.name )

    db.session.add(history)
    db.session.commit()

    flash( f"{agent.name} added as collaborator.", "success" )
    return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

# REMOVE COLLABORATOR
@tickets_bp.route( "/<int:ticket_id>/collaborators/<int:user_id>/remove", methods=["POST"] )
@login_required
def remove_collaborator(ticket_id, user_id):
    ticket = Ticket.query.get_or_404( ticket_id )
    if current_user.role != "supervisor":
        flash( "Only supervisors can manage collaborators.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    collaborator = TicketCollaborator.query.filter_by( ticket_id=ticket.id, user_id=user_id ).first()
    if not collaborator:
        flash( "Collaborator not found.", "danger" )
        return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

    agent = User.query.get( user_id )
    agent_name = ( agent.name if agent else f"User {user_id}" )
    db.session.delete( collaborator )
    history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="collaborator_removed", old_value=agent_name, new_value=None )

    db.session.add(history)
    db.session.commit()

    flash( f"{agent_name} removed as collaborator.", "success" )
    return redirect( url_for( "tickets.ticket_detail", ticket_id=ticket.id ) )

# BULK ACTIONS
@tickets_bp.route( "/bulk-action", methods=["POST"] )
@login_required
def bulk_action():
    if current_user.role != "supervisor":
        flash( "Only supervisors can perform bulk actions.", "danger" )
        return redirect( url_for("tickets.list_tickets") )

    ticket_ids = request.form.getlist( "ticket_ids" )
    action = request.form.get( "action", "" ).strip()
    if not ticket_ids:
        flash( "No tickets were selected.", "warning" )
        return redirect( url_for("tickets.list_tickets") )

    if action not in { "reassign", "close" }:
        flash( "Invalid bulk action.", "danger" )
        return redirect( url_for("tickets.list_tickets") )

    # Bulk Reassign
    if action == "reassign":
        agent_id = request.form.get( "agent_id" )
        try:
            agent_id = int(agent_id)
        except (TypeError, ValueError):
            flash( "Please select a valid agent.", "danger" )
            return redirect( url_for("tickets.list_tickets") )

        agent = User.query.filter_by( id=agent_id, role="agent" ).first()
        if not agent:
            flash( "Selected agent is invalid.", "danger" )
            return redirect( url_for("tickets.list_tickets") )

    success_count = 0
    refused_count = 0
    results = []

    for ticket_id in ticket_ids:
        try:
            ticket_id = int(ticket_id)
        except ValueError:
            refused_count += 1
            results.append({ "ticket": ticket_id, "success": False, "reason": "Invalid ticket ID." })
            continue

        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            refused_count += 1
            results.append({ "ticket": ticket_id, "success": False, "reason": "Ticket not found." })
            continue

        # Archived ticket
        if ticket.archived_at is not None:
            refused_count += 1
            results.append({ "ticket": ticket.id, "success": False, "reason": "Ticket is archived." })
            continue

        # BULK REASSIGN
        if action == "reassign":
            old_agent = None
            if ticket.primary_assignee_id:
                old_agent = User.query.get( ticket.primary_assignee_id )

            if ticket.primary_assignee_id == agent.id:
                refused_count += 1
                results.append({ "ticket": ticket.id, "success": False, "reason": "Already assigned to this agent." })
                continue

            ticket.primary_assignee_id = agent.id
            history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="ticket_reassigned", old_value=( old_agent.name if old_agent else "Unassigned" ), new_value=agent.name )

            db.session.add(history)
            success_count += 1
            results.append({ "ticket": ticket.id, "success": True, "reason": f"Assigned to {agent.name}." })

        # BULK CLOSE
        elif action == "close":
            if ticket.status == "closed":
                refused_count += 1
                results.append({ "ticket": ticket.id, "success": False, "reason": "Ticket is already closed." })
                continue

            # Only valid lifecycle states can be closed
            if ticket.status not in { "resolved" }:
                refused_count += 1
                results.append({ "ticket": ticket.id, "success": False, "reason": ( f"Cannot close ticket from " f"{ticket.status.capitalize()} status." ) })
                continue

            old_status = ticket.status
            ticket.status = "closed"
            ticket.closed_at = utc_now()

            status_history = TicketStatusHistory( ticket_id=ticket.id, from_status=old_status, to_status="closed", changed_by_id=current_user.id )

            history = TicketHistory( ticket_id=ticket.id, actor_id=current_user.id, event_type="status_changed", old_value=old_status, new_value="closed" )

            db.session.add(status_history)
            db.session.add(history)

            success_count += 1
            results.append({ "ticket": ticket.id, "success": True, "reason": "Ticket closed." })
    db.session.commit()

    # Result message
    flash( f"Bulk action completed: " f"{success_count} succeeded, " f"{refused_count} refused.", "info" )
    return render_template( "tickets/bulk_result.html", results=results, success_count=success_count, refused_count=refused_count )

# CSV EXPORT
@tickets_bp.route( "/export" )
@login_required
def export_tickets():
    search = request.args.get( "search", "" ).strip()
    status = request.args.get( "status", "" ).strip().lower()
    priority = request.args.get( "priority", "" ).strip().lower()
    category = request.args.get( "category", "" ).strip()
    assignee = request.args.get( "assignee", "" ).strip()
    sort = request.args.get( "sort", "created" ).strip().lower()

    # Same filtering as queue
    query = Ticket.query.filter( Ticket.archived_at.is_(None) )
    if current_user.role == "agent":
        query = query.filter( or_( Ticket.primary_assignee_id == current_user.id, Ticket.collaborator_links.any( user_id=current_user.id ) ) )

    if search:
        pattern = f"%{search}%"
        query = query.filter( or_( Ticket.subject.ilike(pattern), Ticket.description.ilike(pattern) ) )

    if status in { "new", "open", "pending", "resolved", "closed" }:
        query = query.filter( Ticket.status == status )

    if priority in { "low", "medium", "high", "urgent" }:
        query = query.filter( Ticket.priority == priority )

    if category:
        query = query.filter( Ticket.category == category )

    if assignee:
        try:
            assignee_id = int( assignee )
            query = query.filter( Ticket.primary_assignee_id == assignee_id )
        except ValueError:
            pass

    # Sorting
    if sort == "priority":
        priority_order = case( (Ticket.priority == "urgent", 1), (Ticket.priority == "high", 2), (Ticket.priority == "medium", 3), (Ticket.priority == "low", 4), else_=5 )
        query = query.order_by( priority_order, Ticket.created_at.desc() )
    elif sort == "updated":
        query = query.order_by( Ticket.updated_at.desc() )
    else:
        query = query.order_by( Ticket.created_at.desc() )
    tickets = query.all()

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer( output )
    writer.writerow([ "Ticket ID", "Subject", "Requester", "Requester Email", "Status", "Priority", "Category", "Assignee", "Created At", "Updated At" ])

    for ticket in tickets:
        writer.writerow([ ticket.id, ticket.subject, ticket.requester_name, ticket.requester_email, ticket.status, ticket.priority, ticket.category, ( ticket.primary_assignee.name if ticket.primary_assignee else "Unassigned" ), ticket.created_at, ticket.updated_at ])

    response = Response( output.getvalue(), mimetype="text/csv" )
    response.headers["Content-Disposition"] = ( "attachment; filename=tickets.csv" )
    return response