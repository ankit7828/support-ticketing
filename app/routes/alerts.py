from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import SLAAlert


alerts_bp = Blueprint(
    "alerts",
    __name__,
    url_prefix="/alerts"
)


# ============================================================
# ALERT LIST
# ============================================================

@alerts_bp.route("/")
@login_required
def index():

    query = SLAAlert.query.filter_by(
        acknowledged=False
    )

    # --------------------------------------------------------
    # AGENT:
    # Only alerts for tickets assigned to this agent.
    #
    # SUPERVISOR:
    # Can see all alerts.
    # --------------------------------------------------------

    if current_user.role == "agent":

        query = query.filter(
            SLAAlert.ticket.has(
                primary_assignee_id=current_user.id
            )
        )

    alerts = (
        query
        .order_by(
            SLAAlert.created_at.desc()
        )
        .all()
    )

    return render_template(
        "alerts/index.html",
        alerts=alerts
    )


# ============================================================
# ACKNOWLEDGE ALERT
# ============================================================

@alerts_bp.route(
    "/<int:alert_id>/acknowledge",
    methods=["POST"]
)
@login_required
def acknowledge(alert_id):

    alert = SLAAlert.query.get_or_404(
        alert_id
    )

    # --------------------------------------------------------
    # CHECK IF ALREADY ACKNOWLEDGED
    # --------------------------------------------------------

    if alert.acknowledged:

        flash(
            "This alert has already been acknowledged.",
            "info"
        )

        return redirect(
            url_for("alerts.index")
        )


    # --------------------------------------------------------
    # AGENT PERMISSION
    #
    # An agent can acknowledge only an alert belonging
    # to a ticket where they are the primary assignee.
    #
    # Supervisors can acknowledge any alert.
    # --------------------------------------------------------

    if current_user.role == "agent":

        if (
            alert.ticket is None
            or
            alert.ticket.primary_assignee_id
            != current_user.id
        ):

            flash(
                "You can only acknowledge alerts for tickets assigned to you.",
                "danger"
            )

            return redirect(
                url_for("alerts.index")
            )


    # --------------------------------------------------------
    # ACKNOWLEDGE THE ALERT
    #
    # IMPORTANT:
    # This DOES NOT change the ticket status.
    #
    # For example:
    #
    # Ticket:
    #     Status = Open
    #     SLA = Breached
    #
    # After acknowledgement:
    #
    #     Status = Open
    #     SLA = Breached
    #     Alert = Acknowledged
    #
    # The ticket must be resolved separately.
    # --------------------------------------------------------

    alert.acknowledged = True

    alert.acknowledged_at = datetime.now(
        timezone.utc
    )

    # Keep compatibility with the current SLAAlert model.
    if hasattr(
        alert,
        "acknowledged_by_id"
    ):

        alert.acknowledged_by_id = current_user.id


    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.session.commit()


    flash(
        "SLA alert acknowledged successfully.",
        "success"
    )


    return redirect(
        url_for("alerts.index")
    )