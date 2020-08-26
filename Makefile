env:
	docker-compose up -d --build
	docker exec -it shortify_web_1 bash

test:
	./manage.py test $(TEST_ME_PLEASE) --settings=shortify.settings.test

shell:
	./manage.py shell_plus

run:
	./manage.py runserver 0:8000

makemigrations:
	./manage.py makemigrations

migrate:
	./manage.py migrate
