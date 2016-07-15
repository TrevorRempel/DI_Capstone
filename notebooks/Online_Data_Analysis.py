import urllib
from bs4 import BeautifulSoup
import matplotlib
import shapefile
import pandas as pd
import re
from shapely import geometry,ops,speedups
import os
import seaborn
from collections import defaultdict
import pickle
import matplotlib.pyplot  as plt
import numpy as np
import pandas as pd
import numpy as np
import math
import shapefile
import os
import scipy as sp
import matplotlib as mpl 
import matplotlib.cm as cm 
import matplotlib.pyplot as plt 
import datetime
import seaborn as sns
from matplotlib.patches import Circle
import glob
import shapefile
from sklearn import cluster
from collections import defaultdict
import dill
import json
import utm
from collections import defaultdict
from numpy import linalg
from itertools import combinations
from shapefile_read import get_records, grid_and_bur
from taxi_manipulations import taxi_data

speedups.enable()


SPACING = 0.005/4 

COLUMNS = [u'VendorID', u'tpep_pickup_datetime', u'tpep_dropoff_datetime',
       u'passenger_count', u'trip_distance', u'pickup_longitude',
       u'pickup_latitude', u'RateCodeID', u'store_and_fwd_flag',
       u'dropoff_longitude', u'dropoff_latitude', u'payment_type',
       u'fare_amount', u'extra', u'mta_tax', u'tip_amount', u'tolls_amount',
       u'improvement_surcharge', u'total_amount', u'Pickup_Borough',
       u'Pickup_Neighbourhood', u'Pickup_Zip_code', u'Dropoff_Borough',
       u'Dropoff_Neighbourhood', u'Dropoff_Zip_code']

TO_USE = [u'tpep_pickup_datetime', u'tpep_dropoff_datetime',u'passenger_count', u'trip_distance', u'pickup_longitude',
       u'pickup_latitude', u'dropoff_longitude', u'dropoff_latitude', u'payment_type',
       u'fare_amount', u'tip_amount', u'total_amount', u'Pickup_Borough',
       u'Pickup_Neighbourhood', u'Pickup_Zip_code', u'Dropoff_Borough',
       u'Dropoff_Neighbourhood', u'Dropoff_Zip_code']


INDEX_TO_USE = [COLUMNS.index(item) for item in TO_USE]



sf = shapefile.Reader("new-york_new-york.imposm-shapefiles/new-york_new-york_osm_admin.shp")

names = {"Kings County":"Brooklyn","Queens County":"Queens","Richmond County":"Statten Island",
         "New York County":"Manhattan","Bronx County":"Bronx"}
ny_records = get_records(sf, names)

print "Building Grid"

nyGrid = grid_and_bur(SPACING,ny_records)

nyGrid.set_params()



class agg_data(object):
  def __init__(self):
    self.night = pd.read_csv("Clubs.csv")
    self.banks = pd.read_csv("banks.csv")
    self.bank_grid = None
    self.night_grid = None
    #self.cluster = {}
    self.heat_map = {}
    self.night["counts"] = 0
    #self.MAX_VAL = 0


  def set_boxes(self,grid):
    coords_night = self.night[["Lat","Long"]].values
    self.night = pd.concat([self.night,pd.DataFrame({"grid":map(lambda x:grid.get_index(*x),coords_night)})],axis = 1)
    self.night_grid = self.night["grid"].unique()

    coords_bank = self.banks[["Lat","Long"]].values
    self.banks = pd.concat([self.banks,pd.DataFrame({"grid":map(lambda x:grid.get_index(*x),coords_bank)})],axis = 1)
    self.bank_grid = self.banks["grid"].unique()

  def set_burough(self, grid):
    self.night.loc[:,"burs"] = map(lambda x: grid.get_burough(x), self.night[["Lat","Long"]].values)






  def initialize_heat_map(self):
    for t in np.arange(0,24,0.5):
        self.heat_map[t] = np.zeros(shape = nyGrid.relevant.shape)

    # def normalize_cmap(self):
    #     for key in self.heat_map:
    #         self.heat_map[key] = np.log(np.log(self.heat_map[key]+1)+1)/self.MAX_VAL

TOTAL_DATA = agg_data()
TOTAL_DATA.initialize_heat_map()

TOTAL_DATA.set_burough(nyGrid)
TOTAL_DATA.set_boxes(nyGrid)




#print TOTAL_DATA.night 

#Prepare to process the data

path = "taxi_data/yellow_"
# r = urllib.urlopen(url)
# soup = BeautifulSoup(r, 'lxml')




# def get_urls(soup):
#     for a in soup.findAll('a',href = True):
#         ref = a['href']
#         if "tlc-trip-data" in ref :
#             name = ref.split('/')[-1]
#             color = name.split('_')[0]
#             year = name.split("_")[-1].split("-")[0]
#             color = color[0].upper() + color[1:]+ "_Taxi"
#             file_path = color +"/" + name
#             if int(year) >=2015 and color == 'Yellow_Taxi':
#                 yield (ref,name.split("-")[-1][:2])


def turn_into_panda():
    for val in range(1,13):
        if val < 10:
            val = "0"+str(val)
        else:
            val = str(val)
        df = pd.read_csv(path+val+".csv",usecols = INDEX_TO_USE)
        df.loc[:,["Pickup_Zip_code","Dropoff_Zip_code"]] = df[["Pickup_Zip_code","Dropoff_Zip_code"]].apply\
                    (lambda x: pd.to_numeric(x,errors='coerce'))
        df.dropna(axis = 0, subset = ["Pickup_Zip_code","Dropoff_Zip_code"],inplace = True)
        yield taxi_data(df,nyGrid,val)

full_data = turn_into_panda()
try:
    while True:

        data = full_data.next()
        print data.name

        


        print "Converting datetime"
        data.convert_datetime()

        
        print "Adding Details"
        data.add_details()

        
        print "Cleaning Data"
        data.clean_data()
     



        # data.df.to_csv(path + data.name + "_new.csv", index = False)

        print "Setting Boxes"
        data.set_boxes()


        # print "Get night club counts"
        # data.get_night_counts(TOTAL_DATA)

        # print "Get bank pickups"
        # data.get_bank_pickups(TOTAL_DATA)
        print "Updataing Heatmap"
        data.update_heat_map(TOTAL_DATA)


        # print "Clustering"
        # data.perform_clustering(TOTAL_DATA)

        # file_name = "cluster_" + str(data.name)
        # with open(file_name + ".dill", "w") as f:
        # dill.dump(TOTAL_DATA.cluster, f)
        del data


except StopIteration:
    print "DONE"
    with open("agg_data_heat.dill","w") as f:
        dill.dump(TOTAL_DATA,f)
    pass




    # except StopIteration:
    #     print "Done"

# def reform_data_frame(soup):
#     for df in turn_into_panda(soup):
#         df.columns = chosen_names_2015
#         convert_datetime(df)
#         add_details(df)
#         df = clean_data(df, bounds_of_nyc)
#         yield df
#         #add_details
        


# # In[ ]:




# # In[29]:

# def get_burough_info(df,soup,spacing):
#     #for df in reform_data_frame(soup):
#     gridVals = get_all_boxes(df,latAr,lngAr).reset_index(drop = True)
#     burVals = pd.Series(get_all_burough(df))
#     burVal = pd.DataFrame({"bur":burVals}).reset_index(drop = True)
#     df = df.reset_index(drop = True)
#     gridVals = gridVals.reset_index(drop = True)

#     return pd.concat([df, burVals,gridVals], axis = 1)
        
        


# # In[45]:

# df.columns


# # In[30]:

# df = get_burough_info(df, soup,SPACING)


# # In[ ]:

# df.groupby("ti")


# # In[48]:

# get_heat_map_params(df, "tip_amount",0.1,"Jan")


# # In[47]:

# def get_heat_map_params(df,item, blur,name):
#     MAX_VAL = np.log(np.log(df.groupby(item).agg('size').max()+1)+1)+0.000001
#     counts = df.groupby(item).agg('size')
#     #maxVal = counts.max() + 0.000001
#     vals = np.zeros(shape = boxes.shape)
#     for i,val in enumerate(counts.index):
#         vals[val] = np.log(np.log(counts.values[i]+1)+1)/MAX_VAL
#     with open(name + "_cmap_"+str(item)+".dill","w") as f:
#         dill.dump(gaussian_filter(vals,sigma=blur),f)


# # In[ ]:

# def cluster_step1_get_coords(df):
#     Grouped = df.groupby(by = ["bur","pickup_year","pickup_month","pickup_day","time_category_drop"])
#     pick_coords, drop_coords = get_coords(df)
#     coords_pick_xy = convert_to_xy(pick_coords)
#     coords_drop_xy = convert_to_xy(drop_coords)
#     return (coords_pick_xy,coords_drop_xy)


# # In[ ]:

# df


# # In[22]:

# dfIter = reform_data_frame(soup)


# # In[23]:

# df = dfIter.next()


# # In[39]:

# get_ipython().magic(u'reset pandas')


# # In[ ]:



