# Import Dependencies
import numpy as np
import pandas as pd
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurements = Base.classes.measurement
Stations = Base.classes.station


#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return(
        f"Welcome to the Hawaii Climate App!"
        f"Avalable Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Query to retrieve the last 12 months of precipitation data"""
    session = Session(engine)
    # Calculate the date 1 year ago from the last data point in the database
    recent_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    (last_point,) = recent_date
    last_point = dt.datetime.strptime(last_point, '%Y-%m-%d')
    last_point = last_point.date()
    one_year = last_point-dt.timedelta(days=365)
    # Perform a query to retrieve the data and precipitation scores
    Data = session.query(Measurements.date,Measurements.prcp).\
        filter(Measurements.date>=one_year).all()
    session.close()
        # Convert the query results to a dictionary using date as the key and prcp as the value.
        precip_data = {date : prcp for date, prcp in Data}
        return jsonify(precip_data)