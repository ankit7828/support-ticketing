# ============================================================
# seed_50.py
#
# Creates 50 realistic demo tickets and related data:
#
#   Users
#   Tickets
#   Replies
#   Collaborators
#   Ticket History
#   Ticket Status History
#   SLA Alerts
#
# Designed for the current SupportDesk models.
# ============================================================

from datetime import datetime, timezone, timedelta
import random

from app import create_app
from app.extensions import db

from app.models import (
    User,
    Ticket,
    Reply,
    TicketCollaborator,
    TicketHistory,
    TicketStatusHistory,
    SLAAlert,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOTAL_TICKETS = 50

random.seed(42)

app = create_app()


# ============================================================
# HELPERS
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)


def make_time(days_ago=0, hours=0, minutes=0):
    return now_utc() - timedelta(
        days=days_ago,
        hours=hours,
        minutes=minutes
    )


def get_or_create_user(name, email, role, password="Demo@123"):
    user = User.query.filter_by(email=email).first()

    if user:
        return user

    user = User(
        name=name,
        email=email,
        role=role
    )

    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    return user


# ============================================================
# USERS
# ============================================================

def create_demo_users():

    supervisor = get_or_create_user(
        "Supervisor",
        "supervisor@demo.com",
        "supervisor"
    )

    alice = get_or_create_user(
        "Alice Agent",
        "alice@demo.com",
        "agent"
    )

    bob = get_or_create_user(
        "Bob Agent",
        "bob@demo.com",
        "agent"
    )

    charlie = get_or_create_user(
        "Charlie Agent",
        "charlie@demo.com",
        "agent"
    )

    riya = get_or_create_user(
        "Riya",
        "riya@demo.com",
        "agent"
    )

    db.session.commit()

    print()
    print("Users ready:")
    print("  supervisor@demo.com")
    print("  alice@demo.com")
    print("  bob@demo.com")
    print("  charlie@demo.com")
    print("  riya@demo.com")

    return supervisor, [alice, bob, charlie, riya]


# ============================================================
# DATA
# ============================================================

SUBJECTS = [
    "Cannot login to account",
    "Password reset request",
    "Application is very slow",
    "Unable to upload document",
    "Payment failed",
    "Invoice amount is incorrect",
    "Account verification problem",
    "Email notifications not working",
    "Dashboard is not loading",
    "API request returning error",
    "Unable to download report",
    "Customer portal unavailable",
    "Two factor authentication issue",
    "Subscription renewal problem",
    "Database connection error",
    "Server response timeout",
    "Incorrect customer information",
    "Unable to change account details",
    "Missing transaction",
    "Mobile application crash",
    "Unable to generate invoice",
    "File attachment not opening",
    "User permissions problem",
    "Access denied to application",
    "Search functionality not working",
]

CATEGORIES = [
    "technical",
    "billing",
    "account",
    "access",
    "general",
]

PRIORITIES = [
    "low",
    "medium",
    "high",
    "urgent",
]

STATUSES = [
    "new",
    "open",
    "pending",
    "resolved",
    "closed",
]

REQUESTER_NAMES = [
    "Rahul Sharma",
    "Amit Das",
    "Priya Sen",
    "Sneha Roy",
    "Arjun Mehta",
    "Neha Gupta",
    "Rohit Singh",
    "Ananya Bose",
    "Vikash Kumar",
    "Karan Patel",
]

REQUESTER_DOMAINS = [
    "example.com",
    "customer.com",
    "demo.com",
]


# ============================================================
# SLA TARGET
# ============================================================

def sla_minutes(priority):

    if priority == "urgent":
        return 60

    if priority == "high":
        return 120

    if priority == "medium":
        return 240

    return 480


# ============================================================
# ADD TICKET HISTORY
# ============================================================

def add_history(
    ticket,
    actor,
    event_type,
    old_value=None,
    new_value=None,
    created_at=None
):

    history = TicketHistory(
        ticket_id=ticket.id,
        actor_id=actor.id,
        event_type=event_type,
        old_value=old_value,
        new_value=new_value,
        created_at=created_at or now_utc()
    )

    db.session.add(history)


# ============================================================
# ADD STATUS HISTORY
# ============================================================

def add_status_history(
    ticket,
    actor,
    from_status,
    to_status,
    changed_at
):

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=from_status,
        to_status=to_status,
        changed_by_id=actor.id,
        changed_at=changed_at
    )

    db.session.add(history)


# ============================================================
# ADD REPLY
# ============================================================

def add_reply(
    ticket,
    author,
    body,
    is_internal,
    created_at
):

    reply = Reply(
        ticket_id=ticket.id,
        author_id=author.id,
        body=body,
        is_internal=is_internal,
        created_at=created_at
    )

    db.session.add(reply)


# ============================================================
# ADD COLLABORATOR
# ============================================================

def add_collaborator(ticket, agent, added_at):

    # Do not add primary assignee as collaborator.
    if ticket.primary_assignee_id == agent.id:
        return

    existing = TicketCollaborator.query.filter_by(
        ticket_id=ticket.id,
        user_id=agent.id
    ).first()

    if existing:
        return

    collaborator = TicketCollaborator(
        ticket_id=ticket.id,
        user_id=agent.id,
        added_at=added_at
    )

    db.session.add(collaborator)


# ============================================================
# ADD SLA ALERT
# ============================================================

def add_sla_alert(
    ticket,
    alert_type,
    acknowledged=False,
    acknowledged_by=None,
    created_at=None
):

    alert = SLAAlert(
        ticket_id=ticket.id,
        alert_type=alert_type,
        acknowledged=acknowledged,
        created_at=created_at or now_utc()
    )

    if acknowledged and acknowledged_by:

        alert.acknowledged_by_id = acknowledged_by.id

        alert.acknowledged_at = (
            (created_at or now_utc())
            + timedelta(minutes=10)
        )

    db.session.add(alert)


# ============================================================
# CREATE STATUS HISTORY
# ============================================================

def create_lifecycle_history(
    ticket,
    actor,
    status,
    created_at
):

    # Always begin with New.
    add_status_history(
        ticket,
        actor,
        None,
        "new",
        created_at
    )

    add_history(
        ticket,
        actor,
        "status_change",
        None,
        "new",
        created_at
    )

    current = "new"

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    if status == "new":
        return

    # --------------------------------------------------------
    # OPEN
    # --------------------------------------------------------

    open_time = created_at + timedelta(minutes=15)

    add_status_history(
        ticket,
        actor,
        current,
        "open",
        open_time
    )

    add_history(
        ticket,
        actor,
        "status_change",
        current,
        "open",
        open_time
    )

    current = "open"

    if status == "open":
        return

    # --------------------------------------------------------
    # PENDING
    # --------------------------------------------------------

    if status == "pending":

        pending_time = (
            created_at
            + timedelta(hours=3)
        )

        add_status_history(
            ticket,
            actor,
            current,
            "pending",
            pending_time
        )

        add_history(
            ticket,
            actor,
            "status_change",
            current,
            "pending",
            pending_time
        )

        return

    # --------------------------------------------------------
    # RESOLVED
    # --------------------------------------------------------

    resolved_time = (
        created_at
        + timedelta(hours=8)
    )

    add_status_history(
        ticket,
        actor,
        current,
        "resolved",
        resolved_time
    )

    add_history(
        ticket,
        actor,
        "status_change",
        current,
        "resolved",
        resolved_time
    )

    current = "resolved"

    if status == "resolved":
        return

    # --------------------------------------------------------
    # CLOSED
    # --------------------------------------------------------

    closed_time = (
        created_at
        + timedelta(hours=10)
    )

    add_status_history(
        ticket,
        actor,
        current,
        "closed",
        closed_time
    )

    add_history(
        ticket,
        actor,
        "status_change",
        current,
        "closed",
        closed_time
    )


# ============================================================
# CREATE ONE TICKET
# ============================================================

def create_ticket(
    number,
    supervisor,
    agents
):

    # --------------------------------------------------------
    # Spread tickets across approximately 8 weeks.
    #
    # This is important for the dashboard's:
    #
    # "Tickets Resolved - Last 8 Weeks"
    #
    # chart.
    # --------------------------------------------------------

    days_ago = random.randint(1, 55)

    created_at = make_time(
        days_ago=days_ago,
        hours=random.randint(0, 20),
        minutes=random.randint(0, 59)
    )

    subject = random.choice(SUBJECTS)

    # Add variation to subjects.
    if number > len(SUBJECTS):

        subject = (
            subject
            + f" #{number}"
        )

    requester_name = random.choice(
        REQUESTER_NAMES
    )

    requester_email = (
        requester_name.lower()
        .replace(" ", ".")
        + "@"
        + random.choice(REQUESTER_DOMAINS)
    )

    priority = random.choice(
        PRIORITIES
    )

    category = random.choice(
        CATEGORIES
    )

    # --------------------------------------------------------
    # Balanced status distribution.
    #
    # This gives the dashboard meaningful numbers.
    # --------------------------------------------------------

    status_cycle = [
        "new",
        "open",
        "open",
        "pending",
        "resolved",
        "resolved",
        "closed",
        "closed",
        "closed",
    ]

    status = status_cycle[
        (number - 1) % len(status_cycle)
    ]

    assignee = random.choice(agents)

    description = (
        f"Customer reported an issue regarding "
        f"'{subject.lower()}'. "
        f"The support team needs to investigate "
        f"the problem and provide an appropriate "
        f"resolution. "
        f"This is demo ticket #{number}."
    )

    # --------------------------------------------------------
    # SLA
    # --------------------------------------------------------

    target_minutes = sla_minutes(
        priority
    )

    response_started_at = (
        created_at
        + timedelta(minutes=5)
    )

    # Some pending tickets have a paused clock.
    if status == "pending":

        response_paused_at = (
            created_at
            + timedelta(hours=3)
        )

        response_paused_seconds = (
            random.randint(30, 180) * 60
        )

    else:

        response_paused_at = None

        response_paused_seconds = 0

    # Make a realistic mixture of breached/non-breached.
    response_breached = (
        number % 4 == 0
        or number % 9 == 0
    )

    # --------------------------------------------------------
    # Ticket
    # --------------------------------------------------------

    ticket = Ticket(
        subject=subject,
        description=description,
        requester_name=requester_name,
        requester_email=requester_email,
        priority=priority,
        category=category,
        status=status,
        primary_assignee_id=assignee.id,
        created_by_id=supervisor.id,
        created_at=created_at,
        updated_at=created_at + timedelta(
            hours=random.randint(1, 24)
        ),
        closed_at=(
            created_at + timedelta(hours=10)
            if status == "closed"
            else None
        ),
        archived_at=None,

        response_started_at=response_started_at,
        response_target_minutes=target_minutes,
        response_paused_at=response_paused_at,
        response_paused_seconds=response_paused_seconds,
        response_breached=response_breached
    )

    db.session.add(ticket)

    db.session.flush()

    # --------------------------------------------------------
    # Initial ticket history
    # --------------------------------------------------------

    add_history(
        ticket,
        supervisor,
        "created",
        None,
        "Ticket created",
        created_at
    )

    # --------------------------------------------------------
    # Lifecycle history
    # --------------------------------------------------------

    create_lifecycle_history(
        ticket,
        assignee,
        status,
        created_at
    )

    # --------------------------------------------------------
    # Reassignment history for some tickets
    # --------------------------------------------------------

    if number % 5 == 0:

        old_agent = random.choice(
            [
                a for a in agents
                if a.id != assignee.id
            ]
        )

        reassignment_time = (
            created_at
            + timedelta(minutes=30)
        )

        add_history(
            ticket,
            supervisor,
            "reassignment",
            old_agent.name,
            assignee.name,
            reassignment_time
        )

    # --------------------------------------------------------
    # Replies
    # --------------------------------------------------------

    first_reply_time = (
        created_at
        + timedelta(minutes=20)
    )

    add_reply(
        ticket,
        assignee,
        (
            "Hello, thank you for contacting "
            "SupportDesk. We have received your "
            "request and are investigating the issue."
        ),
        False,
        first_reply_time
    )

    add_history(
        ticket,
        assignee,
        "reply",
        None,
        "Customer-visible reply",
        first_reply_time
    )

    # Internal note for many tickets.
    if number % 2 == 0:

        internal_time = (
            created_at
            + timedelta(hours=1)
        )

        add_reply(
            ticket,
            assignee,
            (
                "Internal note: investigating the "
                "reported issue. This is a demo "
                "internal note."
            ),
            True,
            internal_time
        )

        add_history(
            ticket,
            assignee,
            "internal_note",
            None,
            "Internal note added",
            internal_time
        )

    # Customer-visible second reply for resolved/closed.
    if status in ["resolved", "closed"]:

        final_reply_time = (
            created_at
            + timedelta(hours=7)
        )

        add_reply(
            ticket,
            assignee,
            (
                "The reported issue has been "
                "investigated and resolved. "
                "Please let us know if you need "
                "any further assistance."
            ),
            False,
            final_reply_time
        )

        add_history(
            ticket,
            assignee,
            "reply",
            None,
            "Resolution reply",
            final_reply_time
        )

    # --------------------------------------------------------
    # Collaborators
    #
    # Add collaborators to roughly half the tickets.
    # --------------------------------------------------------

    if number % 2 == 0:

        possible_collaborators = [
            agent
            for agent in agents
            if agent.id != assignee.id
        ]

        if possible_collaborators:

            collaborator_count = (
                1
                if number % 4 != 0
                else 2
            )

            selected = random.sample(
                possible_collaborators,
                min(
                    collaborator_count,
                    len(possible_collaborators)
                )
            )

            for collaborator in selected:

                add_collaborator(
                    ticket,
                    collaborator,
                    created_at + timedelta(
                        hours=1
                    )
                )

                add_history(
                    ticket,
                    supervisor,
                    "collaborator_added",
                    None,
                    collaborator.name,
                    created_at + timedelta(
                        hours=1
                    )
                )

    # --------------------------------------------------------
    # SLA ALERTS
    #
    # Every breached ticket gets an alert.
    # Some alerts are acknowledged and some remain active.
    # --------------------------------------------------------

    if response_breached:

        # Mix active and acknowledged alerts.
        should_acknowledge = (
            number % 3 == 0
        )

        if should_acknowledge:

            add_sla_alert(
                ticket,
                "breach",
                acknowledged=True,
                acknowledged_by=assignee,
                created_at=created_at + timedelta(
                    hours=5
                )
            )

        else:

            add_sla_alert(
                ticket,
                "breach",
                acknowledged=False,
                created_at=created_at + timedelta(
                    hours=5
                )
            )

    # Some tickets are close to SLA breach.
    elif number % 7 == 0:

        add_sla_alert(
            ticket,
            "warning",
            acknowledged=False,
            created_at=created_at + timedelta(
                hours=4
            )
        )

    return ticket


# ============================================================
# MAIN
# ============================================================

with app.app_context():

    print()
    print("=" * 60)
    print("CREATING 50 DEMO TICKETS")
    print("=" * 60)

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    supervisor, agents = create_demo_users()

    # --------------------------------------------------------
    # CREATE TICKETS
    # --------------------------------------------------------

    created_tickets = []

    for number in range(
        1,
        TOTAL_TICKETS + 1
    ):

        ticket = create_ticket(
            number,
            supervisor,
            agents
        )

        created_tickets.append(
            ticket
        )

        # Commit in batches.
        if number % 10 == 0:

            db.session.commit()

            print(
                f"  Created {number}/{TOTAL_TICKETS} tickets..."
            )

    db.session.commit()

    # --------------------------------------------------------
    # FINAL COUNTS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DEMO DATA CREATED SUCCESSFULLY")
    print("=" * 60)

    print()
    print("Tickets:")
    print(
        f"  Total: {Ticket.query.count()}"
    )

    print()
    print("Replies:")
    print(
        f"  Total: {Reply.query.count()}"
    )

    print()
    print("Collaborators:")
    print(
        f"  Total: {TicketCollaborator.query.count()}"
    )

    print()
    print("Ticket History:")
    print(
        f"  Total: {TicketHistory.query.count()}"
    )

    print()
    print("Status History:")
    print(
        f"  Total: {TicketStatusHistory.query.count()}"
    )

    print()
    print("SLA Alerts:")
    print(
        f"  Total: {SLAAlert.query.count()}"
    )

    print()
    print("Ticket Status Breakdown:")

    for status in STATUSES:

        count = Ticket.query.filter_by(
            status=status
        ).count()

        print(
            f"  {status.capitalize():10} : {count}"
        )

    print()
    print("Priority Breakdown:")

    for priority in PRIORITIES:

        count = Ticket.query.filter_by(
            priority=priority
        ).count()

        print(
            f"  {priority.capitalize():10} : {count}"
        )

    print()
    print("Category Breakdown:")

    for category in CATEGORIES:

        count = Ticket.query.filter_by(
            category=category
        ).count()

        print(
            f"  {category.capitalize():10} : {count}"
        )

    print()
    print("Agent Workload:")

    for agent in agents:

        count = Ticket.query.filter_by(
            primary_assignee_id=agent.id
        ).count()

        print(
            f"  {agent.name:20} : {count}"
        )

    print()
    print("=" * 60)
    print("LOGIN")
    print("=" * 60)

    print()
    print("Supervisor:")
    print("  Email    : supervisor@demo.com")
    print("  Password : Demo@123")

    print()
    print("Agents:")
    print("  alice@demo.com   / Demo@123")
    print("  bob@demo.com     / Demo@123")
    print("  charlie@demo.com / Demo@123")
    print("  riya@demo.com    / Demo@123")

    print()
    print("=" * 60)