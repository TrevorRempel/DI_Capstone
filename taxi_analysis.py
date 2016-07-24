import pandas as pd
import numpy as np
import datetime
from collections import defaultdict
import pickle




def select_values(df,year, month, day , time):
    '''
    Inputs
    ------
        df:      Dataframe with multi index structure (year, month, day, time)
        year:    array of desired years
        month:   array of months
        day:     array of desired weekdays
        time:    array of desired times
        ALL the above time values will default to the total range of the data frame
    Returns
    -------
        df_slice:  Sliced version of original data frame corresponding to the year, month, day and time inputed. 
    '''
    idx = pd.IndexSlice
    return df.loc[idx[year,month,day,time]]

def select_year(df, year):
    yearD, month, day, time = df.index.levels
    return select_values (df,year, month,day, time)
def select_month(df, month):
    year,monthD, day, time = df.index.levels
    return select_values (df, year, month, day, time)
def select_day(df, day):
    year, month, dayD, time = df.index.levels
    return select_values(df, year, month, day , time)
def select_time(df, time):
    year, month, day, timeD = df.index.levels
    return select_values(df, year, month, day, time)

def process_lat_lng(df):
    idx = pd.IndexSlice
    lat = df.loc[:,idx[:,"Lat"]].values.flatten()
    lng = df.loc[:,idx[:,"Long"]].values.flatten()
    #Drop of the nan and convert to string
    lat_noNAN = map(str, list(lat[np.isfinite(lat)]))
    lng_noNAN = map(str, list(lng[np.isfinite(lng)]))
    assert len(lat_noNAN) == len(lng_noNAN)
    return (lat_noNAN,lng_noNAN)




