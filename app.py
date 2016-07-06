from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import os
import re
import googlemaps
import shapely
import math
import dill
import matplotlib
from taxi_analysis import select_values, process_lat_lng
import datetime



app = Flask(__name__)
GMAPS_KEY = os.getenv('GOOGLE_MAP')

app.LAT = (40.477399,40.917577)
app.LNG = (-74.25909, -73.700009)
app.SRC = "https://maps.googleapis.com/maps/api/js?key=" +GMAPS_KEY +"&libraries=places&callback=initMap"
app.YEAR = 2015
days_list = ["Monday","Tuesday","Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
months_list = ["January","February","March", "April","May", "June", "July","August", "September","October",\
"November","December"]

with open("cmap.dill", "r") as f:
	cmap = dill.load(f)

def get_Club_Data():
	df = pd.read_csv("night.csv")
	
	lat_club = map(str, df["Lat"].values)
	lng_club = map(str,df["Long"].values)
	counts = map(str,df["percent"].values)
	name = map(str,df["Name"].values)
	vals  = [(counts[i],name[i],lat_club[i],lng_club[i]) for i in range(len(name))]
	vals = sorted(vals)
	counts = [val[0] for val in vals]
	name  = [val[1] for val in vals]
	lat_club = [val[2] for val in vals]
	lng_club = [val[3] for val in vals]
	# web = map(str,dfRest["website"].values)
	# info = dfRest["info"]

	return lat_club,lng_club, counts,name


lat_club,lng_club,counts,names = get_Club_Data()
#info = [json.dumps(item) for item in info]

# relevant_keys = ['name','rating','formatted_address','formatted_phone_number','website']


# info = [json.dumps(item, ensure_ascii=False).encode('utf8') for item in info]
#info = [json.dumps(make_str(item)) for item in info]
#Load in the data that will be used

#with open('pick.pickle', 'rb') as f:
#	dfpick = pickle.load(f) 

# with open('pick.pickle', 'rb') as f:
# 	dfpick = pickle.load(f)

# with open('unfilter_pick.pickle','rb') as f:
# 	dfunfilt = pickle.load(f)


@app.route('/')
def main():
  return redirect('/index')

@app.route('/index', methods = ['GET','POST'])
def index():
	if request.method == 'GET':


		
		#When the website first launches grab the current date-time and use this as an input value
		today = datetime.datetime.today()
		#year_today = str(today.year)
		month_today = today.strftime("%B")
		day_today = today.strftime("%A")
		time_today = today.hour
		#lat, lng = process_lat_lng(select_values(dfdrop,[app.YEAR],[month_today],[day_today],[time_today]))
		# lat = map(str,dfunfilt["pickup_lat"].values)
		# lng = map(str, dfunfilt["pickup_long"].values)
		lat,lng = None, None

		return render_template('index.html',src = app.SRC,plot_lat = lat,\
			plot_lng = lng, month = month_today, day = day_today, time = time_today, time_list = range(24), month_list = months_list,\
			day_list = days_list, lat_club = lat_club,lng_club = lng_club,counts = counts,names = names)
	if request.method == 'POST':
		#dd = request.form.get("date_input")
		#year = int(request.form.get("year"))

		try:
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
			poly = []
			for polygon in poly_info["poly"].values:
				lng, lat = polygon.exterior.xy
				poly.append([list(lng),list(lat)])
			weight = ["{:.1f}".format(val) for val in list(poly_info["percent"].values)]

			percents = [math.log(val + 1) for val in poly_info["percent"].values]
			MAX_VAL = max(percents)+0.001
			percents = [val/MAX_VAL for val in percents]
			
			colors = [matplotlib.colors.rgb2hex(cmap(val)) for val in percents]


			lat,lng = None,None
			# lat, lng = process_lat_lng(select_values(dfpick,[app.YEAR],[month_val],[day_val],[time]))
		except ValueError:
			lat, lng = None, None
	

		#At this point we assume that the month, day and time are being passed in as a number so we select as
		#dfGoing = select_values(dfdrop, [app.YEAR], range(month, month+1), range(day, day+1), range(time, time+1))
		##lats, lngs = process_lat_lng(dfGoing) 
		#print dd
		#print "hello"

		return render_template('index2.html',scroll = 'premap', src = app.SRC,plot_lat = lat, plot_lng = lng,
			month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
			day_list = days_list,lat_club = lat_club,lng_club = lng_club,counts = counts,names= names,poly = poly,colors = colors,
			weight = weight)



		
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



if __name__ == '__main__':
  app.run(debug = True, port = 5001)
  #app.run(port=33507)
