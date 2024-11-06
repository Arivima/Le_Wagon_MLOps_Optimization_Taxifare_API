# from colorama import Fore, Style

from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer, make_column_transformer
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer

from app.logging import logger

import numpy as np
import pandas as pd
import math
import pygeohash as gh
import time
import tracemalloc

def simple_time_and_memory_tracker(method):

    # ### Log Level
    # 0: Nothing
    # 1: print Time and Memory usage of functions
    LOG_LEVEL = 1

    def method_with_trackers(*args, **kw):
        ts = time.time()
        tracemalloc.start()
        result = method(*args, **kw)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        te = time.time()
        duration = te - ts
        if LOG_LEVEL > 0:
            output = f"{method.__qualname__} executed in {round(duration, 2)} seconds, using up to {round(peak / 1024**2,2)}MB of RAM"
            logger.info(output)
        return result

    return method_with_trackers


def preprocess_features(X: pd.DataFrame) -> np.ndarray:
    def create_sklearn_preprocessor() -> ColumnTransformer:
        """
        Scikit-learn pipeline that transforms a cleaned dataset of shape (_, 7)
        into a preprocessed one of fixed shape (_, 65).

        Stateless operation: "fit_transform()" equals "transform()".
        """

        # PASSENGER PIPE
        p_min = 1
        p_max = 8
        passenger_pipe = FunctionTransformer(lambda p: (p - p_min) / (p_max - p_min))

        # DISTANCE PIPE
        dist_min = 0
        dist_max = 100

        distance_pipe = make_pipeline(
            FunctionTransformer(transform_lonlat_features),
            FunctionTransformer(lambda dist: (dist - dist_min) / (dist_max - dist_min))
        )

        # TIME PIPE
        timedelta_min = 0
        timedelta_max = 2090

        time_categories = [
            np.arange(0, 7, 1),  # days of the week
            np.arange(1, 13, 1)  # months of the year
        ]

        time_pipe = make_pipeline(
            FunctionTransformer(transform_time_features),
            make_column_transformer(
                (OneHotEncoder(
                    categories=time_categories,
                    sparse_output=False,
                    handle_unknown="ignore"
                ), [2,3]), # corresponds to columns ["day of week", "month"], not the other columns

                (FunctionTransformer(lambda year: (year - timedelta_min) / (timedelta_max - timedelta_min)), [4]), # min-max scale the columns 4 ["timedelta"]
                remainder="passthrough" # keep hour_sin and hour_cos
            )
        )

        # GEOHASH PIPE
        lonlat_features = [
            "pickup_latitude", "pickup_longitude", "dropoff_latitude",
            "dropoff_longitude"
        ]

        # Below are the 20 most frequent district geohashes of precision 5,
        # covering about 99% of all dropoff/pickup locations,
        # according to prior analysis in a separate notebook
        most_important_geohash_districts = [
            "dr5ru", "dr5rs", "dr5rv", "dr72h", "dr72j", "dr5re", "dr5rk",
            "dr5rz", "dr5ry", "dr5rt", "dr5rg", "dr5x1", "dr5x0", "dr72m",
            "dr5rm", "dr5rx", "dr5x2", "dr5rw", "dr5rh", "dr5x8"
        ]

        geohash_categories = [
            most_important_geohash_districts,  # pickup district list
            most_important_geohash_districts  # dropoff district list
        ]

        geohash_pipe = make_pipeline(
            FunctionTransformer(compute_geohash),
            OneHotEncoder(
                categories=geohash_categories,
                handle_unknown="ignore",
                sparse_output=False
            )
        )

        # COMBINED PREPROCESSOR
        final_preprocessor = ColumnTransformer(
            [
                ("passenger_scaler", passenger_pipe, ["passenger_count"]),
                ("time_preproc", time_pipe, ["pickup_datetime"]),
                ("dist_preproc", distance_pipe, lonlat_features),
                ("geohash", geohash_pipe, lonlat_features),
            ],
            n_jobs=-1,
        )

        return final_preprocessor

    logger.info("----Preprocessing")
    logger.info("Preprocessing features...")

    preprocessor = create_sklearn_preprocessor()
    X_processed = preprocessor.fit_transform(X)

    logger.info("✅ X_processed, with shape", X_processed.shape)
    logger.info("----Preprocessed")

    return X_processed



def transform_time_features(X: pd.DataFrame) -> np.ndarray:
    assert isinstance(X, pd.DataFrame)

    timedelta = (X["pickup_datetime"] - pd.Timestamp('2009-01-01T00:00:00', tz='UTC')) / pd.Timedelta(1,'D')

    pickup_dt = X["pickup_datetime"].dt.tz_convert("America/New_York").dt
    dow = pickup_dt.weekday
    hour = pickup_dt.hour
    month = pickup_dt.month

    hour_sin = np.sin(2 * math.pi / 24 * hour)
    hour_cos = np.cos(2*math.pi / 24 * hour)

    return np.stack([hour_sin, hour_cos, dow, month, timedelta], axis=1)


def transform_lonlat_features(X: pd.DataFrame) -> pd.DataFrame:
    assert isinstance(X, pd.DataFrame)
    lonlat_features = ["pickup_latitude", "pickup_longitude", "dropoff_latitude", "dropoff_longitude"]

    def distances_vectorized(df: pd.DataFrame, start_lat: str, start_lon: str, end_lat: str, end_lon: str) -> dict:
        """
        Calculate the haversine and Manhattan distances between two
        points on the earth (specified in decimal degrees)
        Vectorized version for pandas df
        Computes distance in km
        """
        earth_radius = 6371

        lat_1_rad, lon_1_rad = np.radians(df[start_lat]), np.radians(df[start_lon])
        lat_2_rad, lon_2_rad = np.radians(df[end_lat]), np.radians(df[end_lon])

        dlon_rad = lon_2_rad - lon_1_rad
        dlat_rad = lat_2_rad - lat_1_rad

        manhattan_rad = np.abs(dlon_rad) + np.abs(dlat_rad)
        manhattan_km = manhattan_rad * earth_radius

        a = (np.sin(dlat_rad / 2.0)**2 + np.cos(lat_1_rad) * np.cos(lat_2_rad) * np.sin(dlon_rad / 2.0)**2)
        haversine_rad = 2 * np.arcsin(np.sqrt(a))
        haversine_km = haversine_rad * earth_radius

        return dict(
            haversine=haversine_km,
            manhattan=manhattan_km
        )

    result = pd.DataFrame(distances_vectorized(X, *lonlat_features))

    return result

def compute_geohash(X: pd.DataFrame, precision: int = 5) -> np.ndarray:
    """
    Add a geohash (ex: "dr5rx") of len "precision" = 5 by default
    corresponding to each (lon, lat) tuple, for pick-up, and drop-off
    """
    assert isinstance(X, pd.DataFrame)

    X["geohash_pickup"] = X.apply(lambda x: gh.encode(
        x.pickup_latitude,
        x.pickup_longitude,
        precision=precision
    ), axis=1)

    X["geohash_dropoff"] = X.apply(lambda x: gh.encode(
        x.dropoff_latitude,
        x.dropoff_longitude,
        precision=precision
    ), axis=1)

    return X[["geohash_pickup", "geohash_dropoff"]]
