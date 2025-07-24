-include .env
export AWS_ACCOUNT_ID
export AWS_REGION
export ECR_REPO_NAME
export APP_NAME


.PHONY: help
help:     ## Show this help.
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'


.PHONY: setup_dev_db
setup_dev_db: ## Set up the development db on a local postgres
	createdb consultations_dev
	-createuser consultations_dev
	-psql -d postgres -c 'GRANT ALL ON database consultations_dev TO consultations_dev;'
	-psql -d postgres -c 'ALTER USER consultations_dev WITH SUPERUSER;'

.PHONY: reset_dev_db
reset_dev_db: ## Reset the dev db
	-dropdb consultations_dev
	$(MAKE) setup_dev_db

.PHONY: setup_test_db
setup_test_db:  ## Set up the test db on a local postgres
	createdb consultations_test
	-createuser consultations_test
	-psql -d postgres -c 'GRANT ALL ON database consultations_test TO consultations_test; ALTER USER consultations_test CREATEDB;'
	-psql -d postgres -c 'ALTER USER consultations_test WITH SUPERUSER;'

.PHONY: reset_test_db
reset_test_db: ## Reset the test db
	-psql -lqt | cut -d \| -f 1 | grep -qw consultations_test && dropdb consultations_test
	$(MAKE) setup_test_db

.PHONY: check_db
check_db: ## Make sure the db is addressable
	poetry run python manage.py check --database default

.PHONY: migrate
migrate: ## Apply migrations
	poetry run python manage.py migrate
	poetry run python manage.py generate_erd

.PHONY: serve
serve: ## Run the server and the worker
	poetry run honcho start

.PHONY: test
test: ## Run the tests
	poetry run pytest tests/ --random-order

.PHONY: test-migrations
test-migrations: ## Run the migration tests separately
	poetry run pytest migration_tests/ --random-order

.PHONY: check-python-code
check-python-code: ## Check Python code - linting and mypy
	poetry run ruff check --select I .
	poetry run ruff check .
	# Re-add mypy here and remove from pre-commit once errors fixed
	# poetry run mypy . --ignore-missing-imports

.PHONY: format-python-code
format-python-code: ## Format Python code including sorting imports
	poetry run ruff check --select I . --fix
	poetry run ruff check . --fix
	poetry run ruff format .

.PHONY: govuk_frontend
govuk_frontend: ## Pull govuk-frontend
	npm install
	poetry run python manage.py collectstatic --noinput

.PHONY: build-frontend
build-frontend: ## Build CSR and SSR Lit components
	npm run build-lit

.PHONY: dummy_data
dummy_data: ## Generate a dummy consultation. Only works in dev
	poetry run python manage.py generate_dummy_data

.PHONY: dev_admin_user
dev_admin_user:
	poetry run python manage.py shell -c "from consultation_analyser.authentication.models import User; User.objects.create_user(email='email@example.com', password='admin', is_staff=True)" # pragma: allowlist secret

.PHONY: dev_environment
dev_environment: reset_dev_db migrate dummy_data reset_test_db govuk_frontend dev_admin_user ## set up the database with dummy data and configure govuk_frontend

# Docker
AWS_REGION=eu-west-2
APP_NAME=consult
ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO_URL=$(ECR_URL)/$(ECR_REPO_NAME)
DOCKER_CACHE_BUCKET=i-dot-ai-docker-cache

ifeq ($(service),consult)
    ECR_REPO_NAME=$(APP_NAME)
else
    ECR_REPO_NAME=$(APP_NAME)-$(service)
endif

DOCKER_BUILDER_CONTAINER=$(APP_NAME)
IMAGE_TAG=$$(git rev-parse HEAD)

AUTO_APPLY_RESOURCES = module.ecs.aws_ecs_task_definition.aws-ecs-task \
                       module.ecs.aws_ecs_service.aws-ecs-service \
                       module.ecs.data.aws_ecs_task_definition.main \
                       module.worker.aws_ecs_task_definition.aws-ecs-task \
                       module.worker.aws_ecs_service.aws-ecs-service \
                       module.worker.data.aws_ecs_task_definition.main \
                       module.batch_job_definition.aws_batch_job_definition.job_definition \
                       module.waf.aws_wafv2_ip_set.host_ip_whitelist \
                       module.waf.aws_wafv2_ip_set.header_secured_host_ip_whitelist \
                       module.waf.aws_wafv2_ip_set.uri_path_ip_configuration \
                       aws_secretsmanager_secret.django_secret \
                       aws_secretsmanager_secret.debug \
											 module.load_balancer.aws_security_group_rule.load_balancer_http_whitelist \
											 module.load_balancer.aws_security_group_rule.load_balancer_https_whitelist

target_modules = $(foreach resource,$(AUTO_APPLY_RESOURCES),-target $(resource))
IMAGE=$(ECR_REPO_URL):$(IMAGE_TAG)

ifndef cache
	override cache = ./.build-cache
endif

.PHONY: docker_build
docker_build: ## Build the docker container for the specified service when running in CI/CD
ifeq ($(service),consult)
	DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 --load --builder=$(DOCKER_BUILDER_CONTAINER) -t $(IMAGE) \
	--cache-to type=local,dest=$(cache) \
	--cache-from type=local,src=$(cache) .
else
	DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 --load --builder=$(DOCKER_BUILDER_CONTAINER) -t $(IMAGE) \
	--cache-to type=local,dest=$(cache) \
	--cache-from type=local,src=$(cache) -f $(service)/Dockerfile .
endif

.PHONY: docker_build_local
docker_build_local: ## Build the docker container for the specified service locally
	DOCKER_BUILDKIT=1 docker build --platform=linux/amd64 -t $(IMAGE) -f $(service)/Dockerfile .

.PHONY: docker_run
docker_run: ## Run the docker container
	docker run -e DATABASE_URL=psql://consultations_dev:@host.docker.internal:5432/consultations_dev -p 8000:8000 $(IMAGE)

.PHONY: docker_shell
docker_shell: ## Run the docker container
	docker run -e DATABASE_URL=psql://consultations_dev:@host.docker.internal:5432/consultations_dev -it $(IMAGE) /bin/bash

.PHONY: docker_test
docker_test: ## Run the tests in the docker container
	docker run -e DATABASE_URL=psql://consultations_test:@host.docker.internal:5432/consultations_test $(IMAGE) ./venv/bin/pytest

.PHONY: docker_login
docker_login:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)

.PHONY: docker_push
docker_push:
	docker push $(IMAGE)

docker_tag_is_present_on_image:
	aws ecr describe-images --repository-name $(ECR_REPO_NAME) --image-ids imageTag=$(IMAGE_TAG) --query 'imageDetails[].imageTags' | jq -e '.[]|any(. == "$(tag)")' >/dev/null

check_docker_tag_exists:
	if ! make docker_tag_is_present_on_image tag=$(IMAGE_TAG) 2>/dev/null; then \
		echo "Error: ECR tag $(IMAGE_TAG) does not exist." && exit 1; \
	fi

docker_update_tag: ## Tag the docker image with the specified tag
	# repo and tag variable are set from git-hub core workflow. example: repo=ecr-repo-name, tag=dev
	if make docker_tag_is_present_on_image 2>/dev/null; then echo "Image already tagged with $(tag)" && exit 0; fi && \
	MANIFEST=$$(aws ecr batch-get-image --repository-name $(ECR_REPO_NAME) --image-ids imageTag=$(IMAGE_TAG) --query 'images[].imageManifest' --output text) && \
	aws ecr put-image --repository-name $(ECR_REPO_NAME) --image-tag $(tag) --image-manifest "$$MANIFEST"

# Ouputs the value that you're after - useful to get a value i.e. IMAGE_TAG out of the Makefile
.PHONY: docker_echo
docker_echo:
	echo $($(value))

ifeq ($(instance),postgres)
CONFIG_DIR=../../../consult-infra-config
tf_build_args=
else ifeq ($(instance),universal)
CONFIG_DIR=../../../consult-infra-config
env=prod
else
CONFIG_DIR=../../consult-infra-config
tf_build_args=-var "image_tag=$(IMAGE_TAG)"
endif

TF_BACKEND_CONFIG=$(CONFIG_DIR)/backend.hcl


tf_new_workspace:
	terraform -chdir=./infrastructure/$(instance)  workspace new $(env)

tf_set_workspace:
	terraform -chdir=./infrastructure/$(instance) workspace select $(env)

tf_set_or_create_workspace:
	make tf_set_workspace || make tf_new_workspace

tf_init_and_set_workspace:
	make tf_init && make tf_set_workspace

.PHONY: tf_init
tf_init: ## Initialise terraform
	terraform -chdir=./infrastructure/$(instance) init -backend-config=$(TF_BACKEND_CONFIG) -reconfigure

.PHONY: tf_plan
tf_plan: ## Plan terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./infrastructure/$(instance) plan -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_apply
tf_apply: ## Apply terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./infrastructure/$(instance) apply -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args} ${args}

.PHONY: tf_init_universal
tf_init_universal: ## Initialise terraform
	terraform -chdir=./infrastructure/universal init -backend-config=../$(TF_BACKEND_CONFIG)

.PHONY: tf_apply_universal
tf_apply_universal: ## Apply terraform
	terraform -chdir=./infrastructure workspace select prod && \
	terraform -chdir=./infrastructure/universal apply -var-file=../$(CONFIG_DIR)/prod-input-params.tfvars

.PHONY: tf_auto_apply
tf_auto_apply: ## Auto apply terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./infrastructure apply -auto-approve -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args} $(target_modules)

.PHONY: tf_destroy
tf_destroy: ## Destroy terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./infrastructure destroy -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_import
tf_import:
	make tf_init_and_set_workspace && \
	terraform -chdir=./infrastructure/$(instance) import ${tf_build_args} -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${name} ${id}

# Release commands to deploy your app to AWS
.PHONY: release
release: ## Deploy app
## bail if env is not set
	@if [ -z "$(env)" ]; then \
		echo "make release requires an env= argument"; \
		exit 1; \
	fi

	chmod +x ./infrastructure/scripts/release.sh && ./infrastructure/scripts/release.sh $(env)
