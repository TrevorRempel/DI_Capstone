from flask import Flask, render_template, request, redirect
import pandas as pd
import json
import os
import googlemaps
import pickle
from taxi_analysis import select_values, process_lat_lng
import datetime



app = Flask(__name__)
GMAPS_KEY = os.getenv('GOOGLE_MAP')
app.CENTER = [40.7639206199602, -73.9383529238219]
app.LAT = (40.477399,40.917577)
app.LNG = (-74.25909, -73.700009)
app.SRC = "https://maps.googleapis.com/maps/api/js?key=" +GMAPS_KEY +"&callback=initMap"
app.YEAR = 2015
days_list = ["Monday","Tuesday","Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
months_list = ["January","February","March", "April","May", "June", "July","August", "September","October",\
"November","December"]


#Load in the data that will be used

#with open('pick.pickle', 'rb') as f:
#	dfpick = pickle.load(f) 

with open('drop.pickle', 'rb') as f:
	dfdrop = pickle.load(f)




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
		

		return render_template('index.html', src = app.SRC, center = app.CENTER,plot_lat = None,\
			plot_lng = None, month = month_today, day = day_today, time = time_today, time_list = range(24), month_list = months_list,\
			day_list = days_list)
	if request.method == 'POST':
		#dd = request.form.get("date_input")
		#year = int(request.form.get("year"))
		month = request.form.get("month")
		day = request.form.get("day")
		month_val = months_list.index(month)+1
		day_val = days_list.index(day)
		#print month,day
		time = int(request.form.get("time"))

		lat, lng = process_lat_lng(select_values(dfdrop,[app.YEAR],[month_val],[day_val],[time]))
	

		#At this point we assume that the month, day and time are being passed in as a number so we select as
		#dfGoing = select_values(dfdrop, [app.YEAR], range(month, month+1), range(day, day+1), range(time, time+1))
		##lats, lngs = process_lat_lng(dfGoing) 
		#print dd
		#print "hello"

		return render_template('index.html', src = app.SRC, center = app.CENTER,plot_lat = lat, plot_lng = lng, \
			month = month, day = day, time = time, time_list = range(24), month_list = months_list,\
			day_list = days_list)



		
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
  #app.run(debug = True, port = 5001)
  app.run(port=33507)
