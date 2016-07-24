<<<<<<< HEAD
from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import os
import re
import googlemaps
import math
import dill
import matplotlib
from taxi_analysis import select_values, process_lat_lng
import datetime



app = Flask(__name__)
GMAPS_KEY = os.getenv('GOOGLE_MAP')

app.SRC = "https://maps.googleapis.com/maps/api/js?key=" +GMAPS_KEY +"&libraries=places&callback=initMap"
app.YEAR = 2015
days_list = ["Monday","Tuesday","Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
months_list = ["January","February","March", "April","May", "June", "July","August", "September","October",\
"November","December"]

with open("../data/cmap.dill", "r") as f:
	cmap = dill.load(f)

with open("../data/zip_polys.dill","r") as f:
	zip_polys = dill.load(f)

with open("../data/zip_club.dill","r") as f:
	zip_club = dill.load(f)



dfClub = pd.read_csv("../data/night_info.csv",encoding = 'utf-8').sort_values("percent", ascending = False)

club_counts,lat_club,lng_club,club_names,club_urls = zip(*dfClub[["percent","Lat","Long","Name_Yelp","url"]].values)

app.tip_poly,app.tip_colors,app.tip_weight = None,None,None
club_poly,club_colors,club_weight = None, None, None



@app.route('/')
def main():
  return redirect('/index')

@app.route('/index', methods = ['GET','POST'])
def index():
	today = datetime.datetime.today()
	month = today.strftime("%B")
	day = today.strftime("%A")
	time = today.hour
	if request.method == 'GET':
		
		#When the website first launches grab the current date-time and use this as an input value

		


		return render_template('index.html',src = app.SRC, month = month, day = day, time = time, \
			time_list = range(24), month_list = months_list, day_list = days_list, \
			lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names = club_names,club_urls = club_urls)



	if request.method == 'POST':

		to_render = 'index2.html'
		if 'month' in request.form.keys():

			month = request.form.get("month")
			day = request.form.get("day")
			time = request.form.get("time")



			month_val = months_list.index(month)+1
			if month_val < 10:
				month_str = "0"+str(month_val)
			else:
				month_str = str(month_val)

			day_val = days_list.index(day)
	
			time = int(time)

			
			to_load = "../data/new_cluster_area_" + month_str +".dill"
			with open(to_load, "r") as f:
				poly_info = dill.load(f)[(month_val,day_val,time)]
			app.tip_poly = []
			for polygon in poly_info["poly"].values:
				lng, lat = polygon
				app.tip_poly.append([list(lng),list(lat)])
			app.tip_weight = ["{:.0f}".format(val) for val in list(poly_info["counts"].values)]

			tip_percents = [math.sqrt(val+1)  for val in poly_info["counts"].values]
			MAX_VAL = max(tip_percents)+0.001
			tip_percents = [val/MAX_VAL for val in tip_percents]
			
			app.tip_colors = [matplotlib.colors.rgb2hex(cmap(val)) for val in tip_percents]
			scroll = 'tip_map'

		elif 'reset_club' in request.form.keys():
			scroll = 'club_map'

		else:
			scroll = 'nav-bar main'
	

		return render_template(to_render,scroll = scroll, src = app.SRC,
			month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
			day_list = days_list,lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names= club_names,\
			tip_poly = app.tip_poly,tip_colors = app.tip_colors,
			tip_weight = app.tip_weight,club_urls = club_urls)



		
		#notValid, fig = make_html(ticker, options)
		#app.script, app.div = components(fig)
		#output_file("test.html")

		
		'''
		TOOLS = "resize,crosshair,box_zoom,reset,box_select,save"
		output_file("test.html")
		fig=figure(title="Sensor data", tools = TOOLS)
		fig.line([1,2,3,4],[2,4,6,8])
		#global script
		#global div
		script, div=components(fig)
		'''

@app.route('/club_zipcodes', methods = ['GET','POST'])
def club_zipcodes():

	today = datetime.datetime.today()
	month = today.strftime("%B")
	day = today.strftime("%A")
	time = today.hour

	club = request.form.get('club')

	if club:


		grid = dfClub[dfClub["Name_Yelp"] == club]["grid"].values[0]
		# print dfClub[dfClub["Name_Yelp"] == club][["Lat","Long"]].values
		cur_lat,cur_lng,cur_url = dfClub[dfClub["Name_Yelp"] == club][["Lat","Long","url"]].values[0]

		l,r = grid.split(",")
		grid_point = (int(l[1:]),int(r[:-1]))
		zips = zip_club[grid_point]

		club_poly = []
		club_percent = []
		club_weight = []
		for zip_code, weight in zips.items():
			zip_code = int(zip_code)
			if zip_code != 11371 and zip_code !=11430 and zip_code in zip_polys and weight > 0.1:
				for poly in zip_polys[zip_code]:
					lng,lat = poly
					club_poly.append([list(lng),list(lat)])
					club_percent.append(weight)
					club_weight.append(zip_code)

		club_weight = map(str,map(int,club_weight))
		club_colors = [matplotlib.colors.rgb2hex(cmap(val)) for val in club_percent]
		scroll = 'club_map'
		to_render = 'index3.html'
		return render_template(to_render,scroll = scroll, src = app.SRC,
				month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
				day_list = days_list,lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names= club_names,\
				tip_poly = app.tip_poly,tip_colors = app.tip_colors,
				tip_weight = app.tip_weight,club_urls = club_urls,club_weight = club_weight,club_colors = club_colors,club_poly = club_poly,\
				cur_info = [cur_lat, cur_lng,club,cur_url])
	else:
		return redirect('/index#club_map')


if __name__ == '__main__':
  app.run(debug = True, port = 5002)
  #app.run(port=33507)
||||||| merged common ancestors
=======
from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import os
import re
import googlemaps
import math
import dill
import matplotlib
from taxi_analysis import select_values, process_lat_lng
import datetime



app = Flask(__name__)
GMAPS_KEY = os.getenv('GOOGLE_MAP')

app.SRC = "https://maps.googleapis.com/maps/api/js?key=" +GMAPS_KEY +"&libraries=places&callback=initMap"
app.YEAR = 2015
days_list = ["Monday","Tuesday","Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
months_list = ["January","February","March", "April","May", "June", "July","August", "September","October",\
"November","December"]

with open("cmap.dill", "r") as f:
	cmap = dill.load(f)

with open("zip_polys.dill","r") as f:
	zip_polys = dill.load(f)

with open("zip_club.dill","r") as f:
	zip_club = dill.load(f)



dfClub = pd.read_csv("night_info.csv",encoding = 'utf-8').sort_values("percent", ascending = False)

club_counts,lat_club,lng_club,club_names,club_urls = zip(*dfClub[["percent","Lat","Long","Name_Yelp","url"]].values)

app.tip_poly,app.tip_colors,app.tip_weight = None,None,None
club_poly,club_colors,club_weight = None, None, None



@app.route('/')
def main():
  return redirect('/index')

@app.route('/index', methods = ['GET','POST'])
def index():
	today = datetime.datetime.today()
	month = today.strftime("%B")
	day = today.strftime("%A")
	time = today.hour
	if request.method == 'GET':
		
		#When the website first launches grab the current date-time and use this as an input value

		


		return render_template('index.html',src = app.SRC, month = month, day = day, time = time, \
			time_list = range(24), month_list = months_list, day_list = days_list, \
			lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names = club_names,club_urls = club_urls)



	if request.method == 'POST':
		print request.form.keys()

		to_render = 'index2.html'
		if 'month' in request.form.keys():

			month = request.form.get("month")
			day = request.form.get("day")
			time = request.form.get("time")



			month_val = months_list.index(month)+1
			if month_val < 10:
				month_str = "0"+str(month_val)
			else:
				month_str = str(month_val)

			day_val = days_list.index(day)
	
			time = int(time)

			
			to_load = "new_cluster_" + month_str +".dill"
			with open(to_load, "r") as f:
				poly_info = dill.load(f)[(month_val,day_val,time)]
			app.tip_poly = []
			for polygon in poly_info["poly"].values:
				lng, lat = polygon
				app.tip_poly.append([list(lng),list(lat)])
			app.tip_weight = ["{:.1f}".format(val) for val in list(poly_info["percent"].values)]

			tip_percents = [math.log(val + 1) for val in poly_info["percent"].values]
			MAX_VAL = max(tip_percents)+0.001
			tip_percents = [val/MAX_VAL for val in tip_percents]
			
			app.tip_colors = [matplotlib.colors.rgb2hex(cmap(val)) for val in tip_percents]
			scroll = 'tip_map'

		elif 'reset_club' in request.form.keys():
			scroll = 'club_map'

		else:
			scroll = 'nav-bar main'
	
		print app.tip_weight
		return render_template(to_render,scroll = scroll, src = app.SRC,
			month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
			day_list = days_list,lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names= club_names,\
			tip_poly = app.tip_poly,tip_colors = app.tip_colors,
			tip_weight = app.tip_weight,club_urls = club_urls)



		
		#notValid, fig = make_html(ticker, options)
		#app.script, app.div = components(fig)
		#output_file("test.html")

		
		'''
		TOOLS = "resize,crosshair,box_zoom,reset,box_select,save"
		output_file("test.html")
		fig=figure(title="Sensor data", tools = TOOLS)
		fig.line([1,2,3,4],[2,4,6,8])
		#global script
		#global div
		script, div=components(fig)
		'''

@app.route('/club_zipcodes', methods = ['GET','POST'])
def club_zipcodes():

	today = datetime.datetime.today()
	month = today.strftime("%B")
	day = today.strftime("%A")
	time = today.hour

	club = request.form.get('club')
	print club

	if club:


		grid = dfClub[dfClub["Name_Yelp"] == club]["grid"].values[0]
		# print dfClub[dfClub["Name_Yelp"] == club][["Lat","Long"]].values
		cur_lat,cur_lng,cur_url = dfClub[dfClub["Name_Yelp"] == club][["Lat","Long","url"]].values[0]

		l,r = grid.split(",")
		grid_point = (int(l[1:]),int(r[:-1]))
		zips = zip_club[grid_point]

		club_poly = []
		club_percent = []
		club_weight = []
		for zip_code, weight in zips.items():
			zip_code = int(zip_code)
			if zip_code != 11371 and zip_code !=11430 and zip_code in zip_polys and weight > 0.1:
				for poly in zip_polys[zip_code]:
					lng,lat = poly
					club_poly.append([list(lng),list(lat)])
					club_percent.append(weight)
					club_weight.append(zip_code)

		club_weight = map(str,map(int,club_weight))
		club_colors = [matplotlib.colors.rgb2hex(cmap(val)) for val in club_percent]
		scroll = 'club_map'
		to_render = 'index3.html'
		return render_template(to_render,scroll = scroll, src = app.SRC,
				month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
				day_list = days_list,lat_club = lat_club,lng_club = lng_club,club_counts = club_counts,club_names= club_names,\
				tip_poly = app.tip_poly,tip_colors = app.tip_colors,
				tip_weight = app.tip_weight,club_urls = club_urls,club_weight = club_weight,club_colors = club_colors,club_poly = club_poly,\
				cur_info = [cur_lat, cur_lng,club,cur_url])
	else:
		return redirect('/index#club_map')


if __name__ == '__main__':
  app.run(debug = True, port = 5002)
  #app.run(port=33507)
>>>>>>> b31fe84f50e9f7f8b19261158ff50d87efccd5b0
