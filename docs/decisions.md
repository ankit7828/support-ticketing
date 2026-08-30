# Decisions

## Decision 1

- **Chose:** Flask with SQLAlchemy and PostgreSQL.
- **Rejected:** Using a different backend framework or keeping the application with a simple local database.
- **Why:** Flask was simple enough for me to build the application step by step, while SQLAlchemy made it easier to work with the different tables and relationships. PostgreSQL was suitable for the relational data and the existing Supabase setup.

## Decision 2

- **Chose:** Keep agents and supervisors in the same `users` table and use a `role` field.
- **Rejected:** Creating separate tables for agents and supervisors.
- **Why:** Both are users of the same application and share most of the same information. Using a role keeps the database simpler while the application can control what each role is allowed to do.

## Decision 3

- **Chose:** Use a separate `ticket_collaborators` table for collaborators.
- **Rejected:** Storing multiple collaborator IDs directly inside the `tickets` table.
- **Why:** A ticket can have multiple collaborators and an agent can collaborate on multiple tickets. A separate table makes this many-to-many relationship easier to manage.

## Decision 4

- **Chose:** Keep ticket history, status history, replies and SLA alerts in separate tables.
- **Rejected:** Storing all of these details directly inside the `tickets` table.
- **Why:** These records can occur many times for one ticket. Keeping them separate makes the data easier to manage and allows the ticket timeline and SLA information to be stored properly.

## Decision 5

- **Chose:** Use server-side search, filtering, sorting and pagination for the ticket queue.
- **Rejected:** Loading all tickets into the browser and filtering them using JavaScript.
- **Why:** The requirement specifically asks for these operations to happen on the server. It also means the browser does not need to load every ticket when the database becomes larger.

- **Later reversed:** Initially, I kept some ticket-list and UI logic simpler and relied more on the existing page behaviour. While testing with different users and tickets, I found that the filtering and permission behaviour needed to be handled more carefully on the server. I changed the approach so that the important access and queue rules are checked in the backend rather than depending on what is shown in the interface.
