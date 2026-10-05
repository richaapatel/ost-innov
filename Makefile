.PHONY: install mysql-up mysql-down mysql-logs mysql-status migrate makemigrations check test shell superuser run setup down

install:
	pip install -r requirements.txt

mysql-up:
	docker compose up -d mysql

mysql-down:
	docker compose stop mysql

mysql-logs:
	docker compose logs -f mysql

mysql-status:
	docker compose ps

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

check:
	python manage.py check

test:
	python manage.py test

shell:
	python manage.py shell

superuser:
	python manage.py createsuperuser

run:
	python manage.py runserver

setup: install mysql-up
	@echo "Waiting for MySQL to be ready..."
	@sleep 15
	python manage.py migrate
	python manage.py check

down:
	docker compose stop mysql
