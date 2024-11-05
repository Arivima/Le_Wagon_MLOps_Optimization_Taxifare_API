# Makefile
PROJECT_ID='taxifare-opt'
REGION='europe-west1'
PACKAGE_NAME='taxifare-opt'
ARTIFACT_REPO_NAME='taxifare'
IMAGE_NAME='$(REGION)-docker.pkg.dev/$(PROJECT_ID)/$(ARTIFACT_REPO_NAME)/$(PACKAGE_NAME)'
CLOUD_RUN_CPU=2

# Local Development Server (Development Mode)
local_start_dev:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Local Production Server Simulation
local_start_prod:
	poetry run gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

# Docker Build and Run for Local Testing
local_docker_build:
	docker build -t $(PACKAGE_NAME) .

local_docker_run:
	docker run -p 8000:8000 $(PACKAGE_NAME)


# Production - Cloud Deployment Targets

# Create Artifact Repository for Docker Images
create_artifact_repo:
	gcloud artifacts repositories describe $(ARTIFACT_REPO_NAME) --location=$(REGION) || \
	gcloud artifacts repositories create $(ARTIFACT_REPO_NAME) \
		--repository-format=docker \
		--location=$(REGION) \
		--description="Docker repository for FastAPI app"

# Prerequisites: Authentication and Service Enabling
# Run the following once before deploying:
# gcloud auth login
# gcloud config set project $(PROJECT_ID)
# gcloud services enable run.googleapis.com
# gcloud services enable artifactregistry.googleapis.com

# Authenticate Docker with GCP Artifact Registry
authenticate_docker_to_artifact:
	gcloud auth configure-docker $(REGION)-docker.pkg.dev

# Build Docker Image for Cloud Run Deployment
cloud_docker_build:
	docker build -t $(IMAGE_NAME) .

# Push Docker Image to Artifact Registry
cloud_docker_push:
	docker push $(IMAGE_NAME)

# Deploy Application to Google Cloud Run
cloud_cloud_run:
	gcloud run deploy $(PACKAGE_NAME) \
		--image $(IMAGE_NAME) \
		--platform managed \
		--region $(REGION) \
		--allow-unauthenticated \
		--cpu $(CLOUD_RUN_CPU) \
		--memory 1Gi \
		--max-instances 10 \
		--concurrency 80

# Check Deployment Status
check_deployment:
	gcloud run services describe $(PACKAGE_NAME) --region $(REGION)
