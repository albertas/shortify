env: venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip check

venv:
	python3 -m venv venv

test:
	docker-compose run web /usr/local/bin/python manage.py test $(TEST_ME_PLEASE)

shell:
	docker-compose run web /usr/local/bin/python manage.py shell_plus

makemigrations:
	docker-compose run web /usr/local/bin/python manage.py makemigrations

migrate:
	docker-compose run web /usr/local/bin/python manage.py migrate

run:
	docker-compose up
