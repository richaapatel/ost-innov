# SkillSwap Stage 3

This repository contains the foundational setup for SkillSwap, the Stage 2 data layer, and the Stage 3 authentication experience. It provides a Django backend configured with a custom email-based User model, MySQL in Docker, skills and exchange data integrity, and session-based authentication. Later discovery, matching, exchange UI, dashboard, and analytics functionality are not implemented yet.

## Stage 3 authentication

Authentication uses Django's built-in session system. Users register and log in with their email address, and passwords are hashed with Django's password hashing utilities.

- Registration: `/accounts/register/`
- Login: `/accounts/login/`
- Logout: POST `/accounts/logout/`
- Protected-route example: `/protected/`

Registration requires a full name, a unique email address, and a password from 8–128 characters containing uppercase, lowercase, a number, and a special character. Invalid credentials use a generic error message, inactive users cannot authenticate, and safe `next` redirects are preserved after login. Logout is CSRF-protected and session-based; authentication is not stored in browser storage or application-managed tokens.

## Stage 2 data layer

- `Skill` stores normalized, case-insensitively unique skill names, descriptions, categories, and timestamps.
- Users have `offered_skills` and `wanted_skills` many-to-many relationships with `Skill`.
- `Exchange` records teacher, learner, skill, message, status, and timestamps. Valid statuses are `pending`, `accepted`, `rejected`, and `completed`.
- Exchange services enforce teacher offerings, participant permissions, duplicate pending-request prevention, and the allowed status transitions.

## Demo data

Run the idempotent seed command:

```bash
python manage.py seed_demo_data
# or
make seed
```

It creates six demo users, ten skills, and four valid exchanges covering every exchange status. Re-running it does not duplicate those records and does not delete existing data.

Development-only demo credentials:

- Users: `alice@example.com`, `bob@example.com`, `carlos@example.com`, `diana@example.com`, `elena@example.com`, `frank@example.com`
- Password: `SkillSwapDemoOnly123!`

These credentials are for local development only. Change or remove them before using any non-development environment.

## Prerequisites
- Python 3.12+
- Docker Desktop
- Docker Compose

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

2. **Configure environment variables:**
   Copy the example environment file and adjust if necessary.
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies and setup database:**
   Run the setup command which installs Python packages, starts MySQL via Docker, runs database migrations, and performs system checks.
   ```bash
   make setup
   ```

4. **Create a superuser:**
   ```bash
   make superuser
   ```

5. **Start the development server:**
   ```bash
   make run
   ```
   Visit `http://127.0.0.1:8000/health/` to verify the application is running.

## Development Commands

We provide a `Makefile` with common commands:

- `make install`: Install dependencies from `requirements.txt`.
- `make mysql-up`: Start the MySQL container in the background.
- `make mysql-down`: Stop the MySQL container.
- `make mysql-logs`: View the MySQL container logs.
- `make mysql-status`: View the status of the Docker compose services.
- `make migrate`: Apply database migrations.
- `make makemigrations`: Generate new database migrations.
- `make check`: Run Django system checks.
- `make test`: Run the test suite.
- `make shell`: Open the Django interactive shell.
- `make superuser`: Create a new superuser.
- `make run`: Start the Django development server.
- `make setup`: Install dependencies, start MySQL, run migrations, and check the project.
- `make down`: Stop MySQL without deleting the volume.

## Database Management

- Django runs on `127.0.0.1:8000` (on the host).
- MySQL runs on `127.0.0.1:3306` (in Docker).
- When Django is running on the host, `DB_HOST=127.0.0.1` connects to the exposed Docker port.
- When Django is running inside Docker (via the provided Dockerfile in later stages), `DB_HOST=mysql` would be used instead.
- **Note:** `docker compose down` or `make mysql-down` simply stops and removes the container, but **preserves** the named database volume.
- **Warning:** Running `docker compose down -v` is **destructive** because it deletes the database volume and therefore destroys all local database data.
