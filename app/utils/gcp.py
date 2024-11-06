import os
import re
import json
# from tensorflow import keras
from google.cloud import storage
from app.logging import logger
from app.config import Config
import mlflow.pyfunc


def load_model_metadata_from_gcs():
    """
    Load model metadata (coefficients and intercept) from GCS.

    Parameters:
    - date (str): Date identifier for loading the correct metadata file.
    - processed_uri_prefix (str): GCS URI prefix where the metadata is stored.

    Returns:
    - dict: Dictionary with 'coefficients' and 'intercept'.
    """
    try:
        logger.info("load_model_metadata_from_gcs")

        client = storage.Client()
        bucket_name = Config.GCS_BUCKET_NAME
        bucket = client.bucket(bucket_name)
        logger.info('connected to bucket %s', bucket.name)

        processed_uri_prefix = f"gs://{bucket_name}/processed/taxi_data/lr_model_yellow_tripdata_"
        logger.info('processed_uri_prefix %s', processed_uri_prefix)

        prefix_path = "/".join(processed_uri_prefix.split("/")[3:])
        logger.info(f'Prefix path: {prefix_path}')

        blobs = list(bucket.list_blobs(prefix=prefix_path))
        logger.info(f'Number of blobs found: {len(blobs)}')
        if not blobs:
            raise FileNotFoundError(f"No model files found in GCS path with prefix {prefix_path}")

        pattern = re.compile(r"lr_model_yellow_tripdata_(\d{4}-\d{2})")
        model_dates = {}
        for blob in blobs:
            match = pattern.search(blob.name)
            if match:
                model_date = match.group(1)
                model_dates[blob.name] = model_date
                logger.info(f"Found model for date: {model_date} -> {blob.name}")
        if not model_dates:
            raise FileNotFoundError(f"No valid model folders found in path '{prefix_path}'")


        # Find the latest model folder by checking the 'updated' timestamp
        [logger.info(k) for k in model_dates.keys()]
        latest_model_name = max(model_dates, key=model_dates.get)
        latest_folder_path = "/".join(latest_model_name.split("/")[:3])  # Get folder path up to date part
        logger.info(f'Latest model folder name: {latest_model_name}')
        logger.info(f'Latest model folder path: {latest_folder_path}')

        # Load the model using MLflow's Spark flavor
        gcs_model_uri = f"gs://{bucket_name}/{latest_folder_path}"
        logger.info(f"Attempting to load model from: {gcs_model_uri}")
        model = mlflow.pyfunc.load_model(model_uri=gcs_model_uri)

        logger.info("✅ Model loaded successfully from GCS.")
        return model
    except Exception as e:
        logger.exception(f"❌ Error loading model from GCS bucket {bucket_name}: {e}")
        raise
