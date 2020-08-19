# Shortify
Website for URL shortening.

# How to setup environment and run project locally
* `git clone https://github.com/albertas/shortify`  # Clones this repository
* `cd shortify`  # Goes to project directory
* `make`  # Prepares Python virtual env and installs dependencies to it
* `make test`  # Executes automated tests to see if everything was setup correctly
* `make migrate`  # Creates local SQLite3 database and prepares it for usage
* `make run`  # Starts local development server which can be accessed at [localhost:8000](http://localhost:8000)

# Considered decisions
## How to optimize database queries?
In order to increase performance `db_index=True` has to be used. However primary keys are automatically
indexed, because they must be unique, hence `db_index=True` can be ommited for these fields.

## What max URL size has to be allowed?
Max lenght of URLs submitted by users has to be restriced in order to avoid database flooding attacks.
Hence Django URLField, which requires predefined max length can be used instead of TextField for
storing URLs.

In order to make our URL shortening service as usable as possible we should choose quite loose URL
length restriction. For example, 8190 bytes would be a good option, because its maximum rational
size base on Gunicorn, see: https://docs.gunicorn.org/en/stable/settings.html#limit-request-line
