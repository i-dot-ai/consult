-include .env
export AWS_ACCOUNT_ID
export AWS_REGION
export ECR_REPO_NAME
export APP_NAME


.PHONY: help
help:     ## Show this help.
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'


.PHONY: setup_db
setup_db: ## Set up the development db on docker
	docker compose up -d postgres

.PHONY: reset_db
reset_db: ## Reset the dev db
	docker compose down postgres
	docker volume rm -f consult_postgres_data
	$(MAKE) setup_db

.PHONY: check_db
check_db: ## Make sure the db is addressable
	cd backend && PYTHONPATH=.. poetry run python manage.py check --database default

.PHONY: migrations
migrations: ## Generate migrations
	cd backend && PYTHONPATH=.. poetry run python manage.py makemigrations

.PHONY: migrate
migrate: ## Apply migrations
	cd backend && PYTHONPATH=.. poetry run python manage.py migrate
	cd backend && PYTHONPATH=.. poetry run python manage.py generate_erd

.PHONY: serve
serve: ## Run the server and the worker
	docker compose up -d postgres redis
	cd backend && poetry run honcho start

.PHONY: test
test: ## Run the tests
	cd backend && PYTHONPATH=.. poetry run pytest tests/ --random-order

.PHONY: test-end-to-end
test-end-to-end:
		@echo "Creating test database..."
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "DROP DATABASE IF EXISTS consult_e2e_test;" || true
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "CREATE DATABASE consult_e2e_test;"
		@echo "Backing up current DATABASE_URL..."
		@cp .env .env.backup
		@echo "Setting test DATABASE_URL..."
		@sed -i.tmp 's|DATABASE_URL=.*|DATABASE_URL=psql://postgres:postgres@localhost:5432/consult_e2e_test|' .env && rm .env.tmp  # pragma: allowlist secret
		@echo "create user"
		docker compose run backend venv/bin/python manage.py createadminusers
		@echo "Running end-to-end tests..."
		cd e2e_tests && npm install
		cd e2e_tests && npx playwright install --with-deps
		cd e2e_tests && npm run e2e
		@echo "Cleaning up test database..."
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "DROP DATABASE IF EXISTS consult_e2e_test;"
		@echo "Restoring original .env..."
		@mv .env.backup .env

.PHONY: check-python-code
check-python-code: ## Check Python code - linting and mypy
	cd backend && poetry run ruff check --select I .
	cd backend && poetry run ruff check .
	# Re-add mypy here and remove from pre-commit once errors fixed
	# cd backend && poetry run mypy . --ignore-missing-imports

.PHONY: format-python-code
format-python-code: ## Format Python code including sorting imports
	cd backend && poetry run ruff check --select I . --fix
	cd backend && poetry run ruff check . --fix
	cd backend && poetry run ruff format .

.PHONY: dummy_data
dummy_data: ## Generate dummy consultations. Only works in dev
	cd backend && PYTHONPATH=.. poetry run python manage.py generate_dummy_data

.PHONY: dev_admin_user
dev_admin_user:
	cd backend && PYTHONPATH=.. poetry run python manage.py shell -c "from backend.authentication.models import User; User.objects.create_user(email='email@example.com', password='admin', is_staff=True)" # pragma: allowlist secret

.PHONY: dev_environment
dev_environment: reset_db migrate dummy_data govuk_frontend dev_admin_user ## set up the database with dummy data and configure govuk_frontend

# Docker
AWS_REGION=eu-west-2
APP_NAME=consult
ECR_URL=$(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com
ECR_REPO_URL=$(ECR_URL)/$(ECR_REPO_NAME)

ifeq ($(service),consult)
    ECR_REPO_NAME=$(APP_NAME)
else
    ECR_REPO_NAME=$(APP_NAME)-$(service)
endif

DOCKER_BUILDER_CONTAINER=$(APP_NAME)
cache ?= ./.build-cache
APP_CACHE_DIR=$(cache)/$(APP_NAME)/$(service)
IMAGE_TAG=$$(git rev-parse HEAD)

AUTO_APPLY_RESOURCES = module.backend.aws_ecs_task_definition.aws-ecs-task \
                       module.backend.aws_ecs_service.aws-ecs-service \
                       module.backend.data.aws_ecs_task_definition.main \
                       module.backend.aws_lb_listener_rule.authentication[0] \
                       module.frontend.aws_ecs_task_definition.aws-ecs-task \
                       module.frontend.aws_ecs_service.aws-ecs-service \
                       module.frontend.data.aws_ecs_task_definition.main \
                       module.frontend.aws_lb_listener_rule.authentication[0] \
                       module.worker.aws_ecs_task_definition.aws-ecs-task \
                       module.worker.aws_ecs_service.aws-ecs-service \
                       module.worker.data.aws_ecs_task_definition.main \
                       module.batch_job_definition.aws_batch_job_definition.job_definition \
                       module.waf.aws_wafv2_ip_set.host_ip_whitelist \
                       module.waf.aws_wafv2_ip_set.header_secured_host_ip_whitelist \
                       module.waf.aws_wafv2_ip_set.uri_path_ip_configuration \
                       module.waf.aws_wafv2_web_acl.this \
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
	--cache-to type=local,dest=$(APP_CACHE_DIR) \
	--cache-from type=local,src=$(APP_CACHE_DIR) .
else
	DOCKER_BUILDKIT=1 docker buildx build --platform linux/amd64 --load --builder=$(DOCKER_BUILDER_CONTAINER) -t $(IMAGE) \
	--cache-to type=local,dest=$(APP_CACHE_DIR) \
	--cache-from type=local,src=$(APP_CACHE_DIR) -f $(service)/Dockerfile .
endif

.PHONY: docker_build_local
docker_build_local: ## Build the docker container for the specified service locally
	DOCKER_BUILDKIT=1 docker build --platform=linux/amd64 -t $(IMAGE) -f $(service)/Dockerfile .


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
	terraform -chdir=./terraform/$(instance)  workspace new $(env)

tf_set_workspace:
	terraform -chdir=./terraform/$(instance) workspace select $(env)

tf_set_or_create_workspace:
	make tf_set_workspace || make tf_new_workspace

tf_init_and_set_workspace:
	make tf_init && make tf_set_workspace

.PHONY: tf_init
tf_init: ## Initialise terraform
	terraform -chdir=./terraform/$(instance) init -backend-config=$(TF_BACKEND_CONFIG) -reconfigure

.PHONY: tf_plan
tf_plan: ## Plan terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./terraform/$(instance) plan -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_apply
tf_apply: ## Apply terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./terraform/$(instance) apply -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args} ${args}

.PHONY: tf_init_universal
tf_init_universal: ## Initialise terraform
	terraform -chdir=./terraform/universal init -backend-config=../$(TF_BACKEND_CONFIG)

.PHONY: tf_apply_universal
tf_apply_universal: ## Apply terraform
	terraform -chdir=./terraform workspace select prod && \
	terraform -chdir=./terraform/universal apply -var-file=../$(CONFIG_DIR)/prod-input-params.tfvars

.PHONY: tf_auto_apply
tf_auto_apply: ## Auto apply terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./terraform apply -auto-approve -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args} $(target_modules)

.PHONY: tf_destroy
tf_destroy: ## Destroy terraform
	make tf_init_and_set_workspace && \
	terraform -chdir=./terraform destroy -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${tf_build_args}

.PHONY: tf_import
tf_import:
	make tf_init_and_set_workspace && \
	terraform -chdir=./terraform/$(instance) import ${tf_build_args} -var-file=$(CONFIG_DIR)/${env}-input-params.tfvars ${name} ${id}

# Release commands to deploy your app to AWS
.PHONY: release
release: ## Deploy app
## bail if env is not set
	@if [ -z "$(env)" ]; then \
		echo "make release requires an env= argument"; \
		exit 1; \
	fi

	chmod +x ./terraform/scripts/release.sh && ./terraform/scripts/release.sh $(env)
