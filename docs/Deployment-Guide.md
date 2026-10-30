# Blood Bank Management System — Deployment Guide

## 1. Purpose

This guide describes how to configure and prepare the Blood Bank Management System (BBMS) for deployment.

The project uses Django 5.2. SQLite is configured for development and automated tests, while PostgreSQL 15 is intended for production.

## 2. Prerequisites

The deployment environment should provide:

- Python compatible with Django 5.2.
- pip and a Python virtual environment.
- PostgreSQL 15 for production.
- Nginx as the HTTPS reverse proxy.
- An SMTP server supporting STARTTLS for production email.
- A production WSGI server.

**Dependency note:** The current `requirements.txt` lists Django and `python-barcode`. A PostgreSQL database driver and production WSGI server are not listed. They must be selected, added and tested before production deployment. Do not use Django's development server as the production server.

## 3. Obtain and install the application

1. Clone the project repository.
2. Change to the project directory.
3. Create and activate a virtual environment.
4. Install the project's Python dependencies.

Example:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run Django management commands from the directory containing `manage.py`.

## 4. Environment configuration

The application reads configuration from environment variables. Copy `.env.example` as a starting point and configure the values in the deployment environment.

Important variables:

| Variable | Purpose |
|---|---|
| `BBMS_ENV` | Set to `production` for production deployment |
| `DJANGO_DEBUG` | Set to `false` |
| `DJANGO_SECRET_KEY` | Required secret key for production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of permitted host names |
| `DB_ENGINE` | Set to `postgres` to use PostgreSQL |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL application user |
| `DB_PASSWORD` | PostgreSQL application user's password |
| `DB_HOST` | PostgreSQL server host |
| `DB_PORT` | PostgreSQL server port |

Never commit a real `.env` file, production password or secret key to the repository.

The production secret key must be supplied through a secure environment configuration. The application refuses to start in production if `DJANGO_SECRET_KEY` is missing.

## 5. Database configuration

### Development and testing

The application uses SQLite by default.

### Production

The intended production database is PostgreSQL 15.

1. Install and configure PostgreSQL 15.
2. Create the production database.
3. Create a dedicated database role for the application.
4. Configure the database environment variables.
5. Install and verify the required PostgreSQL Python driver.
6. Apply the Django migrations.

Run:

```bash
python manage.py migrate
```

The production application must connect using its dedicated runtime database role, not a PostgreSQL superuser.

### Protecting audit records

The audit model is `AuditEntry`, and its default Django database table is `audit_auditentry`.

The application prevents audit entries from being edited or deleted through its model and queryset methods. However, these application-level protections do not prevent a database administrator from changing records directly.

For production:

- Use a separate database owner or migration role.
- Use a restricted runtime role for normal application operation.
- Grant the runtime role only the permissions it requires.
- Do not grant the runtime role `UPDATE` or `DELETE` permission on `audit_auditentry`.
- Test that normal audit entry creation and reading still work with the restricted role.
- Perform schema migrations using the authorized migration role.

Database permissions must be verified after deployment.

## 6. Static files

The project defines:

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Collect static files before deployment:

```bash
python manage.py collectstatic
```

Configure the production web server to serve the collected static files from the configured static directory.

## 7. HTTPS and Nginx

In production, the application enables secure deployment settings by default when `BBMS_ENV=production`.

These include:

- Secure session cookies.
- Secure CSRF cookies.
- HTTPS redirection.
- HTTP Strict Transport Security (HSTS).
- `HttpOnly` session cookies.
- `SameSite=Lax` cookie settings.

The project expects Nginx to terminate TLS and forward the HTTPS protocol information to Django.

The Nginx and Django proxy configuration must be tested together. In particular, the application currently obtains the audit source IP using:

```python
request.META.get("REMOTE_ADDR") or None
```

When Nginx is the reverse proxy, this may record the proxy address rather than the original client's address.

**Deployment limitation:** The current application does not demonstrate trusted client-IP extraction from a forwarded header. Do not blindly trust client-supplied forwarding headers. A trusted-proxy solution requires an appropriately configured proxy and application-side handling, followed by verification using a real request.

## 8. Email configuration

In production, the application uses Django's SMTP email backend with STARTTLS.

Configure these environment variables:

| Variable | Purpose |
|---|---|
| `DEFAULT_FROM_EMAIL` | Sender email address |
| `EMAIL_HOST` | SMTP server host |
| `EMAIL_PORT` | SMTP server port; defaults to `587` |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |

The SMTP password must be stored securely and must not be committed to source control.

The development environment uses the console email backend. Production email delivery must be tested using the actual SMTP service.

## 9. Daily expiry job

The application provides the Django management command:

```bash
python manage.py expire_units
```

This command:

1. Marks units past their expiry date as `Expired`.
2. Sends the near-expiry digest when required.

The command is intended to run daily. Configure a cron job or systemd timer to execute it once every 24 hours.

Example cron template (replace the paths with the actual deployment paths):

```cron
0 1 * * * /path/to/venv/bin/python /path/to/project/manage.py expire_units
```

The command also supports:

```bash
python manage.py expire_units --no-digest
```

This runs the expiry operation without sending the digest email.

Verify the scheduled job's logs and confirm that the SMTP configuration works. Until the job runs, the application may still ignore expired units during stock and allocation checks, but their stored status may not yet be updated.

## 10. Authentication and security settings

The production configuration includes:

- Password validation, including a minimum length of 10 characters and complexity validation.
- Account lockout after five consecutive failed login attempts for 15 minutes.
- Session expiry after 30 minutes of inactivity.
- Secure cookies and HTTPS settings in production.
- Authentication middleware requiring sign-in for protected views.

Create the initial administrator account through the Django management command:

```bash
python manage.py createsuperuser
```

Use a strong, unique password and protect administrator credentials.

## 11. Deployment verification

Before making the application available:

1. Confirm that production environment variables are set.
2. Confirm that `DJANGO_DEBUG=false`.
3. Confirm that the production secret key is configured.
4. Confirm that the application connects to PostgreSQL using the intended runtime role.
5. Apply migrations successfully.
6. Run:

   ```bash
   python manage.py check --deploy
   ```

7. Collect static files.
8. Verify that the production WSGI server starts successfully.
9. Verify HTTPS redirection and secure cookies.
10. Test login, logout and role-based access.
11. Test audit event creation and confirm that the runtime role cannot update or delete audit records.
12. Test the expiry command and confirm the daily schedule is active.
13. Test SMTP email delivery and the near-expiry digest.
14. Verify audit source IP behaviour through the Nginx proxy.
15. Review application and scheduled-job logs.

Record the actual test results. Do not mark a deployment check as passed until it has been performed.

## 12. Known deployment limitations and deviations

| Deviation | Description | Deployment action |
|---|---|---|
| D-34 | Audit source IP currently uses `REMOTE_ADDR`, which may identify the Nginx proxy instead of the client. | Configure and test trusted proxy handling and application-side client-IP extraction. |
| D-35 | Application code prevents editing and deleting audit records, but a database administrator can still modify them directly. | Restrict runtime database permissions on `audit_auditentry`. |
| D-41 | Expired units are marked by a management command that must run daily. | Configure and verify a daily cron job or systemd timer. |

## 13. Production readiness notes

The following items still require confirmation before production deployment:

- Add and test a PostgreSQL Python driver.
- Select, add and test a production WSGI server.
- Verify the final Nginx configuration and trusted-proxy handling.
- Verify PostgreSQL audit-table permissions.
- Configure and test SMTP credentials.
- Configure and verify the daily expiry schedule.
- Execute the deployment verification checklist and record actual results.

**End of Deployment Guide**
