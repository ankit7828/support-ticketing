# Submission

## Links

- **GitHub repository:** https://github.com/ankit7828/support-ticketing
- **Live application:** https://support-ticketing-7b7l.onrender.com/login

## Notes for the reviewer

The application is deployed on Render using the free web service.

The free Render instance can sleep after inactivity, so the first request may take some time to respond.

The application uses a PostgreSQL database hosted on Supabase.

Please use the demo credentials below to test the application. The main application starts from the `/login` page.

## Demo credentials

| Role | Email | Password |
|------|-------|----------|
| Supervisor | ankit@demo.com | Ankit@7828 |
| Agent | riya@demo.com | riya@123 |
| Agent | shivam@demo.com | shivam@123 |
| Agent | raghav@demo.com | raghav@123 |

## Stack

| Layer | What you used | Why |
|-------|---------------|-----|
| Frontend | HTML, CSS, Bootstrap, JavaScript, Chart.js | Used to build the ticketing interface, dashboard, forms and charts |
| Backend | Python, Flask, Flask-Login, Flask-SQLAlchemy, Flask-Migrate | Used for the application logic, authentication, permissions, tickets and database operations |
| Database | PostgreSQL with Supabase | Used to store users, tickets, replies, collaborators, history and SLA alerts |
| Hosting | Render | Used to deploy the Flask application and make it publicly accessible |

## Goal checklist

| # | Goal | Status | Notes |
|---|------|--------|-------|
| 1 | User authentication and roles | Done | Login/logout is implemented with supervisor and agent roles. |
| 2 | Ticket creation and management | Done | Users can create, edit and view support tickets. |
| 3 | Ticket assignment | Done | Tickets can be assigned and reassigned to agents. |
| 4 | Ticket status lifecycle | Done | Tickets support New, Open, Pending, Resolved and Closed states. |
| 5 | Replies and internal notes | Done | Users can add replies and internal notes to tickets. |
| 6 | Ticket collaborators | Done | Multiple agents can collaborate on the same ticket. |
| 7 | Search, filtering and ticket actions | Done | Tickets can be searched, filtered and sorted. |
| 8 | Bulk actions and CSV export | Done | Multiple tickets can be reassigned/closed and ticket data can be exported as CSV. |
| 9 | Ticket history and dashboard | Done | Ticket changes are recorded and the dashboard provides ticket statistics and charts. |
| 10 | SLA alerts | Done | SLA warning/breach alerts are displayed and can be acknowledged by authorized users. |

## How much time did you actually spend?

Approximately **12 - 15** hours.

The time included the initial project setup, database design, authentication, ticket features, dashboard, SLA functionality, UI improvements, testing, debugging, demo data and deployment.

## What would you do next, with another 12 hours?

With another 12 hours, I would mainly improve the production quality of the application.

I would add automated tests for more of the important ticket and permission flows, improve the dashboard queries and database indexes, and make the UI more responsive on smaller screens.

I would also improve the deployment setup and add better error handling and logging for production use.

## What are you least happy with in this codebase, and why?

I am least happy with some parts of the code that became more complicated while I was adding features such as SLA alerts, bulk actions and ticket history.

Some of these features required changes in multiple files, which made debugging more difficult than I expected.

I would like to refactor some of these areas into cleaner service functions and add more automated tests so that future changes are easier to make without introducing new errors.
