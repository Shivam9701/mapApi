from fastapi import FastAPI
import uvicorn
from utils import make_map
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware
import os

# Create the app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/map",
    tags=["Get Map"],
)
def read_root(
    start_date: str = "2024-01-08",
    end_date: str = "2024-02-28",
    param: Literal["aqi", "temp", "rainfall"] = "temp",
):
    """
    **Get Map for one of [AQI | Temp | Rainfall]**
    ### IMP : DATES MUST BE BETWEEN 08-01-2024 and 31-05-2024

    Args:
    - start_date : str : "2024-01-08"
    - end_date : str : "2024-02-28"
    - param : Literal["aqi", "temp", "rainfall"] : "temp"

    Raises:
    - ValueError : If start_date or end_date is not in the required format or not in the required range or param is not one of [aqi, temp, rainfall]

    Returns:
    - GeoJSON : GeoJSON object
    """

    # Get The Interpolated GeoDataFrame

    map_gdf = make_map(start_date, end_date, param)
    # Convert the GeoDataFrame to GeoJSON
    map_json = map_gdf.__geo_interface__
    return map_json


if __name__ == "__main__":
    uvicorn.run(
        "index:app", host="127.0.0.1", port=int(os.getenv("PORT", 8000)), reload=True
    )
