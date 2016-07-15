
import pandas as pd
import re
from collections import defaultdict, Counter
import numpy as np
import math
import scipy as sp
import datetime
from sklearn import cluster
import utm
from numpy import linalg
from shapely import geometry
from itertools import combinations
import dill


def half_hour_grading(date_time):
	    time = date_time.time()
	    h,m = time.hour,time.minute
	    if m < 30:
	        m = 0
	    else:
	        m = 0.5
	    return h + m

def round_to_nearest(time_stamp):
    minutes = time_stamp.minute
    seconds = time_stamp.second
    if minutes%5 < 2:
        val = (minutes/5)*5
    elif minutes%5 >= 3:
        val =  (minutes/5 +1)*5
    else:
        if seconds <= 30:
            val=  (minutes/5)*5
        else:
            val =  (minutes/5+1)*5
    return val

def convert_to_xy_list(coord_list):
    xy_list = map(lambda x: utm.from_latlon(*x), coord_list)
    return xy_list
def convert_to_xy(coord_dict):
    return dict([(key,convert_to_xy_list(coord_dict[key]))for key in coord_dict])
def strip_xy(coord_list):
    return [val[:2] for val in coord_list]


class taxi_data(object):

	def __init__(self,df,grid,name):
		self.df = df
		self.grid = grid
		self.name = name

		self.df.columns = ["pickup_datetime", "dropoff_datetime","passenger_count", "trip_distance",\
					"pickup_long","pickup_lat","dropoff_long","dropoff_lat", \
					"payment_type","fare_amount","tip_amount","total_amount",u'Pickup_Borough',\
       				u'Pickup_Neighbourhood', u'Pickup_Zip_code', u'Dropoff_Borough',\
       				u'Dropoff_Neighbourhood', u'Dropoff_Zip_code']
		# self.df["percent"]  = self.df["tip_amount"]/self.df["total_amount"]
		# self.df["percent"][self.df["payment_type"] != 1] = np.nan

	#Set the parameters of this class



	def convert_datetime(self):
		cols = ["pickup_datetime","dropoff_datetime"]
		for col in cols:
			self.df.loc[:,col] = pd.to_datetime(self.df[col], format='%Y-%m-%d %H:%M:%S')
		# self.df.loc[:,"duration"] = self.df["duration"].apply(lambda x: pd.to_timedelta(x))

	def add_details(self):
		# self.df.loc[:,"pickup_month"] = self.df["pickup_datetime"].apply(lambda x: x.month)
		self.df.loc[:,"pickup_day"] = self.df["pickup_datetime"].apply(lambda x: x.weekday())
		self.df.loc[:,"duration"] = self.df["dropoff_datetime"]-self.df["pickup_datetime"]
		self.df.loc[:,"time_category_pick"] = self.df["pickup_datetime"].apply(lambda x: x.hour)
		self.df.loc[:,"dropoff_day"] = self.df["dropoff_datetime"].apply(lambda x: x.weekday())
		self.df.loc[:,"time_category_drop"] = self.df["dropoff_datetime"].apply(lambda x: x.hour)
    	

		# self.df.loc[:,"nearest_pick"] = self.df["pickup_datetime"].apply(lambda x: round_to_nearest(x))
		self.df.loc[:,"half_hour"] = self.df["dropoff_datetime"].apply(lambda x:half_hour_grading(x))
		


	def clean_data(self):
		min_lat, max_lat = self.grid.minLat, self.grid.maxLat
		min_long, max_long = self.grid.minLng, self.grid.maxLng
		self.df = self.df[(min_lat <= self.df.pickup_lat) &(self.df.pickup_lat <= max_lat) & (min_long <= self.df.pickup_long)\
		&(self.df.pickup_long<= max_long)]
		self.df = self.df[(min_lat <= self.df.dropoff_lat) &(self.df.dropoff_lat <= max_lat)\
		& (min_long <= self.df.dropoff_long)  &(self.df.dropoff_long<= max_long)]
		self.df = self.df[self.df.duration >= datetime.timedelta(0)]
		self.df = self.df.reset_index(drop = True)


	def set_buroughs(self,drop_or_pick = "pickup"):
		coords = self.df[[drop_or_pick + "_lat",drop_or_pick +"_long"]].values
		self.df = pd.concat([self.df,  pd.DataFrame({"bur":map(lambda x: self.grid.get_burough(x),coords)})],axis = 1)


	def set_boxes(self):
		coord_pick = self.df[["pickup_lat", "pickup_long"]].values
		coord_drop = self.df[["dropoff_lat", "dropoff_long"]].values
		# self.df.loc[:,"pick_grid"] = map(lambda x: self.grid.get_index(*x), coord_pick)
		self.df = pd.concat([self.df,pd.DataFrame({"drop_grid":map(lambda x: self.grid.get_index(*x), coord_drop)}),\
			pd.DataFrame({"pick_grid":map(lambda x: self.grid.get_index(*x), coord_pick)})],axis = 1)

	def update_heat_map(self, agg_data):
		# MAX_VALUE = np.log(np.log(self.df.groupby("drop_grid").agg('size').max()+1)+1)+0.000001
		# if MAX_VALUE > agg_data.MAX_VAL:
		# 	agg_data.MAX_VAL = MAX_VALUE

		for name, g in self.df.groupby("half_hour"):
			g2 = g.groupby("drop_grid").agg('size')
			for i,val in enumerate(g2.index):
				agg_data.heat_map[name][val] += g2.values[i]


	        

	def perform_clustering(self,agg_data):
		groups_to_use = ["Pickup_Borough","pickup_month","pickup_day","time_category_pick"]

		for name,group in self.df.groupby(by = groups_to_use):
			if name[0] == "Manhattan":
				eps = 80
				throttle = 0.0025
			else:
				eps = 150
				throttle = 0.005




			coords_pick = map(lambda x: utm.from_latlon(*x)[:2],zip(group.pickup_lat.values, group.pickup_long.values))
			min_samples = max(4,len(coords_pick)*throttle)
			dbScan = cluster.DBSCAN(eps = eps, min_samples= min_samples, metric = "euclidean")
			result = dbScan.fit_predict(coords_pick)
			group["result"] = result
			g2 = group[["pickup_lat","pickup_long","fare_amount","payment_type","duration","result"]].groupby("result")
			temp = []

			for name2,group2 in g2:
				if name2 != -1: 
					poly = geometry.MultiPoint(group2[["pickup_long","pickup_lat"]].values).convex_hull
					count_vals = len(group2["pickup_lat"])
					g2card = group2[group2["payment_type"] ==1]

					if g2card.size > 0:
						mean_tip = g2card["fare_amount"]/g2card["duration"].apply(lambda x: x.seconds/60.0)
						mean_tip = mean_tip.median()
					else:
						mean_tip = 0
					temp.append([poly,count_vals,mean_tip])
					#print temp

			if temp:
				
				dfTemp = pd.DataFrame(temp, columns = ["poly","counts","percent"])
				dfTemp["normalized"] = dfTemp["percent"]*(dfTemp["counts"]/dfTemp["counts"].sum())
				dfTemp["normalized"] = dfTemp["normalized"]/(dfTemp["normalized"].max()+0.0000001)
				name_of_group = tuple([self.name] + list(name))
				agg_data.cluster[name_of_group] = dfTemp
				del dfTemp

	def get_night_counts(self, agg_data):
		getCounts = self.df[((self.df["dropoff_day"] == 6) | (self.df["dropoff_day"] == 0)) \
					& ((0 <= self.df["time_category_drop"]) & (self.df["time_category_drop"]<= 4))].groupby("drop_grid").agg("size")
		curr_counts = getCounts[agg_data.night["grid"]].fillna(0).values
		agg_data.night["counts"] += curr_counts
		del getCounts


	def get_night_pickups(self, agg_data):
		get_drops =  self.df[((self.df["dropoff_day"] == 6) | (self.df["dropoff_day"] == 0)) \
					& ((0 <= self.df["time_category_drop"]) & (self.df["time_category_drop"]<= 3))].groupby("drop_grid")

		get_picks =  self.df[((self.df["pickup_day"] == 6) | (self.df["pickup_day"] == 0)) \
					& ((2 <= self.df["time_category_pick"]) & (self.df["time_category_pick"]<= 4))].groupby("pick_grid")
		

		pickups = pd.concat([get_drops.get_group(g) for g in agg_data.night_grid if g in get_drops.groups])
		dropoffs = pd.concat([get_picks.get_group(g) for g in agg_data.night_grid if g in get_picks.groups])

		del get_drops
		del get_picks

		total = pickups.append(dropoffs)
		total_same = total[total.duplicated()]

		pickups.drop(total_same.index, inplace=True)
		dropoffs.drop(total_same.index, inplace=True)

		del total
		del total_same

		pickups = pickups[["pickup_long","pickup_lat","Pickup_Zip_code","drop_grid","passenger_count"]]
		dropoffs = dropoffs[["dropoff_long","dropoff_lat","Dropoff_Zip_code","pick_grid","passenger_count"]]


		pickups = Counter(pickups.groupby(["drop_grid","Pickup_Zip_code"])["passenger_count"].sum().to_dict())
		dropoffs = Counter(dropoffs.groupby(["pick_grid","Dropoff_Zip_code"])["passenger_count"].sum().to_dict())

		with open("club_info_" +self.name +".dill", "w") as f:
			dill.dump(pickups + dropoffs, f)


	
		del pickups
		del dropoffs



	def get_bank_pickups(self, agg_data):
		getCounts = self.df[((self.df["dropoff_day"] != 6) & (self.df["dropoff_day"] != 0) \
			& (5 <= self.df["time_category_drop"]) & (self.df["time_category_drop"]<= 9))].groupby("drop_grid")
		getCounts = pd.concat([getCounts.get_group(g) for g in agg_data.bank_grid])

		zips = getCounts.groupby("Pickup_Zip_code").agg("size")
		zipdf = pd.DataFrame({"zip_code":zips.index, "count":zips.values},dtype = float)
		zipdf.to_csv("bank_picks_new_grid"+self.name+".csv", index = False)
		del getCounts
		del zips
		del zipdf

	        


	


