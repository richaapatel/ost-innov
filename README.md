# SkillSwap

This repository contains the SkillSwap Django application: a custom email-based User model, MySQL-backed skills and exchanges, session authentication, profiles, a skill library, community discovery, matching recommendations, and the exchange workflow. Dashboard analytics are not implemented yet.

## Stage 3 authentication

Authentication uses Django's built-in session system. Users register and log in with their email address, and passwords are hashed with Django's password hashing utilities.

- Registration: `/accounts/register/`
- Login: `/accounts/login/`
- Logout: POST `/accounts/logout/`
- Protected-route example: `/protected/`

Registration requires a full name, a unique email address, and a password from 8–128 characters containing uppercase, lowercase, a number, and a special character. Invalid credentials use a generic error message, inactive users cannot authenticate, and safe `next` redirects are preserved after login. Logout is CSRF-protected and session-based; authentication is not stored in browser storage or application-managed tokens.

## Stage 4 profile

Authenticated users can view and edit their current profile at `/profile/` (`accounts:profile`). The profile displays an initials avatar, name, read-only email address, bio, member-since date, and any existing offered or wanted skills. Users can edit only their name and bio; updates are validated server-side, CSRF-protected, and saved through a POST–redirect–GET flow. Anonymous users are redirected to login.

## Skills, discovery, and public member profiles

- Skills: `/skills/` (`skills:list`) is publicly viewable and supports case-insensitive search, description search, and database-backed category filters.
- Authenticated users can create shared skills at `/skills/create/` and add or remove existing skills from their offered or wanted lists. These actions use CSRF-protected Django POST endpoints with progressive jQuery/AJAX enhancement.
- Discovery: `/discover/` (`community:discover`) supports member-name search, offered-skill filters, wanted-skill filters, combined filters, and nine-member pagination.
- Public profiles: `/members/<user_id>/` (`community:member_detail`) show only public profile information, initials, member-since date, and skill relationships. Email, password, permissions, and other private account data are not displayed.

Example discovery URL:

```text
/discover/?search=python&offered_skill=3&wanted_skill=7
```

## Matching

Authenticated users can visit `/discover/matches/` (`community:matches`). A candidate must offer at least one skill the current user wants to learn. The match score is the number of shared learning opportunities in both directions:

- Skills you want that they offer.
- Skills they want that you offer.

Results are sorted by score descending, then member name alphabetically. A match is labelled “Two-way match” only when both overlap sets are non-empty. The optional `?skill=<id>` filter is limited to skills currently in the user's wanted-skills list. Users without wanted skills receive an intentional prompt to add learning goals in the Skill Library.

## Exchange requests

Authenticated users can request to learn from another member through the reusable Request to Learn flow, or use the server-rendered fallback at `/exchanges/create/`. The selected skill list is restricted to the teacher's current offered skills and all relationships are rechecked server-side.

- Exchange list: `/exchanges/` (`exchanges:list`)
- Exchange detail: `/exchanges/<id>/` (`exchanges:detail`)
- Requests are visible to the teacher as Received Requests and to the learner as Sent Requests.
- Only the teacher can accept or reject a pending request.
- Either participant can complete an accepted request.

The state machine is:

```text
pending → accepted → completed
pending → rejected
```

Rejected and completed requests are terminal. A deterministic active-request key prevents duplicate pending requests for the same learner, teacher, and skill; it is cleared when a request leaves `pending`, allowing a later request.

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
