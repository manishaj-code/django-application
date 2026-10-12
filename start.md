# Project: Production-Ready Django Web Application

Act as a senior full-stack Python engineer, Django architect, PostgreSQL database engineer, UI/UX designer, QA engineer, and DevOps engineer.

Your task is to design and implement a complete, maintainable, secure web application from scratch. The application must support user registration and authentication, administrative content management, a responsive frontend, PostgreSQL integration, automated testing, production deployment, and administrator handover documentation.

Do not just provide code snippets or a tutorial. Create the actual project files in the current working directory, run available checks, fix errors, and guide me through each phase until the application is ready for deployment.

## 1. Technology Stack

Use the following technologies:

- Python 3.12 or another compatible, supported Python version.
- Django 5.2 LTS or a newer compatible supported release.
- PostgreSQL.
- Django ORM and migrations.
- HTML5, CSS3, JavaScript, and Bootstrap 5.
- Django built-in authentication.
- Django Admin for administrative content management.
- pytest and pytest-django, or Django's built-in test framework.
- Git for version control.
- Gunicorn for production serving where appropriate.
- WhiteNoise or an equivalent appropriate approach for static files.
- Docker and Docker Compose as an optional reproducible deployment environment.
- Environment variables for secrets and configuration.

Avoid React, Node.js frontend frameworks, and unnecessary microservices. Prefer a simple Django monolith that is easy to maintain.

Before installing dependencies, verify compatible versions and select stable releases.

## 2. Functional Requirements

### A. Public Website

Create a clean, modern, responsive website with:

- Home page.
- Content listing page.
- Content detail page.
- About page.
- Contact page with server-side validation.
- Navigation bar and footer.
- Custom 403, 404, and 500 error pages.
- Responsive layouts for desktop, tablet, and mobile.
- Appropriate empty states, success messages, and error messages.

The application must be generic enough to adapt to different content-management use cases. Do not invent complex business features that the client has not requested.

### B. User Registration and Authentication

Implement:

- User registration.
- Login and logout.
- Password hashing through Django's authentication framework.
- Password reset using Django's supported mechanisms.
- User profile page.
- Secure session handling.
- Form validation and helpful error messages.
- Login-required access to protected pages.
- Appropriate permissions for regular users and administrators.
- CSRF protection.
- Rate limiting or throttling for sensitive authentication endpoints where practical.

Never store plain-text passwords.

Do not allow users to assign themselves administrative privileges during registration.

Configure email-based password reset through environment variables. Provide a safe local development method for viewing reset emails without requiring a live email service.

### C. Administrative Content Management

Use Django Admin as the initial administrative CMS. Configure it to provide a usable, professional management experience.

Administrators must be able to:

- Create content.
- View content.
- Edit content.
- Delete content.
- Publish and unpublish content.
- Manage categories.
- Search and filter records.
- Manage publication dates and timestamps.
- Upload optional content images if appropriate.
- Manage user accounts and permissions.

Create appropriate Django models for Content and Category.

Suggested Content fields:

- id
- title
- slug
- summary
- body
- category
- featured_image
- status
- created_at
- updated_at
- published_at
- created_by

Use appropriate database constraints, indexes, relationships, slug generation, and validation.

Ensure the admin interface includes useful list displays, filters, search fields, and read-only timestamps where appropriate.

Only authorized staff users may access Django Admin.

### D. PostgreSQL Integration

Configure PostgreSQL through environment variables:

- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT

Provide a .env.example file containing placeholder values only.

Never commit real credentials or secret keys.

Create and test database migrations. Verify model relationships, constraints, and CRUD operations.

Provide clear instructions for creating the database and database user.

SQLite may be used for isolated tests if necessary, but PostgreSQL must be the documented production database.

### E. Frontend and User Experience

Create a clean, modern interface using Bootstrap 5 and Django templates.

Include:

- Consistent spacing and typography.
- Responsive navigation.
- Accessible form labels.
- Visible validation errors.
- Confirmation messages for important actions.
- Loading and empty states where relevant.
- Accessible color contrast.
- Responsive content cards and detail pages.
- Pagination for content listings.

Keep templates reusable with a shared base template and appropriate template partials.

Avoid unnecessary animations and frontend dependencies.

## 3. Security Requirements

Apply Django security best practices:

- Use Django's built-in password hashing and authentication.
- Protect POST requests against CSRF.
- Validate and sanitize user-provided data appropriately.
- Use ORM queries rather than unsafe SQL string concatenation.
- Restrict administrative actions to authorized users.
- Configure secure cookies and HTTPS settings for production.
- Keep DEBUG disabled in production.
- Configure ALLOWED_HOSTS explicitly.
- Keep secrets outside source code.
- Protect uploaded files and validate permitted file types and sizes.
- Avoid exposing stack traces, passwords, tokens, or secrets in logs.
- Apply least-privilege database access.
- Configure security headers and HTTPS redirects appropriately for the chosen host.
- Follow Django's deployment security checklist.

Do not claim the application is completely secure without appropriate testing and review.

## 4. Project Architecture

Use a clear, maintainable structure similar to:

django_cms/
    manage.py
    config/
        __init__.py
        settings.py
        urls.py
        wsgi.py
        asgi.py
    accounts/
        models.py
        forms.py
        views.py
        urls.py
        tests.py
    content/
        models.py
        forms.py
        views.py
        urls.py
        admin.py
        tests.py
    templates/
        base.html
        home.html
        registration/
        accounts/
        content/
        errors/
    static/
        css/
        js/
        images/
    media/
    tests/
    requirements.txt
    .env.example
    .gitignore
    README.md
    Dockerfile
    compose.yaml

Adapt the structure when justified, but keep the architecture simple. Avoid duplicate implementations of authentication or CMS functionality already provided by Django.

## 5. Automated Testing

Write tests covering:

- Registration with valid and invalid input.
- Login and logout.
- Password reset behavior.
- Anonymous access to protected pages.
- Authorization for administrative pages.
- Content creation, editing, deletion, and publication.
- Category relationships.
- Slug uniqueness.
- Form validation.
- Public listing and detail pages.
- Pagination.
- Database constraints.
- Invalid or missing records.
- Security-sensitive access control.

Run the tests and fix failures before declaring a phase complete.

Use Django's test client or pytest-django as appropriate.

Do not remove failing tests simply to make the test suite pass.

## 6. Deployment

Prepare the application for deployment to a suitable hosting provider selected by the client.

Support a deployment approach appropriate to the host, such as a managed Python application platform, a managed container platform, or a VPS.

Provide:

- Production settings.
- PostgreSQL connection configuration.
- Gunicorn configuration where appropriate.
- Static file collection.
- Media storage guidance.
- Environment variable setup.
- Database migration instructions.
- HTTPS and domain configuration instructions.
- Production logging.
- Backup and restore guidance.
- Health-check endpoint if appropriate.
- A deployment checklist.

Use the selected hosting provider's supported SSL mechanism. Never hardcode production credentials.

Do not claim the application is deployed or live unless deployment has actually succeeded and has been verified.

Do not purchase hosting, register domains, or incur paid service charges without my explicit approval.

## 7. Documentation and Handover

Create a complete README.md covering:

- Project overview.
- Technology stack.
- Prerequisites.
- Local installation.
- Virtual environment setup.
- Dependency installation.
- PostgreSQL database setup.
- Environment variable configuration.
- Database migrations.
- Creating a superuser.
- Running the development server.
- Running tests.
- Creating and managing content.
- Collecting static files.
- Deployment.
- Backup and restore.
- Common errors and troubleshooting.

Create ADMIN_GUIDE.md explaining how the administrator can:

- Sign in to the admin panel.
- Create and edit content.
- Manage categories.
- Publish and unpublish content.
- Manage users and permissions.
- Reset passwords.
- Troubleshoot common administrative problems.

Provide a concise deployment and handover checklist.

## 8. Development Workflow

Follow these phases in order.

Phase 1: Inspect the current directory and environment. Create the project foundation, virtual environment, dependencies, Django configuration, PostgreSQL settings, environment example, and Git ignore rules.

Phase 2: Implement the database models, migrations, Django Admin, and content-management functionality.

Phase 3: Implement registration, login, logout, password reset, profiles, and authorization.

Phase 4: Build the responsive frontend and connect all templates to the backend.

Phase 5: Add automated tests, run migrations, execute system checks, run tests, and fix errors.

Phase 6: Prepare production settings, deployment files, health checks where appropriate, and hosting instructions.

Phase 7: Complete the README, administrator guide, verification checklist, and handover notes.

At the beginning of each phase:

1. Explain the objective briefly.
2. List the files that will be created or modified.
3. Identify any decisions requiring my approval.

Then implement the phase.

After implementation:

1. Run the relevant commands and tests.
2. Inspect the results.
3. Fix problems before proceeding.
4. Summarize files changed and functionality completed.
5. Tell me exactly what I need to do next.

## 9. Working Rules

- Work directly in the current project directory.
- Inspect existing files before modifying them.
- Do not overwrite existing work without approval.
- Prefer complete, maintainable implementations over unnecessary abstractions.
- Do not leave essential functionality as TODO comments or placeholder implementations.
- Do not fabricate test results.
- Never expose secrets in generated files or terminal output.
- Ask before performing destructive operations or incurring costs.
- Do not proceed with external deployment until the hosting provider and credentials are configured by me.
- Explain errors in simple language and provide exact commands to resolve them.
- Keep all changes aligned with the stated scope.
- If a requirement is ambiguous, choose a sensible minimal implementation and explain the assumption.

## 10. Initial Action

Start with Phase 1 only.

Inspect the current working directory, identify the installed Python and PostgreSQL tools, and determine whether the required environment is ready.

If PostgreSQL is not installed or running, explain the available setup options before making system-level changes.

Then create the Django project foundation, install compatible dependencies, configure environment-based settings, and verify that the application starts.

Do not attempt all phases in one unreviewed operation. Finish Phase 1, run the checks, report the results, and wait for my confirmation before proceeding to Phase 2.

Begin now.