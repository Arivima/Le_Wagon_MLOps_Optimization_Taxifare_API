# app/config.py
import os

class Config:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Taxifare Opts")
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "taxifare-opt")
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "bucket_imane")
