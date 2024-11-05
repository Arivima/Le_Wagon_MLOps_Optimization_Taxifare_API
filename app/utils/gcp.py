import os
import json
# from tensorflow import keras
from google.cloud import storage
from app.logging import logger
from app.config import Config
from mlflow import spark


def load_model_metadata_from_gcs():
    """
    Load model metadata (coefficients and intercept) from GCS.

    Parameters:
    - date (str): Date identifier for loading the correct metadata file.
    - processed_uri_prefix (str): GCS URI prefix where the metadata is stored.

    Returns:
    - dict: Dictionary with 'coefficients' and 'intercept'.
    """
    print("----load_model_metadata_from_gcs")
    client = storage.Client()
    # print('client.name', client.pr)
    processed_uri_prefix =  f"gs://{Config.GCS_BUCKET_NAME}/processed/taxi_data/lr_model_yellow_tripdata_"
    print('processed_uri_prefix', processed_uri_prefix)
    bucket = client.bucket(Config.GCS_BUCKET_NAME)
    print('bucket', bucket.name)

    prefix_path = "/".join(processed_uri_prefix.split("/")[3:])  # Get path after bucket name
    print('prefix_path', prefix_path)
    blobs = list(bucket.list_blobs(prefix=prefix_path))
    print('blobs', len(blobs))
    [print(b) for b in blobs]
    if not blobs:
        logger.error("No metadata files found in the specified GCS path.")
        raise FileNotFoundError("No metadata files found in the specified GCS path.")
    # Find the oldest blob by sorting by 'updated' timestamp in ascending order
    oldest_blob = min(blobs, key=lambda x: x.updated)
    print('oldest_blob', oldest_blob.name)

    blob_path =  f"gs://{Config.GCS_BUCKET_NAME}/{oldest_blob.name}"
    print(blob_path)
    model = spark.load_model(blob_path)

    # Download metadata JSON content
    metadata_content = oldest_blob.download_as_text()
    model_metadata = json.loads(metadata_content)

    logger.info("Model metadata loaded successfully from GCS.")
    return model_metadata


# def load_model(stage="Production") -> keras.Model:
#     """
#     Return a saved model:
#     - or from GCS (most recent one) if MODEL_TARGET=='gcs'
#     Return None (but do not Raise) if no model is found
#     """
#     logger.info("Loading model from gcs")

#     client = storage.Client()
#     prefix = 'processes/taxi_data/lr_model'
#     blobs = list(client.get_bucket(BUCKET_NAME).list_blobs(prefix=prefix))

#     try:
#         latest_blob = max(blobs, key=lambda x: x.updated)
#         latest_model_path_to_save = os.path.join(LOCAL_REGISTRY_PATH, latest_blob.name)
#         latest_blob.download_to_filename(latest_model_path_to_save)

#         latest_model = keras.models.load_model(latest_model_path_to_save)

#         logger.info("✅Model loaded successfully.")
#         return latest_model

#     except Exception as e:
#         logger.exception("❌ No model found in GCS bucket {BUCKET_NAME}")
#         raise
