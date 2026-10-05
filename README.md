# SkillSwap Stage 1

This repository contains the foundational setup for the SkillSwap application (Stage 1). It provides a Django backend configured with a custom User model, a MySQL database running in Docker, and foundational settings, templates, and static files.

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
