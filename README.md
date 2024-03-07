# Consultation Analyser

This project is currently at prototyping stage.

The Consultation Analyser is an AI-powered tool to automate the processing of public consultations.

## Setting up the application

Populate `.env` by copying `.env.example` and filling in required values.

Ensure you have `python > 3.10` and `poetry` installed.

```
poetry install
```

### Database

Assuming local postgres:

```
# dev
createdb consultations_dev
createuser consultations_dev
psql -d postgres -c 'GRANT ALL ON database consultations_dev TO consultations_dev;'

# test
createdb consultations_test
createuser consultations_test
psql -d postgres -c 'GRANT ALL ON database consultations_test TO consultations_test; ALTER USER consultations_test CREATEDB;'
```

Confirm it works with

```
poetry run python manage.py check --database default
```


### Run the application
```
poetry run python manage.py runserver
```

### Run the tests

```
poetry run pytest
```


### Frontend


#### CSS

We depend on `govuk-frontend` for GOV.UK Design System styles.

```
npm install
```

Once this has been done, `django-compressor` should work automatically to
compile the govuk-frontend SCSS on the first request and any subsequent request
after the SCSS has changed. In the meantime it will read from `frontend/CACHE`,
which is `.gitignore`d.

When we get to production, we can prepopulate `frontend/CACHE` using `manage.py
compress` before building our container, which will mean that every request
will be served from the cache.

`django-compressor` also takes care of fingerprinting and setting cache headers
for our CSS so it can be cached.

#### Fonts and images

The govuk assets are versioned in the `npm` package. On initial app setup you will need to run `poetry run python manage.py collectstatic` to copy them to the `frontend` folder from where `runserver` can serve them.

We’ll revisit this process when we deploy the app.


## Frontend Prototype

Located at `/prototype`. Using the Gov.uk Prototype Kit. This is work in progress, not all pages are available yet.

### How to run

Ensure you have a recent version of Node.js installed (v16 or greater). Then, from the prototype directory, run:
`npm install`

To start development server:
`npm run dev`

Start at http://localhost:3000/
