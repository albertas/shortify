prepare_environment: venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip check

venv:
	python3 -m venv venv

test:
	venv/bin/python manage.py test --settings shortify.settings

shell:
	venv/bin/python manage.py shell_plus --settings shortify.settings
