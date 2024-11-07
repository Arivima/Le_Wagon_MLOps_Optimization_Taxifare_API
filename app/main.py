# app/main.py
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.logging import logger
from app.utils.gcp import load_model_metadata_from_gcs

from contextlib import asynccontextmanager
import pandas as pd


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up taxifare API application...")
    yield  # Control passed to the application
    logger.info("Shutting down taxifare API application...")

app = FastAPI(lifespan=lifespan)
logger.info("FastApi() loaded")

app.state.model = load_model_metadata_from_gcs()
logger.info("Model loaded : %s", app.state.model is not None)
logger.info(app.state.model)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    logger.info("Endpoint : /root")
    return {"status": "ok"}

@app.get("/model_reload")
async def root():
    logger.info("Endpoint : /model_reload")
    app.state.model = load_model_metadata_from_gcs()
    if app.state.model is None:
        logger.error("model could not reload")
        return {"status": "Error 500 - model could not reload"}
    logger.info("Model loaded : %s", app.state.model is not None)
    logger.info(app.state.model)
    return {"status": "reloaded"}



# Example request:
# http://127.0.0.1:8000/predict?pickup_datetime=2014-07-06+19:18:00
# &pickup_longitude=-73.950655&pickup_latitude=40.783282
# &dropoff_longitude=-73.984365&dropoff_latitude=40.769802
# &passenger_count=2
@app.get("/predict")
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
    logger.info("Endpoint : /predict")
    logger.info("Received request for fare prediction with parameters: %s", {
        "pickup_datetime": pickup_datetime, "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude, "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude, "passenger_count": passenger_count
    })

    try:
        X_pred = pd.DataFrame({
            "pickup_datetime": [pickup_datetime],
            "pickup_longitude": [pickup_longitude],
            "pickup_latitude": [pickup_latitude],
            "dropoff_longitude": [dropoff_longitude],
            "dropoff_latitude": [dropoff_latitude],
            "passenger_count": [passenger_count]
        })
        logger.info(X_pred.loc[0])

        if not app.state.model:
            logger.info("Empty app.state.model, loading the model...")
            app.state.model = load_model_metadata_from_gcs()
        model = app.state.model
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")
        logger.info("Model loaded.")

        logger.info(model)
        coefficients = model["weights"]
        intercept = model["intercept"]

    except Exception as e:
        logger.error("Error: %s", str(e))
        return {"fare": 0}

    # Prepare feature vector in the same order as during training
    feature_vector = [
        X_pred['pickup_longitude'],
        X_pred['pickup_latitude'],
        X_pred['dropoff_longitude'],
        X_pred['dropoff_latitude'],
        X_pred['passenger_count']
    ]

    # Calculate the prediction using linear regression formula
    y_pred = intercept + sum(c * f for c, f in zip(coefficients, feature_vector))

    logger.info("Prediction : %f", y_pred)

    return {"fare": y_pred}
