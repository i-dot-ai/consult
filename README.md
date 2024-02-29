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
psql -d postgres -c 'GRANT ALL ON database consultations_test TO consultations_test;'
```

Confirm it works with

```
poetry run python manage.py check --database default
```

## Frontend Prototype

Located at `/prototype`. Using the Gov.uk Prototype Kit. This is work in progress, not all pages are available yet.

### How to run

Ensure you have a recent version of Node.js installed (v16 or greater). Then, from the prototype directory, run:
`npm install`

To start development server:
`npm run dev`

Start at http://localhost:3000/
