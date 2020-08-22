# Shortify
Website for URL shortening.

# Setup and run project using `docker-compose up`
* Install `docker-ce` and `docker-compose` (check if its setup correctly by running `docker run hello-world`)
* `git clone https://github.com/albertas/shortify`  # Clones this repository
* `cd shortify`  # Goes to project directory
* `make`  # Prepares Python virtual env and installs dependencies to it
* `make test`  # Executes automated tests to see if everything was setup correctly
* `make migrate`  # Creates local SQLite3 database and prepares it for usage
* `make run`  # Starts local development server which can be accessed at [localhost:8000](http://localhost:8000),
  profiling information at [localhost:8000/silk/](http://localhost:8000/silk/) and
  admin page at [localhost:8000/silk/](http://localhost:8000/silk/)

# Setup and run project without docker
* `git clone https://github.com/albertas/shortify`  # Clones this repository
* `cd shortify`  # Goes to project directory
* `make env`  # Prepares Python virtual env and installs dependencies to it
* `venv/bin/python manage.py test --settings=shortify.settings.test`  # Executes automated tests to see if everything was setup correctly
* `venv/bin/python manage.py migrate`  # Creates local SQLite3 database and prepares it for usage
* `venv/bin/python manage.py runserver`  # Starts local development server which can be accessed at [localhost:8000](http://localhost:8000), 
  profiling information at [localhost:8000/silk/](http://localhost:8000/silk/) and
  admin page at [localhost:8000/silk/](http://localhost:8000/silk/)

# Considered decisions
## How to optimize database queries?
In order to increase performance `db_index=True` has to be used. However primary keys are
automatically, hence `db_index=True` can be omitted for these fields.

Each shortened URL click creates a separate `Click` record in the database.
To disable shortened URL after fixed number of clicks, number of `Click` records has to be counted
for that URL, which is time consuming operation. Counting operation can be avoided if a counter
value is stored in the database. Updating the counter would require additional database hit during
shortened URL redirection. However, this database hit can be moved out of URL redirection view to
`Click.post_save` signal, this way increasing URL redirection efficiency.

## What max URL size has to be allowed?
Max length of URLs submitted by users has to be restricted in order to avoid database flooding attacks.
Hence Django URLField, which requires predefined max length can be used instead of TextField for
storing URLs.

In order to make our URL shortening service as usable as possible we should choose quite loose URL
length restriction. For example, 8190 bytes would be a good option, because its maximum rational
size base on Gunicorn, see: https://docs.gunicorn.org/en/stable/settings.html#limit-request-line
