import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import click
from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DATABASE = INSTANCE_DIR / "church_helpdesk.sqlite3"
SETTINGS_PATH = BASE_DIR / "demo_settings.json"

DEFAULT_CATEGORIES = [
    "Care / Pastoral Care",
    "Care Committee",
    "Property / Safety",
    "Technology",
    "Worship / Music",
    "Children and Youth RE",
    "Adult RE",
    "Hospitality",
    "Membership",
    "Social Justice",
    "Stewardship / Finance",
    "Events / Calendar",
    "General",
]
OTHER_CATEGORY = "Other"

PRIORITIES = ["Low", "Normal", "High", "Urgent"]
STATUSES = ["New", "In Review", "Scheduled", "Waiting", "Resolved"]
ASSIGNEES = [
    "Unassigned",
    "Technology Team",
    "Safety Team",
    "Media Team",
    "Care Team",
    "Office Admin",
    "Events Team",
]
DEFAULT_ADMIN_USERS = ["Staff", "Shalin", "Treo", "Wayne", "David"]
SORT_COLUMNS = [
    {"key": "ticket", "label": "Ticket"},
    {"key": "request", "label": "Request"},
    {"key": "category", "label": "Category"},
    {"key": "priority", "label": "Priority"},
    {"key": "status", "label": "Status"},
    {"key": "assignee", "label": "Assignee"},
    {"key": "updated", "label": "Updated"},
]
SORT_COLUMN_KEYS = {column["key"] for column in SORT_COLUMNS}
DEFAULT_SORT_KEY = "priority"
DEFAULT_SORT_DIRECTION = "desc"
SORT_ORDER_SQL = {
    "ticket": {
        "asc": "ticket_number COLLATE NOCASE ASC",
        "desc": "ticket_number COLLATE NOCASE DESC",
    },
    "request": {
        "asc": "lower(title) ASC, lower(requester_name) ASC",
        "desc": "lower(title) DESC, lower(requester_name) DESC",
    },
    "category": {
        "asc": "lower(category) ASC, lower(title) ASC",
        "desc": "lower(category) DESC, lower(title) DESC",
    },
    "priority": {
        "asc": "CASE priority WHEN 'Low' THEN 1 WHEN 'Normal' THEN 2 WHEN 'High' THEN 3 WHEN 'Urgent' THEN 4 ELSE 5 END ASC",
        "desc": "CASE priority WHEN 'Low' THEN 1 WHEN 'Normal' THEN 2 WHEN 'High' THEN 3 WHEN 'Urgent' THEN 4 ELSE 5 END DESC",
    },
    "status": {
        "asc": "CASE status WHEN 'New' THEN 1 WHEN 'In Review' THEN 2 WHEN 'Scheduled' THEN 3 WHEN 'Waiting' THEN 4 WHEN 'Resolved' THEN 5 ELSE 6 END ASC",
        "desc": "CASE status WHEN 'New' THEN 1 WHEN 'In Review' THEN 2 WHEN 'Scheduled' THEN 3 WHEN 'Waiting' THEN 4 WHEN 'Resolved' THEN 5 ELSE 6 END DESC",
    },
    "assignee": {
        "asc": "lower(assignee) ASC",
        "desc": "lower(assignee) DESC",
    },
    "updated": {
        "asc": "updated_at ASC",
        "desc": "updated_at DESC",
    },
}

DEFAULT_SETTINGS = {
    "church_name": "UUCH Help Desk",
    "staff_notification_email": "helpdesk-staff@example.com",
    "requester_reply_email": "helpdesk@example.com",
    "notification_mode": "Preview only",
    "public_contact_instructions": (
        "For emergencies or immediate safety concerns, contact local emergency "
        "services or church leadership directly."
    ),
    "team_labels": ASSIGNEES,
    "category_labels": DEFAULT_CATEGORIES,
    "admin_users": DEFAULT_ADMIN_USERS,
}

UUCH_CONTACT = {
    "name": "Unitarian Universalist Church of Huntsville",
    "tagline": "A liberal religion and Welcoming Congregation in Huntsville, AL",
    "address": "3921 Broadmor Rd., Huntsville AL, 35810",
    "mailing_address": "P. O. Box 5545, Huntsville, AL 35814",
    "phone": "(256) 534-0508",
    "email": "uuch@uuch.org",
    "service_time": "Sunday Services: 10:45am",
    "website_url": "https://uuch.org/",
    "contact_url": "https://uuch.org/about-us/contact/",
    "donate_url": "https://uuch.org/connecting/donate/",
    "accessibility_url": "https://uuch.org/about-us/access/",
    "privacy_url": "https://uuch.org/website-privacy-policy/",
    "logo_url": "https://uuch.org/wp-content/uploads/2016/02/tmpLogo5.png",
}

DEMO_SECRET_KEY = "church-helpdesk-dev"
DEMO_STAFF_PASSWORD = "church-demo"
DEFAULT_MAX_TICKETS = 30


def configured_max_tickets():
    value = os.environ.get("MAX_TICKETS")
    if not value:
        return DEFAULT_MAX_TICKETS
    try:
        return max(1, int(value))
    except ValueError:
        return DEFAULT_MAX_TICKETS


app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.config.update(
    DATABASE=str(DATABASE),
    SECRET_KEY=os.environ.get("SECRET_KEY") or DEMO_SECRET_KEY,
    STAFF_PASSWORD=os.environ.get("STAFF_PASSWORD") or DEMO_STAFF_PASSWORD,
    MAX_TICKETS=configured_max_tickets(),
)


def is_production_environment():
    return (
        os.environ.get("APP_ENV", "").lower() == "production"
        or os.environ.get("FLASK_ENV", "").lower() == "production"
        or "K_SERVICE" in os.environ
    )


def validate_runtime_config():
    if not is_production_environment():
        return

    unsafe = []
    if app.config["SECRET_KEY"] == DEMO_SECRET_KEY:
        unsafe.append("SECRET_KEY")
    if app.config["STAFF_PASSWORD"] == DEMO_STAFF_PASSWORD:
        unsafe.append("STAFF_PASSWORD")

    if unsafe:
        joined = ", ".join(unsafe)
        raise RuntimeError(f"Production deployment requires explicit values for: {joined}")


validate_runtime_config()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def as_iso(value=None):
    return (value or utc_now()).isoformat()


def normalize_settings(data=None):
    settings = DEFAULT_SETTINGS | (data or {})

    teams = settings.get("team_labels") or DEFAULT_SETTINGS["team_labels"]
    clean_teams = []
    for team in teams:
        team = str(team).strip()
        if team and team not in clean_teams:
            clean_teams.append(team)
    if "Unassigned" not in clean_teams:
        clean_teams.insert(0, "Unassigned")
    settings["team_labels"] = clean_teams

    categories = settings.get("category_labels") or DEFAULT_SETTINGS["category_labels"]
    clean_categories = []
    for category in categories:
        category = str(category).strip()
        if category and category != OTHER_CATEGORY and category not in clean_categories:
            clean_categories.append(category)
    if not clean_categories:
        clean_categories = DEFAULT_CATEGORIES.copy()
    clean_categories.append(OTHER_CATEGORY)
    settings["category_labels"] = clean_categories

    admins = settings.get("admin_users") or DEFAULT_SETTINGS["admin_users"]
    clean_admins = []
    for admin in admins:
        admin = str(admin).strip()
        if admin and admin not in clean_admins:
            clean_admins.append(admin)
    if not clean_admins:
        clean_admins = DEFAULT_ADMIN_USERS.copy()
    settings["admin_users"] = clean_admins

    return settings


def load_settings():
    if SETTINGS_PATH.exists():
        try:
            return normalize_settings(json.loads(SETTINGS_PATH.read_text()))
        except json.JSONDecodeError:
            return normalize_settings()
    settings = normalize_settings()
    save_settings(settings)
    return settings


def save_settings(settings):
    normalized = normalize_settings(settings)
    SETTINGS_PATH.write_text(json.dumps(normalized, indent=2) + "\n")
    return normalized


def get_assignees():
    return load_settings()["team_labels"]


def get_categories():
    return load_settings()["category_labels"]


def get_request_team_choices():
    return [team for team in get_assignees() if team != "Unassigned"]


def count_tickets():
    return get_db().execute("SELECT COUNT(*) FROM tickets").fetchone()[0]


def get_db():
    if "db" not in g:
        INSTANCE_DIR.mkdir(exist_ok=True)
        db = sqlite3.connect(app.config["DATABASE"])
        db.row_factory = sqlite3.Row
        g.db = db
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def staff_logged_in():
    return session.get("staff_authenticated") is True


def safe_next_url(value):
    if value and value.startswith("/") and not value.startswith("//"):
        return value
    return url_for("tickets")


def staff_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not staff_logged_in():
            flash("Please sign in to view the staff dashboard.", "error")
            return redirect(url_for("staff_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE,
            requester_name TEXT NOT NULL,
            contact TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            ministry TEXT,
            location TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            assignee TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            visibility TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            event TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            audience TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id) ON DELETE CASCADE
        );
        """
    )
    db.commit()


def reset_database():
    db = get_db()
    db.executescript(
        """
        DROP TABLE IF EXISTS notifications;
        DROP TABLE IF EXISTS activity;
        DROP TABLE IF EXISTS comments;
        DROP TABLE IF EXISTS tickets;
        """
    )
    db.commit()
    init_db()
    seed_demo_data(force=True)


def choice_or_default(value, choices, default):
    return value if value in choices else default


def normalize_sort_state(sort_key=None, direction=None):
    if sort_key not in SORT_COLUMN_KEYS:
        sort_key = DEFAULT_SORT_KEY
    if direction not in {"asc", "desc"}:
        direction = DEFAULT_SORT_DIRECTION
    return {"key": sort_key, "direction": direction}


def ticket_sort_clause(sort_state):
    order_sql = SORT_ORDER_SQL[sort_state["key"]][sort_state["direction"]]
    tie_direction = "ASC" if sort_state["direction"] == "asc" else "DESC"
    if sort_state["key"] == "updated":
        return f"{order_sql}, id {tie_direction}"
    return f"{order_sql}, updated_at DESC, id DESC"


def create_ticket(data, comments=None, activity=None, created_at=None):
    db = get_db()
    created = created_at or utc_now()
    now = as_iso(created)
    cur = db.execute(
        """
        INSERT INTO tickets (
            requester_name, contact, category, priority, ministry, location,
            title, description, status, assignee, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["requester_name"].strip(),
            data["contact"].strip(),
            data["category"],
            data["priority"],
            data.get("ministry", "").strip(),
            data.get("location", "").strip(),
            data["title"].strip(),
            data["description"].strip(),
            data.get("status", "New"),
            data.get("assignee", "Unassigned"),
            now,
            now,
        ),
    )
    ticket_id = cur.lastrowid
    ticket_number = f"CHD-{created.year}-{ticket_id:04d}"
    db.execute(
        "UPDATE tickets SET ticket_number = ? WHERE id = ?",
        (ticket_number, ticket_id),
    )

    events = activity or ["Request submitted"]
    for event in events:
        db.execute(
            "INSERT INTO activity (ticket_id, event, created_at) VALUES (?, ?, ?)",
            (ticket_id, event, now),
        )

    for comment in comments or []:
        db.execute(
            """
            INSERT INTO comments (ticket_id, author, body, visibility, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                comment["author"],
                comment["body"],
                comment.get("visibility", "Internal"),
                comment.get("created_at", now),
            ),
        )

    ticket = get_ticket(ticket_id)
    queue_new_ticket_notifications(ticket, now)
    db.commit()
    return ticket


def get_ticket(ticket_id):
    return get_db().execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()


def get_comments(ticket_id):
    return get_db().execute(
        "SELECT * FROM comments WHERE ticket_id = ? ORDER BY created_at DESC",
        (ticket_id,),
    ).fetchall()


def get_activity(ticket_id):
    return get_db().execute(
        "SELECT * FROM activity WHERE ticket_id = ? ORDER BY created_at DESC, id DESC",
        (ticket_id,),
    ).fetchall()


def create_notification(ticket_id, audience, recipient, subject, body, created_at=None):
    get_db().execute(
        """
        INSERT INTO notifications (
            ticket_id, audience, recipient, subject, body, status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            audience,
            recipient,
            subject,
            body,
            load_settings()["notification_mode"],
            created_at or as_iso(),
        ),
    )


def queue_new_ticket_notifications(ticket, created_at):
    settings = load_settings()
    ticket_url = f"/tickets/{ticket['id']}"
    create_notification(
        ticket["id"],
        "Staff",
        settings["staff_notification_email"],
        f"New help request {ticket['ticket_number']}: {ticket['title']}",
        (
            f"{ticket['requester_name']} submitted a {ticket['priority'].lower()} "
            f"{ticket['category']} request.\n\n"
            f"Request: {ticket['title']}\n"
            f"Ministry: {ticket['ministry'] or 'Not specified'}\n"
            f"Location: {ticket['location'] or 'Not specified'}\n"
            f"Open in dashboard: {ticket_url}"
        ),
        created_at,
    )
    create_notification(
        ticket["id"],
        "Requester",
        ticket["contact"],
        f"Request received: {ticket['ticket_number']}",
        (
            f"Thank you for contacting {settings['church_name']}. "
            f"Your request has been received as {ticket['ticket_number']}.\n\n"
            f"Request: {ticket['title']}\n"
            "Church staff will review it and follow up using the contact information provided."
        ),
        created_at,
    )


def queue_ticket_update_notifications(ticket, changes, created_at):
    if not changes:
        return
    settings = load_settings()
    change_text = "\n".join(f"- {change}" for change in changes)
    create_notification(
        ticket["id"],
        "Requester",
        ticket["contact"],
        f"Update on {ticket['ticket_number']}",
        (
            f"There is an update on your request, {ticket['ticket_number']}.\n\n"
            f"{change_text}\n\n"
            "Church staff will continue to follow up as needed."
        ),
        created_at,
    )
    create_notification(
        ticket["id"],
        "Staff",
        settings["staff_notification_email"],
        f"Ticket updated: {ticket['ticket_number']}",
        f"{ticket['title']}\n\n{change_text}",
        created_at,
    )


def queue_comment_notification(ticket, author, body, visibility, created_at):
    settings = load_settings()
    if visibility == "Public":
        create_notification(
            ticket["id"],
            "Requester",
            ticket["contact"],
            f"New comment on {ticket['ticket_number']}",
            f"{author} added a comment on your request:\n\n{body}",
            created_at,
        )
        return

    create_notification(
        ticket["id"],
        "Staff",
        settings["staff_notification_email"],
        f"Internal note added to {ticket['ticket_number']}",
        f"{author} added an internal note:\n\n{body}",
        created_at,
    )


def list_notifications():
    return get_db().execute(
        """
        SELECT
            notifications.*,
            tickets.ticket_number,
            tickets.title
        FROM notifications
        JOIN tickets ON tickets.id = notifications.ticket_id
        ORDER BY notifications.created_at DESC, notifications.id DESC
        """
    ).fetchall()


def seed_demo_data(force=False):
    db = get_db()
    existing = db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    if existing and not force:
        return

    now = utc_now()
    samples = [
        {
            "data": {
                "requester_name": "Angela Brooks",
                "contact": "angela@example.com",
                "category": "Property / Safety",
                "priority": "High",
                "ministry": "Children's Ministry",
                "location": "Education Wing Room 204",
                "title": "Classroom thermostat not cooling",
                "description": "The room has been warm for the last two Sundays, especially during the second service.",
                "status": "Scheduled",
                "assignee": "Safety Team",
            },
            "created_at": now - timedelta(days=3, hours=2),
            "activity": [
                "Request submitted",
                "Assigned to Safety Team",
                "Status changed to Scheduled",
            ],
            "comments": [
                {
                    "author": "Safety Team",
                    "body": "HVAC vendor is scheduled to check the room before Wednesday night programming.",
                }
            ],
        },
        {
            "data": {
                "requester_name": "Marcus Lee",
                "contact": "marcus@example.com",
                "category": "Technology",
                "priority": "Urgent",
                "ministry": "Worship Team",
                "location": "Sanctuary booth",
                "title": "Slides computer froze during rehearsal",
                "description": "ProPresenter locked up twice during rehearsal. We need confidence monitor output checked before Sunday.",
                "status": "In Review",
                "assignee": "Technology Team",
            },
            "created_at": now - timedelta(days=1, hours=5),
            "activity": ["Request submitted", "Assigned to Technology Team"],
            "comments": [
                {
                    "author": "Technology Team",
                    "body": "Reviewing logs and checking the display adapter configuration.",
                }
            ],
        },
        {
            "data": {
                "requester_name": "Natalie Green",
                "contact": "555-0147",
                "category": "Events / Calendar",
                "priority": "Normal",
                "ministry": "Women's Bible Study",
                "location": "Fellowship Hall",
                "title": "Room setup for Thursday gathering",
                "description": "Please set up eight round tables, coffee service, and a sign-in table near the entrance.",
                "status": "Waiting",
                "assignee": "Events Team",
            },
            "created_at": now - timedelta(days=2, hours=4),
            "activity": ["Request submitted", "Waiting on attendance estimate"],
            "comments": [
                {
                    "author": "Events Team",
                    "body": "Can you confirm whether childcare tables are needed as well?",
                    "visibility": "Public",
                }
            ],
        },
        {
            "data": {
                "requester_name": "David Kim",
                "contact": "david@example.com",
                "category": "Stewardship / Finance",
                "priority": "Low",
                "ministry": "Missions",
                "location": "Church office",
                "title": "Reimbursement form question",
                "description": "Need confirmation on which budget code to use for the community pantry receipt.",
                "status": "Resolved",
                "assignee": "Office Admin",
            },
            "created_at": now - timedelta(days=5, hours=7),
            "activity": ["Request submitted", "Assigned to Office Admin", "Status changed to Resolved"],
            "comments": [
                {
                    "author": "Office Admin",
                    "body": "Use the local outreach budget code and attach the receipt to the reimbursement form.",
                }
            ],
        },
        {
            "data": {
                "requester_name": "Sophia Martinez",
                "contact": "sophia@example.com",
                "category": "Care / Pastoral Care",
                "priority": "Normal",
                "ministry": "Hospitality",
                "location": "Narthex",
                "title": "Prayer request follow-up",
                "description": "A visitor asked for someone to follow up this week about a family illness.",
                "status": "New",
                "assignee": "Care Team",
            },
            "created_at": now - timedelta(hours=8),
            "activity": ["Request submitted"],
            "comments": [],
        },
    ]

    for sample in samples:
        create_ticket(
            sample["data"],
            comments=sample.get("comments"),
            activity=sample.get("activity"),
            created_at=sample["created_at"],
        )


def list_tickets(filters, sort_state):
    db = get_db()
    clauses = []
    params = []

    for field in ("status", "assignee", "priority"):
        value = filters.get(field)
        if value and value != "All":
            clauses.append(f"{field} = ?")
            params.append(value)

    query = filters.get("q", "").strip()
    if query:
        like = f"%{query.lower()}%"
        clauses.append(
            "(lower(ticket_number) LIKE ? OR lower(title) LIKE ? OR lower(requester_name) LIKE ? OR lower(ministry) LIKE ?)"
        )
        params.extend([like, like, like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    order_sql = ticket_sort_clause(sort_state)
    return db.execute(
        f"""
        SELECT *
        FROM tickets
        {where}
        ORDER BY {order_sql}
        """,
        params,
    ).fetchall()


def dashboard_stats():
    db = get_db()
    rows = db.execute("SELECT status, COUNT(*) AS count FROM tickets GROUP BY status").fetchall()
    by_status = {row["status"]: row["count"] for row in rows}
    total = sum(by_status.values())
    open_count = total - by_status.get("Resolved", 0)
    urgent_count = db.execute(
        "SELECT COUNT(*) FROM tickets WHERE priority = 'Urgent' AND status != 'Resolved'"
    ).fetchone()[0]
    return {
        "total": total,
        "open": open_count,
        "urgent": urgent_count,
        "resolved": by_status.get("Resolved", 0),
        "by_status": by_status,
    }


@app.template_filter("pretty_datetime")
def pretty_datetime(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    return dt.strftime("%b %d, %Y %I:%M %p UTC")


@app.context_processor
def inject_choices():
    return {
        "categories": get_categories(),
        "priorities": PRIORITIES,
        "statuses": STATUSES,
        "assignees": get_assignees(),
        "request_team_choices": get_request_team_choices(),
        "staff_logged_in": staff_logged_in(),
        "settings": load_settings(),
        "uuch": UUCH_CONTACT,
    }


@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    next_url = safe_next_url(request.args.get("next") or url_for("tickets"))
    if request.method == "POST":
        next_url = safe_next_url(request.form.get("next"))
        password = request.form.get("password", "")
        if password == app.config["STAFF_PASSWORD"]:
            session["staff_authenticated"] = True
            flash("Signed in to staff dashboard.", "success")
            return redirect(next_url)
        flash("Incorrect staff password.", "error")

    return render_template("login.html", next_url=next_url)


@app.route("/staff/logout", methods=["POST"])
def staff_logout():
    session.pop("staff_authenticated", None)
    flash("Signed out of staff dashboard.", "success")
    return redirect(url_for("request_ticket"))


@app.route("/", methods=["GET", "POST"])
@app.route("/request", methods=["GET", "POST"])
def request_ticket():
    errors = []
    form = request.form if request.method == "POST" else {}
    max_tickets = app.config["MAX_TICKETS"]
    ticket_count = count_tickets()
    ticket_limit_reached = ticket_count >= max_tickets
    categories = get_categories()
    if request.method == "POST":
        if ticket_limit_reached:
            errors.append(
                f"This demo has reached its {max_tickets}-ticket limit. "
                "Please use the staff dashboard to review existing requests."
            )
        else:
            required = ["requester_name", "contact", "category", "title", "description"]
            missing = [field for field in required if not request.form.get(field, "").strip()]
            if missing:
                errors.append("Please complete the required fields.")

        if not errors and not ticket_limit_reached:
            ticket = create_ticket(
                {
                    "requester_name": request.form["requester_name"],
                    "contact": request.form["contact"],
                    "category": choice_or_default(
                        request.form.get("category"),
                        categories,
                        OTHER_CATEGORY,
                    ),
                    "priority": choice_or_default(request.form.get("priority"), PRIORITIES, "Normal"),
                    "ministry": choice_or_default(
                        request.form.get("ministry", ""),
                        get_request_team_choices() + [""],
                        "",
                    ),
                    "location": request.form.get("location", ""),
                    "title": request.form["title"],
                    "description": request.form["description"],
                    "status": "New",
                    "assignee": "Unassigned",
                }
            )
            flash(f"Request {ticket['ticket_number']} submitted.", "success")
            return redirect(url_for("request_confirmation", ticket_id=ticket["id"]))

    return render_template(
        "request.html",
        errors=errors,
        form=form,
        ticket_count=ticket_count,
        max_tickets=max_tickets,
        ticket_limit_reached=ticket_limit_reached,
    )


@app.route("/request/confirmation/<int:ticket_id>")
def request_confirmation(ticket_id):
    ticket = get_ticket(ticket_id)
    if ticket is None:
        flash("Ticket not found.", "error")
        return redirect(url_for("request_ticket"))
    return render_template("confirmation.html", ticket=ticket)


@app.route("/tickets")
@staff_required
def tickets():
    filters = {
        "status": request.args.get("status", "All"),
        "assignee": request.args.get("assignee", "All"),
        "priority": request.args.get("priority", "All"),
        "q": request.args.get("q", ""),
    }
    sort_state = normalize_sort_state(
        request.args.get("sort"),
        request.args.get("direction"),
    )
    return render_template(
        "tickets.html",
        tickets=list_tickets(filters, sort_state),
        filters=filters,
        sort_columns=SORT_COLUMNS,
        sort_state=sort_state,
        stats=dashboard_stats(),
    )


@app.route("/notifications")
@staff_required
def notifications():
    return render_template(
        "notifications.html",
        notifications=list_notifications(),
    )


@app.route("/settings", methods=["GET", "POST"])
@staff_required
def settings_page():
    settings = load_settings()
    if request.method == "POST":
        settings = save_settings(
            {
                "church_name": request.form.get("church_name", "").strip()
                or DEFAULT_SETTINGS["church_name"],
                "staff_notification_email": request.form.get(
                    "staff_notification_email", ""
                ).strip()
                or DEFAULT_SETTINGS["staff_notification_email"],
                "requester_reply_email": request.form.get(
                    "requester_reply_email", ""
                ).strip()
                or DEFAULT_SETTINGS["requester_reply_email"],
                "notification_mode": request.form.get("notification_mode", "").strip()
                or DEFAULT_SETTINGS["notification_mode"],
                "public_contact_instructions": request.form.get(
                    "public_contact_instructions", ""
                ).strip()
                or DEFAULT_SETTINGS["public_contact_instructions"],
                "category_labels": request.form.get("category_labels", "").splitlines(),
                "team_labels": request.form.get("team_labels", "").splitlines(),
                "admin_users": request.form.get("admin_users", "").splitlines(),
            }
        )
        flash("Demo settings saved.", "success")
        return redirect(url_for("settings_page"))

    return render_template(
        "settings.html",
        settings=settings,
        category_labels="\n".join(settings["category_labels"]),
        team_labels="\n".join(settings["team_labels"]),
        admin_users="\n".join(settings["admin_users"]),
    )


@app.route("/tickets/<int:ticket_id>", methods=["GET", "POST"])
@staff_required
def ticket_detail(ticket_id):
    ticket = get_ticket(ticket_id)
    if ticket is None:
        flash("Ticket not found.", "error")
        return redirect(url_for("tickets"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_ticket":
            update_ticket(ticket)
        elif action == "add_comment":
            add_comment(ticket_id)
        return redirect(url_for("ticket_detail", ticket_id=ticket_id))

    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        comments=get_comments(ticket_id),
        activity=get_activity(ticket_id),
        created=request.args.get("created"),
    )


def update_ticket(ticket):
    db = get_db()
    new_status = choice_or_default(request.form.get("status"), STATUSES, ticket["status"])
    new_priority = choice_or_default(request.form.get("priority"), PRIORITIES, ticket["priority"])
    new_assignee = choice_or_default(request.form.get("assignee"), get_assignees(), ticket["assignee"])
    now = as_iso()

    changes = []
    for label, old, new in (
        ("Status", ticket["status"], new_status),
        ("Priority", ticket["priority"], new_priority),
        ("Assignee", ticket["assignee"], new_assignee),
    ):
        if old != new:
            changes.append(f"{label} changed from {old} to {new}")

    db.execute(
        """
        UPDATE tickets
        SET status = ?, priority = ?, assignee = ?, updated_at = ?
        WHERE id = ?
        """,
        (new_status, new_priority, new_assignee, now, ticket["id"]),
    )
    for event in changes:
        db.execute(
            "INSERT INTO activity (ticket_id, event, created_at) VALUES (?, ?, ?)",
            (ticket["id"], event, now),
        )
    queue_ticket_update_notifications(ticket, changes, now)
    db.commit()
    flash("Ticket updated.", "success")


def add_comment(ticket_id):
    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be blank.", "error")
        return

    author = request.form.get("author", "").strip() or "Staff"
    visibility = request.form.get("visibility", "Internal")
    visibility = "Public" if visibility == "Public" else "Internal"
    now = as_iso()
    ticket = get_ticket(ticket_id)

    db = get_db()
    db.execute(
        """
        INSERT INTO comments (ticket_id, author, body, visibility, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ticket_id, author, body, visibility, now),
    )
    db.execute(
        "INSERT INTO activity (ticket_id, event, created_at) VALUES (?, ?, ?)",
        (ticket_id, f"{visibility} comment added by {author}", now),
    )
    db.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket_id))
    if ticket is not None:
        queue_comment_notification(ticket, author, body, visibility, now)
    db.commit()
    flash("Comment added.", "success")


@app.route("/health")
@app.route("/healthz")
def healthz():
    return {"status": "ok"}


@app.cli.command("seed-demo")
def seed_demo_command():
    """Reset the local database and load demo tickets."""
    reset_database()
    click.echo("Demo database reset and seeded.")


with app.app_context():
    init_db()
    seed_demo_data()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug)
