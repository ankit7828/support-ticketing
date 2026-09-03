# Schema

## Table by table: what columns and types does each one have?

The database has seven main tables.

### 1. `users`

This table stores all users of the application.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `name` | String(100) | User name |
| `email` | String(255) | User email |
| `password_hash` | String(255) | Hashed password |
| `role` | String(20) | Agent or supervisor |
| `created_at` | DateTime | Account creation time |

The email is unique and indexed. The password is stored as a hash instead of plain text. :contentReference[oaicite:0]{index=0}

### 2. `tickets`

This is the main table of the application. It stores the ticket information, assignment, status and SLA information.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `subject` | String(255) | Ticket subject |
| `description` | Text | Ticket description |
| `requester_name` | String(100) | Customer name |
| `requester_email` | String(255) | Customer email |
| `priority` | String(20) | Low, medium, high or urgent |
| `category` | String(50) | Ticket category |
| `status` | String(20) | New, open, pending, resolved or closed |
| `primary_assignee_id` | Integer | Main assigned agent |
| `created_by_id` | Integer | User who created the ticket |
| `created_at` | DateTime | Creation time |
| `updated_at` | DateTime | Last update time |
| `closed_at` | DateTime | Closing time |
| `archived_at` | DateTime | Archive time |
| `response_started_at` | DateTime | Start of SLA response clock |
| `response_target_minutes` | Integer | SLA target in minutes |
| `response_paused_at` | DateTime | Time when SLA was paused |
| `response_paused_seconds` | Integer | Total paused time |
| `response_breached` | Boolean | Whether the SLA has been breached |

The ticket table has foreign keys to the users table for the primary assignee and the user who created the ticket. :contentReference[oaicite:1]{index=1}

### 3. `replies`  

This table stores all replies and internal notes made inside tickets.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `ticket_id` | Integer | Ticket to which the reply belongs |
| `author_id` | Integer | User who wrote the reply |
| `body` | Text | Reply message |
| `is_internal` | Boolean | Whether it is an internal note |
| `created_at` | DateTime | Reply time |

Each reply belongs to one ticket and one user. :contentReference[oaicite:2]{index=2}

### 4. `ticket_collaborators`

This table connects tickets and agents. It is used when more than one agent works on the same ticket.

| Column | Type | Purpose |
|---|---|---|
| `ticket_id` | Integer | Ticket |
| `user_id` | Integer | Collaborating agent |
| `added_at` | DateTime | Time the collaborator was added |

The combination of `ticket_id` and `user_id` is the primary key, so the same agent cannot be added twice to the same ticket. Both columns are also foreign keys. :contentReference[oaicite:3]{index=3}

### 5. `ticket_history`

This table stores the main timeline of changes made to a ticket.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `ticket_id` | Integer | Related ticket |
| `actor_id` | Integer | User who made the change |
| `event_type` | String(50) | Type of event |
| `old_value` | Text | Previous value |
| `new_value` | Text | New value |
| `created_at` | DateTime | Time of the event |

This allows the application to keep a history of actions such as ticket creation, status changes, replies and other changes. :contentReference[oaicite:4]{index=4}

### 6. `ticket_status_history`

This table specifically stores ticket status changes.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `ticket_id` | Integer | Related ticket |
| `from_status` | String(20) | Previous status |
| `to_status` | String(20) | New status |
| `changed_by_id` | Integer | User who changed the status |
| `changed_at` | DateTime | Time of the change |

For example, a change from `open` to `pending` is stored with `from_status = open` and `to_status = pending`. :contentReference[oaicite:5]{index=5}

### 7. `sla_alerts`

This table stores SLA warning and breach alerts.

| Column | Type | Purpose |
|---|---|---|
| `id` | Integer | Primary key |
| `ticket_id` | Integer | Related ticket |
| `alert_type` | String(20) | Warning or breach |
| `acknowledged` | Boolean | Whether the alert was acknowledged |
| `acknowledged_by_id` | Integer | User who acknowledged it |
| `acknowledged_at` | DateTime | Time of acknowledgement |
| `created_at` | DateTime | Alert creation time |

The alert is connected to both the ticket and the user who acknowledged it. :contentReference[oaicite:6]{index=6}


## Which relationships are one-to-many, and which are many-to-many?

Most relationships in the database are one-to-many.

### One-to-Many Relationships

1. **User → Tickets**
   - One user can create many tickets.
   - One user can be the primary assignee of many tickets.

2. **User → Replies**
   - One user can write many replies.

3. **Ticket → Replies**
   - One ticket can have many replies.

4. **User → Ticket History**
   - One user can make many history entries.

5. **Ticket → Ticket History**
   - One ticket can have many history entries.

6. **User → Ticket Status History**
   - One user can make many status changes.

7. **Ticket → Ticket Status History**
   - One ticket can have many status history entries.

8. **Ticket → SLA Alerts**
   - One ticket can have multiple SLA alerts.

9. **User → SLA Alerts**
   - One user can acknowledge multiple SLA alerts.

### Many-to-Many Relationship

**Tickets ↔ Users (Agents) through `ticket_collaborators`**

- One ticket can have many collaborating agents.
- One agent can collaborate on many tickets.
- The `ticket_collaborators` table connects the two.

## Which constraints are enforced by the database, and which by application code — and why did you draw the line there?

I used database constraints for basic data integrity and application code for rules that depend on the user's role or the current ticket status.

### Database constraints

- Every table has a **primary key**.
- Related records use **foreign keys**, for example tickets are connected to users.
- Required fields use `nullable=False`.
- User email is **unique**, so two users cannot have the same email.
- `ticket_collaborators` uses `ticket_id` and `user_id` together as a **composite primary key**, so the same agent cannot be added to the same ticket twice.
- Replies, collaborators and SLA alerts have foreign keys to their tickets, with cascade delete where defined.

These are handled by the database because they are basic rules that should always be true for the stored data.

### Application-level constraints

The application handles the rules that depend on the current user and ticket state, such as:

- Supervisors and agents have different permissions.
- Agents can only work on tickets they are assigned to or collaborate on.
- Agents cannot reassign a ticket away from themselves.
- Ticket status changes follow the required lifecycle.
- SLA response time and pending/paused behaviour are handled by the application.
- SLA alerts can be acknowledged only by the appropriate user.

I kept these rules in the application because the database only knows about the stored data, while the Flask application can check **who is performing the action and what is happening to the ticket** before allowing it.

## What did you deliberately denormalise?

I did not deliberately denormalise the database much. I kept the main information separated into different tables such as users, tickets, replies, collaborators, history and SLA alerts.

The main deliberate choice was keeping some SLA information directly in the `tickets` table, such as `response_target_minutes`, `response_paused_seconds` and `response_breached`. These values could be calculated when needed, but storing them makes it easier to check the current SLA state and display it quickly.

Apart from this, I mainly kept the database normalized to avoid unnecessary duplicate data.

## What would break first if this had 100x the data?

The first problem would most likely be **performance**, especially in the ticket list and dashboard.

With 100x more tickets, replies and history records, database queries for searching, filtering, sorting and dashboard statistics would take longer. The history and replies tables would also become much larger.

The application already uses server-side filtering and pagination, which helps. If the data became much larger, I would first optimize the database queries and add or improve indexes for the fields used frequently in searching, filtering and sorting.

I would also optimize the dashboard queries and consider archiving older history data if the database became very large.
