# Taxifare API

This FastAPI application provides taxi fare predictions based on ride parameters. The application uses a machine learning model stored in Google Cloud Storage (GCS) and can be deployed both locally and on Google Cloud Run.

## README Sections
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Makefile Commands](#makefile-commands)
- [Environment Setup](#environment-setup)
- [Quickstart Local Development](#quickstart-local-development)
- [Production Deployment to Cloud Run](#production-deployment)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Testing and Logging](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **FastAPI Framework**: High-performance, easy-to-use API with automatic documentation.
- **Prediction endpoint**: Predicts taxi fares based on inputs like pickup location, dropoff location, and time.
- **Deployment-Ready**: Configured for production deployment on Google Cloud Run with Docker.

## Prerequisites

- Python 3.8 or higher
- Poetry
- Docker
- Google Cloud SDK (includes gcloud CLI) - needs separate installation from https://cloud.google.com/sdk/docs/install
  - Required for deployment commands, not for local development
- A Google Cloud Project
  We will enable the following services:
  - Cloud Run
  - Artifact Registry
- GCP service account key which needs to include the following IAM roles:
  1. Google Cloud Storage:
     - `roles/storage.objectViewer`
  2. Artifact Registry:
     - `roles/artifactregistry.repoAdmin`
  3. Cloud Run:
     - `roles/run.admin`
     - `roles/iam.serviceAccountUser`

## Makefile Commands

The project includes a `Makefile` with useful commands for local development, Docker usage, and Google Cloud deployment.

The commands mentioned in this README are part of the Makefile. Refer to the Makefile to see the full list of commands and additional options to support your development and deployment workflow.

## Environment Setup

1. Clone the repository
```
git clone https://github.com/Arivima/taxifare-fastapi.git
cd taxifare-fastapi
```
2. Place your GCP service account key JSON file in the root directory

3. Environment variables

Create a `.env` file in the root directory from the `.env.sample`

```bash
cp .env.sample .env
```
Modify the variables to fit your GCP project and cloud storage bucket
```env
# GCP PROJECT
GCP_PROJECT_ID="your-gcp-project-id"
GCS_BUCKET_NAME="your-gcs-bucket-name"
REGION="region"

# DOCKER LOCAL
DOCKER_IMAGE_NAME="your-docker-image-name"
PATH_SERVICE_ACCOUNT_KEY="path-to-your-service-account-key.json"

# ARTIFACT
ARTIFACT_REPO_NAME="your-artifact-repo-name"

# CLOUD RUN
PACKAGE_NAME="your-package-name"
```

Note on Environment Variables:
This project requires sensitive configuration details (like GCP credentials) stored in a `.env` file and necessary to interact with GCP. The environment variables are loaded automatically using `python-dotenv` (which is installed automatically by `poetry`). This setup ensures that configuration data remains secure and manageable.


## Quickstart Local Development

### Install Dependencies

```bash
poetry install
```

### Run Development Server

```bash
make local_start_dev
```
This starts the server in development mode with hot reload at `http://localhost:8080`


### Run Production Server Locally

```bash
make local_start_prod
```
This simulates the production environment using Gunicorn.

### Access the API:

- Open http://127.0.0.1:8080 to view the root endpoint.
- View API documentation:
  - Swagger UI: http://127.0.0.1:8080/docs
  - ReDoc: http://127.0.0.1:8080/redoc

### Docker Local Testing

1. Build the Docker image:
```bash
make local_docker_build
```
2. Run the container:
```bash
make local_docker_run
```
This runs the container using the service account key

To inspect the container:
```bash
make local_docker_run_detached
```

## Production Deployment

### 1. GCP Setup

Check GCP settings:
```bash
make gcloud_check_config
```
Configure GCP settings:
```bash
make gcloud_set_auth
make gcloud_set_project
```
Check if required services are enabled
```bash
make gcloud_check_enabled_services
```
Enable required services:
```bash
make gcloud_enable_services
```

### 2. Artifact Registry Setup

Create repository (will check if it does not exists already)
```bash
make create_artifact_repo
```
Configure authentication
```bash
make gcloud_set_artifact_repo
make authenticate_docker_to_artifact
```

### 3. Build and Push Docker Image

If there is an existing docker image, rename it for cloud
```bash
make cloud_docker_rename_for_artifact
```
or build from scratch for cloud
```bash
make cloud_docker_build
```
Then, push to Artifact Registry
```bash
make cloud_docker_push_to_artifact
```
for debug => Listing and deleting images in Artifact :
```bash
# List repo / images / files in the artifact repo
cloud_artifact_list_repo
cloud_artifact_list_images
cloud_artifact_list_files
# Delete the image from the artifact registry
cloud_artifact_delete_image
# Delete the cached layers from the artifact registry
cloud_artifact_delete_files
```

### 4. Deploy to Cloud Run

Deploy the application, includes the env variables
```bash
make cloud_run
```
Set up IAM permissions
```bash
make cloud_run_set_permissions
```

### 5. Verify Deployment

```bash
make check_deployment
```

## API Endpoints

### Root Endpoint
- GET `/`: Health check endpoint
- Response: `{"status": "ok"}`

### Model Reload
This endpoint was set-up to force-reload the model before the demo day to prevent latency
- GET `/model_reload`: Reloads the model from GCS
- Response: `{"status": "reloaded"}` or error message

### Prediction Endpoint
- GET `/predict`: Get fare prediction
- Parameters:
  - `pickup_datetime`: string (format: "YYYY-MM-DD HH:MM:SS")
  - `pickup_longitude`: float
  - `pickup_latitude`: float
  - `dropoff_longitude`: float
  - `dropoff_latitude`: float
  - `passenger_count`: integer
- Response: `{"fare": float}`

Example request:
```
http://localhost:8080/predict?pickup_datetime=2014-07-06 19:18:00&pickup_longitude=-73.950655&pickup_latitude=40.783282&dropoff_longitude=-73.984365&dropoff_latitude=40.769802&passenger_count=2
```

## Project Structure
```
.
├── app/
│   ├── config.py         # Configuration settings
│   ├── logging.py        # Logging configuration
│   ├── main.py           # FastAPI application
│   └── utils/
│       └── gcp.py        # GCP utilities
├── tests/                # Test files
├── .dockerignore         # Files to ignore from docker image
├── .env                  # your env variables to set-up
├── .env.sample           # .env template with placeholder values
├── Dockerfile            # Docker configuration
├── Makefile              # Development and deployment commands
├── pyproject.toml        # Project dependencies
├── README.md
└── service-account-key.json # your gcp project service account key to copy
```

## Development

### Running Tests

```bash
poetry run pytest
```

### Logging

The application logs are written to:
- Console output
- `app.log` file

## Troubleshooting

1. If the model fails to load, check:
   - GCP credentials are properly set
   - Bucket permissions are correct
   - Model file exists in the specified GCS path

2. For deployment issues:
   - Verify GCP service account permissions
   - Check Cloud Run logs for detailed error messages
   - Ensure all required environment variables are set

## License

This project is licensed under the MIT License - see the LICENSE file for details.
