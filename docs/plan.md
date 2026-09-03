# Plan

## How did you break the work into sessions?

I divided the project into small parts instead of trying to build everything at once. First, I set up the Flask project and database. Then I worked on login and user roles. After that, I built the ticket creation, ticket list, editing, and ticket details.

Next, I added the ticket lifecycle, replies, collaborators, search and filters. After that, I worked on bulk actions, CSV export, dashboard, ticket history, and SLA alerts.

Finally, I worked on the UI, added demo data, fixed errors, and prepared the project for deployment.  

## What order did you build in, and why that order?

I started with the basic project setup because all the other features depend on it. I created the database models and authentication first so that I could control users and permissions.

Then I built tickets because it is the main part of the application. After tickets were working, I added replies, status changes, collaborators, search, and bulk actions.

I built the dashboard and SLA features later because they depend on ticket data and ticket status. I left testing, demo data, UI improvements, and deployment for the final stage.

## What did you estimate versus what it actually took?

At first, I thought the basic ticketing system would be fairly quick to complete. I underestimated the time needed for permissions, database migrations, SLA tracking, history, and fixing errors.

The project took more time than I expected because some changes affected multiple parts of the application. I also had to fix several errors while adding new features, especially with database migrations, seed data, and SLA alerts.

The UI and final testing also took longer than I originally planned.

## What did you cut when you ran short?

I decided not to add email notifications because they were not necessary for the main 10 requirements and would take additional time to configure and test.

I focused instead on completing the main ticketing features, server-side permissions, bulk actions, dashboard, history, collaborators, and SLA alerts.

I also kept some UI features simple rather than spending too much time on extra visual effects that were not part of the main requirements.
