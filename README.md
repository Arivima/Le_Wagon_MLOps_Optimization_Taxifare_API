# Le Wagon - MLOps Optimization : Taxifare API
# FastAPI Project

A FastAPI-based RESTful API for predicting taxi fares using a trained machine learning model. This project is designed to be deployed on **Google Cloud Run** using **Docker** and **Poetry** for dependency management.

### Key README Sections

- **Overview**: Project purpose and features.
- **Setup**: Installation, local setup, and testing.
- **Docker Usage**: Details on building and running the Docker container locally.
- **Google Cloud Deployment**: Provides a step-by-step guide for deploying to Google Cloud Run.
- **Makefile Commands**: Lists available `make` targets for local and cloud operations.
- **License** and **Contact**: Legal and contact information.

## Overview
### Project Structure

. ├── app
│ ├── api
│ │ ├── endpoints.py # Main API endpoints
│ │ ├── fast.py # Additional utility
│ │ └── init.py
│ ├── config.py # Configuration settings
│ ├── gcp.py # Google Cloud utilities
│ ├── main.py # FastAPI application entry point
│ └── preprocess.py # Preprocessing utility for predictions
├── Dockerfile # Dockerfile for containerizing the app
├── LICENSE # Project license
├── Makefile # Makefile with helpful commands
├── pyproject.toml # Poetry configuration file
├── README.md # Project documentation
└── tests
├── init.py
└── test_endpoints.py # Unit tests for API endpoints

### Features

- **Taxi Fare Prediction**: Predicts taxi fares based on inputs like pickup location, dropoff location, and time.
- **FastAPI Framework**: High-performance, easy-to-use API with automatic documentation.
- **Deployment-Ready**: Configured for production deployment on Google Cloud Run with Docker.

## Set-up
### Prerequisites

- **Python 3.9+**
- **Docker**
- **Google Cloud SDK** (for deployment)
- **Poetry** (for dependency management)

### Installation

1. **Clone the Repository**:

```
git clone https://github.com/your-username/taxifare-fastapi.git
cd taxifare-fastapi
```

2. Install Dependencies:

Use Poetry to install the dependencies in a virtual environment:

```
poetry install
```

3. Run the API Locally:

For development:

```
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

For production simulation:

```
poetry run gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

4. Access the API:

- Open http://127.0.0.1:8000 to view the root endpoint.
- View API documentation:
  - Swagger UI: http://127.0.0.1:8000/docs
  - ReDoc: http://127.0.0.1:8000/redoc

### Testing
Run unit tests using `pytest` (you may need to add `pytest` as a dev dependency with `poetry add --dev pytest`):

```poetry run pytest```

## Docker Usage
### Build and Run Locally with Docker
1. Build the Docker Image:

```docker build -t taxifare-opt . ```

2. Run the Docker Container:

```docker run -p 8000:8000 taxifare-opt```

## Google Cloud Deployment
This project is designed to be deployed on Google Cloud Run using Google Artifact Registry to store Docker images.

### Steps to Deploy
1. Set Up Google Cloud (only needed once per project):

```
gcloud auth login
gcloud config set project taxifare-opt
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

2. Create the Artifact Repository:

```
make create_artifact_repo
```

3. Authenticate Docker to Artifact Registry:

```
make authenticate_docker_to_artifact
```

4. Build and Push Docker Image to Artifact Registry:

```
make cloud_docker_build
make cloud_docker_push
```

5. Deploy to Cloud Run:

```
make cloud_cloud_run
```

6. Verify Deployment:

```
make check_deployment
```

After deployment, Cloud Run will provide a URL where the API can be accessed.

## Makefile Commands

The project includes a Makefile with useful commands for local development, Docker usage, and Google Cloud deployment:

- `local_start_dev`: Start the API locally in development mode with Uvicorn.
- `local_start_prod`: Start the API locally in production mode with Gunicorn and Uvicorn workers.
- `local_docker_build`: Build the Docker image locally.
- `local_docker_run`: Run the Docker container locally.
- `create_artifact_repo`: Create an Artifact Registry for storing Docker images.
- `authenticate_docker_to_artifact`: Authenticate Docker with Google Artifact Registry.
- `cloud_docker_build`: Build the Docker image for cloud deployment.
- `cloud_docker_push`: Push the Docker image to Artifact Registry.
- `cloud_cloud_run`: Deploy the Docker image to Cloud Run.
- `check_deployment`: Check the status of the Cloud Run deployment.

## License
This project is licensed under the MIT License.
