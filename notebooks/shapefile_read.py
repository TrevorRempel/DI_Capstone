import shapely
import shapefile
from shapely import geometry,ops,speedups
import numpy as np



speedups.enable()

def get_records(sf,names):
	sf_ref = sf.shapeRecords()
	ny_records = {}
	polygons = []
	for rec in sf_ref:
	    name = rec.record[2]
	    if rec.record[-1] == 6 and name in names:
	        poly = geometry.Polygon(rec.shape.points)
	        if not poly.is_valid:
	            poly = poly.buffer(0)[1]
	        ny_records[names[name]] = poly
	return ny_records




class grid_and_bur(object):
	def __init__(self, SPACING, records):
		self.spacing = SPACING
		self.records = records
		self.minLat = None
		self.maxLat = None
		self.minLng = None
		self.maxLng = None
		self.latAr = None
		self.lngAr = None
		self.relevant = None


	def set_params(self):
		minLat = np.inf
		maxLat = -np.inf
		minLng = np.inf
		maxLng = -np.inf
		for bur in self.records:
		    lng,lat = self.records[bur].boundary.xy
		    lngMin,lngMax = min(lng),max(lng)
		    latMin,latMax = min(lat), max(lat)
		    if lngMin < minLng:
		        minLng = lngMin
		    if lngMax > maxLng:
		        maxLng = lngMax
		    if latMin < minLat:
		        minLat = latMin
		    if latMax > maxLat:
		        maxLat = latMax

		latNums = int((maxLat-minLat)/self.spacing)
		lngNums =int((maxLng-minLng)/self.spacing)
		latAr = np.linspace(minLat-10**(-10),maxLat+10**(-10), latNums)
		lngAr = np.linspace(minLng-10**(-10), maxLng+10**(-10),lngNums)

		relevant = []
		full_NYC = ops.unary_union([self.records[val] for val in self.records])
		for i in range(len(lngAr)-1):
		    for j in range(len(latAr)-1):
		    	box = geometry.box(lngAr[i],latAr[j],lngAr[i+1],latAr[j+1])
		    	if box.intersects(full_NYC):
		        	relevant.append(box.intersection(full_NYC))
		    	else:
		        	relevant.append(None)

	    
		self.minLat = minLat
		self.maxLat = maxLat
		self.minLng = minLng
		self.maxLng = maxLng
		self.latAr = latAr
		self.lngAr = lngAr
		self.relevant = np.array(relevant).reshape(len(lngAr)-1, len(latAr)-1)


	def get_index(self,lat,lng):
	    jLat = np.argmax(lat <= self.latAr)-1
	    iLng = np.argmax(lng<=self.lngAr)-1
	    return (iLng,jLat)



	def get_burough(self,coord):
	    point = geometry.Point(coord[::-1])

	    for bur, poly in self.records.items():
	        #if poly[0].contains(point):
	        if poly.contains(point):
	            return bur
	    return None

