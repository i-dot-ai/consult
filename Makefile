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
	cd backend && PYTHONPATH=.. uv run python manage.py check --database default

.PHONY: migrations
migrations: ## Generate migrations
	cd backend && PYTHONPATH=.. uv run python manage.py makemigrations

.PHONY: migrate
migrate: ## Apply migrations
	cd backend && PYTHONPATH=.. uv run python manage.py migrate
	cd backend && PYTHONPATH=.. uv run python manage.py generate_erd

.PHONY: backend
backend: ## Run the backend and the worker
	docker compose up -d postgres redis
	cd backend && uv run honcho start

.PHONY: frontend
frontend: ## Run the frontend
	cd frontend && npm run dev

.PHONY: test-backend
test-backend: ## Run the backend tests
	cd backend && PYTHONPATH=.. uv run pytest tests/ --random-order

.PHONY: test-frontend
test-frontend: ## Run the frontend tests
	cd frontend && npm run test

.PHONY: test-end-to-end
test-end-to-end:
		@echo "Creating test database..."
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "DROP DATABASE IF EXISTS consult_e2e_test;" || true
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "CREATE DATABASE consult_e2e_test;"
		@echo "Backing up current DATABASE_URL..."
		@cp .env .env.backup
		@echo "Setting test DATABASE_URL..."
		@sed -i.tmp 's|DATABASE_URL=.*|DATABASE_URL=psql://postgres:postgres@localhost:5432/consult_e2e_test|' .env && rm .env.tmp  # pragma: allowlist secret
		@echo "Running migrations on test database..."
		docker compose run -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/consult_e2e_test backend venv/bin/python manage.py migrate  # pragma: allowlist secret
		@echo "Creating admin user..."
		docker compose run -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/consult_e2e_test backend venv/bin/python manage.py createadminusers  # pragma: allowlist secret
		@echo "Generating dummy data..."
		docker compose run -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/consult_e2e_test backend venv/bin/python manage.py generate_dummy_data  # pragma: allowlist secret
		@echo "Adding user to all consultations..."
		docker compose run -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/consult_e2e_test backend venv/bin/python manage.py shell -c "from authentication.models import User; from consultations.models import Consultation; user = User.objects.get(email='email@example.com'); [c.users.add(user) for c in Consultation.objects.all()]"  # pragma: allowlist secret
		@echo "Creating docker-compose override for test database..."
		@echo "services:" > docker-compose.override.yml
		@echo "  backend:" >> docker-compose.override.yml
		@echo "    environment:" >> docker-compose.override.yml
		@echo "      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/consult_e2e_test" >> docker-compose.override.yml  # pragma: allowlist secret
		@echo "Stopping any existing backend container..."
		@docker compose down backend 2>/dev/null || true
		@echo "Starting backend and frontend services with test database..."
		docker compose up -d backend
		docker compose up -d frontend
		@echo "Verifying backend is using correct database..."
		@sleep 3
		@docker compose exec backend sh -c 'echo "DATABASE_URL=$$DATABASE_URL"'
		@echo "Waiting for services to be ready..."
		@timeout 60 sh -c 'until curl -s http://localhost:3000 > /dev/null; do echo "Waiting for frontend..."; sleep 2; done' || (echo "Frontend failed to start" && docker compose logs frontend && exit 1)
		@timeout 60 sh -c 'until curl -s http://localhost:8000/api/user/ > /dev/null; do echo "Waiting for backend..."; sleep 2; done' || (echo "Backend failed to start" && docker compose logs backend && exit 1)
		@echo "Services ready!"
		@echo "Running end-to-end tests..."
		cd e2e_tests && npm install
		@if [ -z "$$CI" ]; then cd e2e_tests && npx playwright install --with-deps; fi
		cd e2e_tests && npm run e2e
		@echo "Cleaning up test database..."
		@docker exec -i $$(docker compose ps -q postgres) psql -U postgres -c "DROP DATABASE IF EXISTS consult_e2e_test;"
		@echo "Restoring original .env..."
		@mv .env.backup .env
		@echo "Removing docker-compose override..."
		@rm -f docker-compose.override.yml


.PHONY: check-python-code
check-python-code: ## Check Python code - linting and mypy
	cd backend && uv run ruff check --select I .
	cd backend && uv run ruff check .
	# Re-add mypy here and remove from pre-commit once errors fixed
	# cd backend && uv run mypy . --ignore-missing-imports

.PHONY: format-python-code
format-python-code: ## Format Python code including sorting imports
	cd backend && uv run ruff check --select I . --fix
	cd backend && uv run ruff check . --fix
	cd backend && uv run ruff format .

.PHONY: dummy_data
dummy_data: ## Generate dummy consultations. Only works in dev
	cd backend && PYTHONPATH=.. uv run python manage.py generate_dummy_data

.PHONY: dev_admin_user
dev_admin_user:
	cd backend && PYTHONPATH=.. uv run python manage.py shell -c "from authentication.models import User; from consultations.models import Consultation; user = User.objects.create_user(email='email@example.com', password='admin', is_staff=True); user.save(); [c.users.add(user) for c in Consultation.objects.all()]" # pragma: allowlist secret

.PHONY: dev_environment
dev_environment: reset_db migrate dummy_data dev_admin_user ## set up the database with dummy data

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
