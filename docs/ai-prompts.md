# AI Prompts

I used AI during the development of this project to help with coding, debugging, database changes, UI improvements and understanding errors. I did not use the generated code blindly. I tested the changes and corrected the code when it did not match my actual project.

## Project setup

### Prompt

"Give me code which creates this folder structure for a Flask support ticketing system."

### What I got

I got the basic Flask project structure with folders for the application, models, routes, templates and configuration.

### What I corrected

I created the structure in my project and then changed some files as the project requirements became clearer.

## Ticket management

### Prompt

"Give updated `app/routes/tickets.py`."

### What I got

I got Flask routes for creating, viewing, editing and managing tickets, including role and assignment checks.

### What I corrected

I tested the routes and fixed errors when some field names or route names did not match my actual project.

## SLA response tracking

### Prompt

"Give updated migration code for adding SLA response tracking."

### What I got

The generated migration tried to add required fields such as `response_target_minutes` directly as `NOT NULL`.

### What I corrected

When I ran the migration, PostgreSQL gave a `NotNullViolation` because existing tickets had no value for the new column. I changed the migration so existing records could receive appropriate values before the fields were made required.

## Demo data

### Prompt

"Give me code that would add 50 data to show in dashboard."

### What I got

I got a seed script that created demo users, tickets and related data for the dashboard.

### What I corrected

Some generated seed code used field names that did not exist in my actual models. For example, it first used `old_status` for `TicketStatusHistory`, but my model uses `from_status` and `to_status`. It also tried to use `created_at` where that field was not available in that model.

I checked my actual models and changed the seed code to use the correct field names.

## Bulk ticket actions

### Prompt

"Give full updated code for the bulk result page."

### What I got

I got a template showing successful and refused tickets after a bulk reassign or bulk close operation.

### What I corrected

The first template assumed `result.ticket` was a Ticket object and used `result.ticket.id`. My application was actually returning the ticket ID as an integer. This caused the error:

`'int object' has no attribute 'id'`

I changed the template to use the ticket ID directly.

## SLA alerts

### Prompt

"Give updated code for the SLA alert route so that acknowledging an alert does not resolve the ticket."

### What I got

I got an updated alert route that sets the alert as acknowledged and stores the acknowledgement time and user.

### What I corrected

I compared it with my existing `alerts.py` and kept the parts that already matched my project. I made sure that acknowledging an alert only removes it from the active alert list and does not change the ticket status.

## UI improvements

### Prompt

"Update the dashboard code and make the UI better, especially the chart."

### What I got

I got an improved dashboard layout with summary cards, status breakdown, agent breakdown, recent tickets and an eight-week resolved-ticket chart.

### What I corrected

I kept the parts that worked with my existing dashboard variables and adjusted the UI so that it matched the rest of my application instead of replacing the whole design.
