prepare_environment: venv
	venv/bin/pip install -r requirements.txt
	venv/bin/pip check

venv:
	python3 -m venv venv
