import pandas as pd
import os
from shapely.geometry import Point
import numpy as np
import geopandas as gpd
from scipy.spatial import distance_matrix
from geopandas import GeoDataFrame
from typing import Literal
import logging
import inspect

gdf = gpd.read_file("./data/ayodhya.json")
logger = logging.getLogger(__name__)
current_file = inspect.getfile(inspect.currentframe())


def make_map(start_date: str, end_date: str, param: Literal["temp", "aqi", "rainfall"]):
    current_function = inspect.currentframe().f_code.co_name
    filename = "./data/AQI_Temp_2024-01-08_2024-05-30_data.csv"
    col = ""

    match param:
        case "temp":
            col = "Temperature"
        case "aqi":
            col = "AQI"
        case "rainfall":
            return {"Hello": "World"}
        case _:  # default
            return {
                "Error": "Invalid parameter value, it should be one of 'temp', 'aqi', 'rainfall'."
            }

    if not os.path.exists(filename):
        logger.error(
            f"Error in file: {current_file}, function: {current_function}, line: {inspect.currentframe().f_lineno} - Could not find specified data for the period mentioned"
        )
        return {"Error": "Could not find specified data for the period mentioned"}

    try:
        sensor_gdf = sensor_gdf_util(start_date, end_date, col, filename)
    except Exception:
        logger.error(
            f"Error in file: {current_file}, function: {current_function}, line: {inspect.currentframe().f_lineno} - Could not convert sensor data to GeoDataFrame"
        )
        return {"Error": "Something went wrong, please try again later"}

    return idw(gdf, sensor_gdf, col)


def sensor_gdf_util(start_date: str, end_date: str, param: str, filename: str):
    # Read DataFrame from specified file path
    try:
        df = pd.read_csv(filename)
    except FileNotFoundError:
        return {"Error": "Could not find specified data for the period mentioned"}

    # Filter the DataFrame based on the start and end date
    df["time"] = pd.to_datetime(df["time"])
    df = df[(df["time"] >= start_date) & (df["time"] <= end_date)]

    # Group the data by Latitude, Longitude and Location and calculate the mean of the parameter

    sensor_data = (
        df.groupby(["Latitude", "Longitude", "Location"])[param]
        .mean()
        .round()
        .reset_index()
    )

    # Create a GeoDataFrame from the sensor data

    geometry = [Point(xy) for xy in zip(sensor_data.Longitude, sensor_data.Latitude)]
    sensor_gdf = gpd.GeoDataFrame(sensor_data, geometry=geometry)
    return sensor_gdf


# Function for Inverse Distance Weighting (IDW) interpolation, add latitude and longitude of centroid to each polygon as well


def idw(gdf: GeoDataFrame, sensor_gdf: GeoDataFrame, param: str, power: int = 2):
    # Create an empty column for the interpolated temperatures
    current_function = inspect.currentframe().f_code.co_name
    gdf[param] = np.nan
    gdf["latitude"] = gdf.geometry.centroid.y
    gdf["longitude"] = gdf.geometry.centroid.x

    # Extract centroids of each MultiPolygon
    try:
        centroids = gdf.geometry.centroid.apply(lambda geom: (geom.x, geom.y))

        # Extract sensor points

        sensor_points = np.array([(geom.x, geom.y) for geom in sensor_gdf.geometry])

        sensor_temps = sensor_gdf[param].values

        for i, centroid in enumerate(centroids):
            dist = distance_matrix([centroid], sensor_points)[0]

            weights = 1 / (dist**power)

            weights /= weights.sum()

            gdf.at[i, param] = np.dot(weights, sensor_temps).round(1)

        # return gdf as geojson object
        return gdf
    except Exception:
        logger.error(
            f"Error in file: {current_file}, function: {current_function}, line: {inspect.currentframe().f_lineno} - Error in IDW interpolation"
        )
        return {"Error": "Something went wrong, please try again later"}
