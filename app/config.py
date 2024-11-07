# app/config.py
import os

class Config:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "")
