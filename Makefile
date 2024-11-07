# Makefile
# GCP PROJECT
GCP_PROJECT_ID='taxifare-opt'
GCS_BUCKET_NAME='bucket_imane'
REGION='europe-west1'
# DOCKER LOCAL
DOCKER_IMAGE_NAME='taxifare-opt'
TAG='latest'
PATH_SERVICE_ACCOUNT_KEY='taxifare-opt-1142853755ce.json'
DOCKER_CONTAINER_NAME='detached-tmp'
# ARTIFACT
ARTIFACT_REPO_NAME='taxifare'
ARTIFACT_REPO_LOCATION = '$(REGION)-docker.pkg.dev/$(GCP_PROJECT_ID)/$(ARTIFACT_REPO_NAME)'
ARTIFACT_IMAGE_NAME='$(ARTIFACT_REPO_LOCATION)/$(DOCKER_IMAGE_NAME)'
# CLOUD RUN
PACKAGE_NAME='taxifare-opt'
CLOUD_RUN_CPU=2

################ DEV LOCAL #################
# Local Development Server (Development Mode)
local_start_dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Local Production Server Simulation
local_start_prod:
	poetry run gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8080

# Docker Build and Run for Local Testing
local_docker_build:
	docker build --no-cache -t $(DOCKER_IMAGE_NAME) .

local_docker_run:
	docker run -p 8080:8080 \
	-e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json \
	-e GCS_BUCKET_NAME=$(GCS_BUCKET_NAME) \
	-e GCP_PROJECT_ID=$(GCP_PROJECT_ID) \
	-v $(shell pwd)/$(PATH_SERVICE_ACCOUNT_KEY):/app/service-account.json \
	$(DOCKER_IMAGE_NAME)

# to get in the container and check the file tree
local_docker_run_detached:
	docker run -d --entrypoint=/bin/bash $(DOCKER_IMAGE_NAME) -c "tail -f /dev/null"\
	-p 8080:8080 \
	-e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json \
	-e GCS_BUCKET_NAME=$(GCS_BUCKET_NAME) \
	-e GCP_PROJECT_ID=$(GCP_PROJECT_ID) \
	-v $(shell pwd)/$(PATH_SERVICE_ACCOUNT_KEY):/app/service-account.json \
	--name $(DOCKER_CONTAINER_NAME) $(DOCKER_IMAGE_NAME)
	docker exec -it $(DOCKER_CONTAINER_NAME) /bin/bash


################ PRODUCTION - CLOUD DEPLOYMENT #################

################ AUTHENTICATION AUTHORISATION #################
# Prerequisites: Authentication and Service Enabling
# Run the following once before deploying:
# check service account and project
gcloud_check_config:
	gcloud config list

# if not the right config, config with :
gcloud_set_auth:
	gcloud auth login
gcloud_set_project:
	gcloud config set project $(GCP_PROJECT_ID)

# check if the project has enabled the right services :
gcloud_check_enabled_services:
	gcloud services list --enabled --filter="NAME:run.googleapis.com"
	gcloud services list --enabled --filter="NAME:artifactregistry.googleapis.com"

# enable services idf they are not listed :
gcloud_enable_services:
	gcloud services enable run.googleapis.com
	gcloud services enable artifactregistry.googleapis.com


################ ARTIFACT #################
# Create Artifact Repository for Docker Images - if it does not exists already
create_artifact_repo:
	gcloud artifacts repositories describe $(ARTIFACT_REPO_NAME) --location=$(REGION) || \
	gcloud artifacts repositories create $(ARTIFACT_REPO_NAME) \
		--repository-format=docker \
		--location=$(REGION) \
		--description="Docker repository for taxifare FastAPI app"

gcloud_set_artifact_repo:
	gcloud config set artifacts/repository $(ARTIFACT_REPO_NAME)
	gcloud config set artifacts/location $(REGION)

# Authenticate Docker with GCP Artifact Registry - updates docker config ~/.docker/config.json to include auth creds for artifact
authenticate_docker_to_artifact:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

# rename an existing docker image so it can be pushed to artifact
make cloud_docker_rename_for_artifact:
	docker tag $(DOCKER_IMAGE_NAME):$(TAG) $(ARTIFACT_IMAGE_NAME):$(TAG)
# OR
# Build Docker Image for Cloud Run Deployment
cloud_docker_build:
	docker build --no-cache -t $(ARTIFACT_IMAGE_NAME) .

# Checks that no other image is on artifact and delete cached layers
# List repo / images / files in the artifact repo
cloud_artifact_list_repo:
	gcloud artifacts repositories list
# gcloud artifacts repositories list --location=$(REGION) --project=$(ARTIFACT_REPO_NAME)
# gcloud artifacts docker images list $(ARTIFACT_REPO_LOCATION)

cloud_artifact_list_images:
	gcloud artifacts docker images list

cloud_artifact_list_files:
	gcloud artifacts files list

# Delete the image from the artifact registry
cloud_artifact_delete_image:
	gcloud artifacts docker images delete $(ARTIFACT_IMAGE_NAME) --delete-tags

# Delete the cached layers from the artifact registry
cloud_artifact_delete_files:
	for digest in $(gcloud artifacts files list --format="value(name)")
	do
			gcloud artifacts files delete "$digest" --quiet
	done

# Push Docker Image to Artifact Registry
cloud_docker_push_to_artifact:
	docker push $(ARTIFACT_IMAGE_NAME)


################ CLOUD RUN #################

# Deploy Application to Google Cloud Run
cloud_run:
	gcloud run deploy $(PACKAGE_NAME) \
		--image $(ARTIFACT_IMAGE_NAME) \
		--platform managed \
		--region $(REGION) \
		--allow-unauthenticated \
		--cpu $(CLOUD_RUN_CPU) \
		--memory 1Gi \
		--max-instances 10 \
		--concurrency 80 \
		--set-env-vars "GCS_BUCKET_NAME=$(GCS_BUCKET_NAME),GCP_PROJECT_ID=$(GCP_PROJECT_ID)"


# Set-up IAM to allow cloud run to access bucket
# Info : how to retrieve Project Number
cloud_run_get_project_number:
	gcloud projects describe $(GCP_PROJECT_ID) --format="value(projectNumber)"

# Retrieve project number and Attribute the correct permission for the cloud run service account
cloud_run_set_permissions:
	@echo "Adding Storage Object Viewer role to Cloud Run service account"
	gcloud projects add-iam-policy-binding $(GCP_PROJECT_ID) \
	    --member="serviceAccount:$(shell gcloud projects describe $(GCP_PROJECT_ID) --format="value(projectNumber)")-compute@developer.gserviceaccount.com" \
	    --role="roles/storage.objectViewer"

# Check Deployment Status
check_deployment:
	gcloud run services describe $(PACKAGE_NAME) --region $(REGION)
