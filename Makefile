.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z\.\-\_]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: setup_dev_db
setup_dev_db: ## Set up the development db on a local postgres
	createdb consultations_dev
	-createuser consultations_dev
	-psql -d postgres -c 'GRANT ALL ON database consultations_dev TO consultations_dev;'

.PHONY: reset_dev_db
reset_dev_db: ## Reset the dev db
	dropdb consultations_dev
	$(MAKE) setup_dev_db

.PHONY: setup_test_db
setup_test_db:  ## Set up the test db on a local postgres
	createdb consultations_test
	-createuser consultations_test
	-psql -d postgres -c 'GRANT ALL ON database consultations_test TO consultations_test; ALTER USER consultations_test CREATEDB;'

.PHONY: reset_test_db
reset_test_db: ## Reset the test db
	dropdb consultations_test
	$(MAKE) setup_test_db

.PHONY: check_db
check_db: ## Make sure the db is addressable
	poetry run python manage.py check --database default

.PHONY: migrate
migrate: ## Apply migrations
	poetry run python manage.py migrate
	poetry run python manage.py generate_erd

.PHONY: serve
serve: ## Run the server
	poetry run python manage.py runserver

.PHONY: test
test: ## Run the tests
	poetry run pytest

.PHONY: govuk_frontend
govuk_frontend: ## Pull govuk-frontend
	npm install
	poetry run python manage.py collectstatic --noinput

.PHONY: dummy_data
dummy_data: ## Generate a dummy consultation. Only works in dev
	poetry run python manage.py generate_dummy_data
