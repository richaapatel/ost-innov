# SkillSwap

SkillSwap is a Django monolith for learning and teaching skills in a community. Members can manage their profiles, discover skills and people, find reciprocal matches, send exchange requests, and monitor activity from an authenticated dashboard.

## Features

- Email-based Django session authentication with server-side password validation.
- Current-user profile editing with public member profiles.
- Searchable, category-filtered skill library with offered/wanted relationships.
- Community discovery and reciprocal skill matching.
- Exchange requests with protected permissions and the state machine:

  ```text
  pending → accepted → completed
  pending → rejected
  ```

- Authenticated dashboard with request summaries, match recommendations, and in-memory Matplotlib analytics.
- Django admin configuration for users, skills, and exchanges.

## Technology stack

- Python 3.12+
- Django
- MySQL 8.0 and `mysqlclient`
- Django templates, forms, ORM, sessions, and CSRF protection
- Bootstrap 5.3, Bootstrap Icons, and jQuery through versioned CDN links
- Matplotlib with the non-GUI `Agg` backend

## Project structure

```text
accounts/    User model, authentication, and current-user profile
skills/      Skill model, library, and skill relationships
community/   Discovery, matching, and public member profiles
exchanges/   Exchange requests and status transitions
dashboard/   Authenticated summaries and Matplotlib chart endpoints
core/        Landing and health/protected utility views
templates/   Shared layout and server-rendered UI
static/      Project CSS and progressive-enhancement JavaScript
```

## Requirements and environment

Install Python dependencies from `requirements.txt`. Copy the safe template and create local values in `.env`:

```bash
cp .env.example .env
python -m venv venv
source venv/bin/activate       # Windows: venv\\Scripts\\activate
make install
```

`.env` is ignored by Git. Do not commit real secrets or production database credentials. Important settings include `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT`.

## Docker/MySQL setup

The provided Compose file runs MySQL 8.0 with a healthcheck and persistent named volume. The Django development server runs on the host by default and connects to `127.0.0.1:3306`.

```bash
make mysql-up
make migrate
make run
```

When Django runs inside a container, use `DB_HOST=mysql`. `docker compose down` preserves the named volume; `docker compose down -v` removes local database data and is destructive.

## Migrations, seed data, and tests

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
python manage.py test
python manage.py collectstatic --noinput
python manage.py seed_demo_data
```

The `seed_demo_data` command is idempotent. It creates six demo users, ten skills, and valid exchanges covering every status without deleting existing data.

Development-only demo credentials:

- Users: `alice@example.com`, `bob@example.com`, `carlos@example.com`, `diana@example.com`, `elena@example.com`, `frank@example.com`
- Password: `SkillSwapDemoOnly123!`

These credentials are for local development only. Change or remove them before using any non-development environment.

## Main routes

Authentication and profile:

- `/accounts/register/` — registration (`accounts:register`)
- `/accounts/login/` — email login (`accounts:login`)
- `/accounts/logout/` — CSRF-protected POST logout (`accounts:logout`)
- `/accounts/profile/` — authenticated profile (`accounts:profile`)

Skills and community:

- `/skills/` — public skill library (`skills:list`)
- `/skills/create/` — authenticated skill creation (`skills:create`)
- `/discover/` — member discovery (`community:discover`)
- `/discover/matches/` — authenticated recommendations (`community:matches`)
- `/members/<id>/` — public member profile (`community:member_detail`)

Exchanges:

- `/exchanges/` — sent and received requests (`exchanges:list`)
- `/exchanges/create/` — request creation (`exchanges:create`)
- `/exchanges/<id>/` — participant-only detail (`exchanges:detail`)
- `/exchanges/<id>/accept/`, `/reject/`, `/complete/` — protected transitions

Dashboard and analytics:

- `/dashboard/` — authenticated dashboard (`dashboard:index`)
- `/dashboard/charts/skill-demand.png` — private skill-demand chart
- `/dashboard/charts/exchange-status.png` — private exchange-status chart

The chart endpoints require an authenticated session, return `image/png`, and generate figures in memory. Generated chart files are not stored in the repository, `static/`, or `media/`.

## Authentication and security

Django manages password hashing, sessions, authentication cookies, middleware, and CSRF protection. Email addresses are normalized by the registration form, passwords are never displayed or stored in plaintext, and protected views use Django authentication decorators. Exchange permissions are rechecked in the service layer with transaction locking; a user can only act on their own requests or requests where they are the teacher.

Public member profiles intentionally expose only name, bio, member-since date, initials, and skill relationships. Email, password data, permissions, and session details remain private.

## Static and media handling

Project assets live under `static/`. Bootstrap, Bootstrap Icons, and jQuery remain centralized in `templates/base.html` and are loaded from explicit CDN versions. Matplotlib charts are generated in memory and are not static or media files. No profile-image upload feature is enabled in this MVP.

## Useful Make targets

```text
make install
make mysql-up
make migrate
make makemigrations
make check
make test
make seed
make run
```
