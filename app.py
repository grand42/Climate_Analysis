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
    precip_data = []
    for date, prcp in Data:
        if prcp != None:
            prcp_dict={}
            prcp_dict[date] = prcp
            precip_data.append(prcp_dict)
    #Return JSON
    return jsonify(precip_data)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations"""
    session = Session(engine)
    station_list = session.query(Stations.station, Stations.name, Stations.latitude, Stations.longitude, Stations.elevation).all()
    session.close()
    # Convert results into a dictionary
    all_stations = []
    for station, name, latitude, longitude, elevation in station_list:
        station_dict = {}
        station_dict['station'] = station
        station_dict['name']=name
        station_dict['latitude'] = latitude
        station_dict['longitude'] = longitude
        station_dict['elevation'] = elevation
        all_stations.append(station_dict)

    # Return a JSON list of stations from the dataset.
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most active station for the last year of data."""
    session = Session(engine)
    # Find most active Station
    Active_station = session.query(Measurements.station).group_by(Measurements.station).order_by(func.count().desc()).first()
    # Get ID of active station
    (station_ID,)=Active_station
    print(f"The most active station is {station_ID}.")
    # Perform Query to retieve temperature data for last year at active station
    
    #Calculate 12 months before recent point
    Active_Station_Date = session.query(Measurements.date).\
        order_by(Measurements.date.desc()).\
        filter(Measurements.station == station_ID).\
        first()
    (last_point,) = Active_Station_Date
    last_point = dt.datetime.strptime(last_point, '%Y-%m-%d')
    last_point = last_point.date()
    one_year = last_point-dt.timedelta(days=365)
    
    #Filter to grab a years worth of data
    Year_Station_Data = session.query(Measurements.date,Measurements.tobs).\
        filter(Measurements.date>=one_year).\
        filter(Measurements.station == station_ID).all()
    
    session.close()
    
    # Convert to a dictionary
    all_temperatures = []
    for date, temp in Year_Station_Data:
        if temp != None:
            tempdict = {}
            tempdict[date]=temp
            all_temperatures.append(tempdict)
    
    # Return JSON of dictionary
    return jsonify(all_temperatures)

@app.route('/api/v1.0/<start>', defaults={'end':None})
@app.route('/api/v1.0/<start>/<end>')
def temps_for_date_ranges(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range."""
    """When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates greater than and equal to the start date."""
    """When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` for dates between the start and end date inclusive."""
    # Create session link
    session = Session(engine)

    if end != None:
        temps = session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
        filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    else:
        temps = session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.avg(Measurements.tobs)).\
        filter(Measurements.date >= start).all()

    session.close()

    # Convert temperatures to a list
    temp_stats = []
    data_available = True
    for min_temp, max_temp, avg_temp in temps:
        if min_temp == None or max_temp == None or avg_temp == None:
            data_available = False
        temp_stats.append(min_temp)
        temp_stats.append(avg_temp)
        temp_stats.append(max_temp)

    if data_available == False:
        return f"No data found for given dates.  Try another date range."
    else:
        return jsonify(temp_stats)


if __name__ == '__main__':
    app.run(debug=True)