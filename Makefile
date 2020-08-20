env: venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip check

venv:
	python3 -m venv venv

test:
	docker-compose run web /usr/local/bin/python manage.py test $(TEST_ME_PLEASE) --settings=shortify.settings.test

shell:
	docker-compose run web /usr/local/bin/python manage.py shell_plus --settings=shortify.settings.dev

makemigrations:
	docker-compose run web /usr/local/bin/python manage.py makemigrations --settings=shortify.settings.dev

migrate:
	docker-compose run web /usr/local/bin/python manage.py migrate --settings=shortify.settings.dev

run:
	docker-compose up
