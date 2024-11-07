import re
import json
from google.cloud import storage
from app.logging import logger
from app.config import Config


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

        bucket_name = Config.GCS_BUCKET_NAME
        if not bucket_name:
            raise ValueError("GCS_BUCKET_NAME is not configured in Config.")

        # connection to gcs
        project_id = Config.GCP_PROJECT_ID
        if not project_id:
            raise ValueError("GCP_PROJECT_ID is not configured in Config.")
        client = storage.Client(project=project_id)
        bucket = client.bucket(bucket_name)
        logger.info('connected to bucket %s', bucket.name)

        # paths
        processed_uri_prefix = f"gs://{bucket_name}/processed/taxi_data/json_model_yellow_tripdata_"
        prefix_path = "/".join(processed_uri_prefix.split("/")[3:])
        logger.info(f'Prefix path: {prefix_path}')

        # list blobs
        blobs = list(bucket.list_blobs(prefix=prefix_path))
        logger.info(f'Number of blobs found: {len(blobs)}')
        if not blobs:
            logger.error(f"No model files found in GCS path with prefix {prefix_path}")
            return None

        # find the relevant blob
        pattern = re.compile(r"json_model_yellow_tripdata_(\d{4}-\d{2})\.json")
        model_dates = {}
        for blob in blobs:
            _match = pattern.search(blob.name)
            if _match:
                model_date = _match.group(1)
                model_dates[blob.name] = model_date
                logger.info(f"Found json for date: {model_date} -> {blob.name}")
        if not model_dates:
            logger.error(f"No json files found in GCS path with prefix {prefix_path}")
            return None

        # select json from the latest month
        [logger.info(k) for k in model_dates.keys()]
        latest_model_name = max(model_dates, key=model_dates.get)

        # download json
        logger.info(f"Attempting to load json from: {latest_model_name}")
        blob = bucket.blob(latest_model_name)
        json_content = blob.download_as_text()
        model_params = json.loads(json_content)

        if "weights" not in model_params or "intercept" not in model_params:
            logger.error("JSON model file missing required keys: 'weights' or 'intercept'.")
            return None

        logger.info("✅ Model weights and intercept loaded successfully from GCS.")
        return model_params

    except Exception as e:
        logger.exception(f"❌ Error loading model from GCS bucket {bucket_name}: {e}")
        raise
