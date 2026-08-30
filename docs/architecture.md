# Architecture

## What are the moving pieces, and how do they talk to each other?

The application is built using Flask as the main backend framework. The main parts are Flask routes, SQLAlchemy models, HTML templates, authentication, and the PostgreSQL database.

The routes handle requests from the user and contain the application logic. The models represent the database tables and are used by the routes to read and update data. The templates are used to display the data in the browser.

Flask-Login handles user login and authentication. Flask-Migrate is used to manage database schema changes.

The main flow is:

Browser → Flask routes → SQLAlchemy models → PostgreSQL database

The result then goes back in the opposite direction:

PostgreSQL → SQLAlchemy → Flask → HTML template → Browser


## Where does each piece run?

The browser runs on the user's computer and displays the SupportDesk interface.

The Flask application runs on the server. It handles authentication, permissions, tickets, replies, collaborators, dashboard data, history and SLA alerts.

The PostgreSQL database is hosted on Supabase. It stores users, tickets, replies, collaborators, history and SLA alert data.

Flask-Migrate and Alembic are used with the Flask application to manage changes to the database structure.


## What is the request path for one representative user action, end to end?

For example, when an agent acknowledges an SLA alert:

1. The agent opens the Alerts page in the browser.
2. The browser sends a request to the Flask alert route when the agent clicks **Acknowledge**.
3. Flask checks that the user is logged in.
4. The application checks whether the agent is allowed to acknowledge that alert.
5. The SLA alert record is updated by setting it as acknowledged and storing who acknowledged it and when.
6. SQLAlchemy sends the update to the PostgreSQL database.
7. The database saves the changes.
8. Flask redirects the user back to the Alerts page.
9. The page is loaded again and the acknowledged alert is no longer shown in the active alerts list.


## What did you decide not to build, and why?

I decided not to build email notifications because they were not required for the main 10 goals and would require extra configuration and testing.

I also did not build a separate customer-facing portal. The project focuses on the support team and the required agent and supervisor functionality.

I kept the application as a web-based Flask application instead of building separate mobile or desktop applications because that was outside the main requirements.
