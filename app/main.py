# app/main.py
from fastapi import FastAPI
from app.api import endpoints
from fastapi.middleware.cors import CORSMiddleware
from app.logging import logger
from app.utils.gcp import load_model_metadata_from_gcs

app = FastAPI()

print("----fast api loaded")

app.state.model = load_model_metadata_from_gcs()

print("----model loaded", not app.state.model == None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
print("----CORSMiddleware")

# app.include_router(endpoints.router)
# print("----include_router")

@app.on_event("startup")
async def startup_event():
    print("----startup_event")
    logger.info("Starting up taxifare api application...")

@app.on_event("shutdown")
async def shutdown_event():
    print("----shutdown_event")
    logger.info("Shutting down taxifare api application...")

@app.get("/")
async def root():
    print("----root")
    return {"status": "ok"}



# TODO : refactor async load model

# app/api/endpoints.py
from fastapi import APIRouter, HTTPException
import pandas as pd

from app.utils.gcp import load_model_metadata_from_gcs
from app.utils.preprocess import preprocess_features
from app.logging import logger

router = APIRouter()

# Example request:
# http://127.0.0.1:8000/predict?
# pickup_datetime=2014-07-06+19:18:00
# &pickup_longitude=-73.950655
# &pickup_latitude=40.783282
# &dropoff_longitude=-73.984365
# &dropoff_latitude=40.769802
# &passenger_count=2


@router.get("/predict")
def predict(
        pickup_datetime: str,
        pickup_longitude: float,
        pickup_latitude: float,
        dropoff_longitude: float,
        dropoff_latitude: float,
        passenger_count: int,
    ):
    """
    Make a single fare prediction based on coefficients and intercept.
    """
    print("----predict")
    logger.info("Received request for fare prediction with parameters: %s", {
        "pickup_datetime": pickup_datetime,
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": passenger_count
    })

    try:
        # 💡 Optional trick instead of writing each column name manually:
        # locals() gets us all of our arguments back as a dictionary
        # https://docs.python.org/3/library/functions.html#locals
        X_pred = pd.DataFrame({
            "pickup_datetime": [pickup_datetime],
            "pickup_longitude": [pickup_longitude],
            "pickup_latitude": [pickup_latitude],
            "dropoff_longitude": [dropoff_longitude],
            "dropoff_latitude": [dropoff_latitude],
            "passenger_count": [passenger_count]
        })

        # Convert to US/Eastern TZ-aware!
        X_pred['pickup_datetime'] = pd.to_datetime(X_pred['pickup_datetime']).dt.tz_localize("US/Eastern")

        if not app.state.model:
            logger.info("Empty app.state.model, loading the model...")
            app.state.model = load_model_metadata_from_gcs()
        model = app.state.model
        if model is None:
            logger.error("Model not loaded.")
            raise HTTPException(status_code=500, detail="Model not loaded")
        print("----loaded model_metadata")

        coefficients = model["coefficients"]
        intercept = model["intercept"]
    except Exception as e:
        logger.error("Failed to load model metadata: %s", str(e))
        raise HTTPException(status_code=500, detail="Model metadata could not be loaded")

    X_processed = preprocess_features(X_pred)

    # Prepare feature vector in the same order as during training
    feature_vector = [
        X_processed['pickup_longitude'],
        X_processed['pickup_latitude'],
        X_processed['dropoff_longitude'],
        X_processed['dropoff_latitude'],
        X_processed['passenger_count']
    ]

    # Calculate the prediction using linear regression formula
    y_pred = intercept + sum(c * f for c, f in zip(coefficients, feature_vector))

    print("----Prediction", y_pred)
    logger.info("Prediction calculated successfully: %f", y_pred)

    return {"fare": y_pred}










# @router.get("/predict_old")
# def predict_old(
#         pickup_datetime: str,       # Example: 2014-07-06 19:18:00
#         pickup_longitude: float,    # Example: -73.950655
#         pickup_latitude: float,     # Example: 40.783282
#         dropoff_longitude: float,   # Example: -73.984365
#         dropoff_latitude: float,    # Example: 40.769802
#         passenger_count: int        # Example: 1
#     ):
#     """
#     Make a single fare prediction.
#     `pickup_datetime` should be provided in "%Y-%m-%d %H:%M:%S" format, assuming "US/Eastern" timezone.
#     """

#     logger.info("Received request for fare prediction with parameters: %s", {
#         "pickup_datetime": pickup_datetime,
#         "pickup_longitude": pickup_longitude,
#         "pickup_latitude": pickup_latitude,
#         "dropoff_longitude": dropoff_longitude,
#         "dropoff_latitude": dropoff_latitude,
#         "passenger_count": passenger_count
#     })

#     try:
#         # 💡 Optional trick instead of writing each column name manually:
#         # locals() gets us all of our arguments back as a dictionary
#         # https://docs.python.org/3/library/functions.html#locals
#         X_pred = pd.DataFrame({
#             "pickup_datetime": [pickup_datetime],
#             "pickup_longitude": [pickup_longitude],
#             "pickup_latitude": [pickup_latitude],
#             "dropoff_longitude": [dropoff_longitude],
#             "dropoff_latitude": [dropoff_latitude],
#             "passenger_count": [passenger_count]
#         })

#         # Convert to US/Eastern TZ-aware!
#         X_pred['pickup_datetime'] = pd.to_datetime(X_pred['pickup_datetime']).dt.tz_localize("US/Eastern")

#         if not app.state.model:
#             logger.info("Empty app.state.model, loading the model...")
#             app.state.model = load_model()

#         model = app.state.model
#         if model is None:
#             logger.error("Model not loaded.")
#             raise HTTPException(status_code=500, detail="Model not loaded")

#         X_processed = preprocess_features(X_pred)
#         y_pred = model.predict(X_processed)

#         fare = float(y_pred[0])
#         logger.info("Predicted fare: %f", fare)

#         return {"fare": fare}

#     except Exception as e:
#         logger.exception("An error occurred during prediction")
#         raise HTTPException(status_code=500, detail="An internal error occurred")
