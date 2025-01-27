# Consult

Consult is a machine learning and LLM-powered tool to automate the processing of public consultations.

> [!IMPORTANT]
> Incubation Project: This project is an incubation project; as such, we don't recommend using this for critical use cases yet. We are currently in a research stage, trialling the tool for case studies across the Civil Service. If you are a civil servant and wish to take part in our research stage, please contact us at i-dot-ai-enquiries@cabinetoffice.gov.uk.


## Setting up the application

### External dependencies

- PostgreSQL (`brew install postgresql`)
- redis (`brew install redis`)
- GraphViz (`brew install graphviz`), for generating diagrams
- precommit (`brew install pre-commit`)

Installation instructions assume using a Mac with Homebrew.

### Clone the repo

```
git clone git@github.com:i-dot-ai/consult.git
```

In the new repo install pre-commit:
```
cd consult
```
```
pre-commit install
```
Pre-commit identifies some potential secrets on commit (but will not catch all potential sensitive information).

### Environment variables

Populate `.env` by copying `.env.example` and filling in required values.


### Install packages

Ensure you have `python 3.12.3`, `poetry` and `npm` installed. Then run `poetry install`, and `npm install`.

### Database setup

```
brew services start postgresql
```
This will run the postgresql locally.

```
make dev_environment
```

This will set up dev and test databases with dummy data. See the definition of that make task for the various steps.

It will also set up the admin account to dev environment.

You will have an staff user (i.e. one that can access the admin) created with the username `email@example.com` and the password `admin`.


Confirm everything is working with

```
make check_db
```

(You can see all the available `make` commands by running bare `make` or `make help`).

### Run the application

Make sure redis is running:
```
brew services start redis
```

The database should also be running as described above.

Then run:
```
make serve
```

Go to `http://localhost:8000` in the browser.

### Run the tests

```
make test
```

## The database

### Generating dummy data
Only run this in development. Will create a consultation with 100 complete
responses in a variety of question formats. This runs as part of `make
dev_environment`, but you can run it more than once.

```
make dummy_data
```

Or go to `/support/consultations/` and generate a dummy consultation from there.

### Database migrations and schema diagram

If you use the `make migrate` command to run migrations, the diagram below will
be regenerated automatically. If you need to generate it outside that process,
you can run `manage.py generate_erd`. (You will need `graphviz` installed: see
[`pydot` docs](https://pypi.org/project/pydot/)).

![](docs/erd.png)

## Login

### Magic links

You can sign into the application using a magic link, requested via `/sign-in/`. 
You need to have a user set-up first - add new users in `/support/users/` 
(only be done by `staff` members).

When running locally, you can create your first admin user using `make dev_admin_user`, 
on dev/pre-prod/prod ask one of the existing members of the team.

For convenience, in local dev environments the value of the magic link will be
logged along with the rest of the server logs.


### The frontend

#### CSS

We depend on `govuk-frontend` for GOV.UK Design System styles.

`django-compressor` should work automatically to compile the govuk-frontend
SCSS on the first request and any subsequent request after the SCSS has
changed. In the meantime it will read from `frontend/CACHE`, which is
`.gitignore`d.

In production, we prepopulate `frontend/CACHE` using `manage.py compress`
which will mean that every request is served from the cache.

`django-compressor` also takes care of fingerprinting and setting cache headers
for our CSS.

#### Fonts and images

The govuk assets are versioned in the `npm` package. `make dev_environment`
includes a step to copy them to the `frontend` folder from where `runserver`
can serve them; you can rerun this with `make govuk_frontend`.

## Docs

We are using `adr-tools` to manage "Architectural Decision Records" - to track decisions made. To install and use: https://github.com/npryce/adr-tools.