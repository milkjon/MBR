#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	webserver.py
#	
#	Implements the HTTP Request Server
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#----------------------------------------------------------------------------------------------------------------------#

# python library imports
import string, cgi, time, urlparse, zlib, os.path, unicodedata, datetime, time, gc
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# local imports
import iTunesLibrary
import Debug


#----------------------------------------------------------------------------------------------------------------------#
#  Globals
#----------------------------------------------------------------------------------------------------------------------#

global Library, Config

Library = None
Config = {}

global Hosts, Requests, NewRequests
# Hosts dictionary - all remote hosts (users) that have made requests
#	Contents:
#		key:	IP-address of host
#		value:	dict{ 'requests':		list[ dict{'id': (requestID), 'songID': (songID), 'time': (timestamp)}, ... ]
#					  'banned':			0 or 1
#					}

Hosts = {}

# Requests list - all requests received by server
#	Contents:
#		list[ dict{ 'id': (requestID),
#					'info': dict{ 'songID': (songID), 'time': (timestamp), 'host': (host IP),
#									'requestedBy': (requestor), 'dedication': (dedication info) }
#		          }
#		    ]

Requests = []

# NewRequests list - requests waiting to be collected by the display program.
#	Contents:
#		list[ (requestID1), (requestID2), ... ]

NewRequests = []

#----------------------------------------------------------------------------------------------------------------------#
#  Load configuration
#----------------------------------------------------------------------------------------------------------------------#

def LoadConfig():
	global Library, Config
	
	# which Library DB to use?  Currently the only acceptable option is "iTunes"
	Config['Library'] = "iTunes"

	# port to which the HTTP request server binds
	Config['Port'] = 15800

	# directory for saving prefs and logs
	# *Jonathan* this may need to be changed on the Mac
	Config['AppDir'] = os.path.join(os.path.expanduser('~'), ".mbradio")

	# iTunes DB location   *Jonathan* this will need to be changed for Mac
	Config['iTunesDB'] = os.path.join(os.path.expanduser('~'), 'Music\iTunes\iTunes Music Library.xml')

	# Max requests are enforced on sliding hour-long timeframe
	Config['maxRequests_User'] = 10
	Config['maxRequests_Artist'] = 5
	Config['maxRequests_Album'] = 5
	Config['maxRequests_Song'] = 2

	Library = None

	if Config['Library'] == "iTunes":
		Library = iTunesLibrary.iTunesLibrary()
		
		Debug.out('Loading song database...')
		Library.load(Config['iTunesDB'])
	
#enddef LoadConfig

#----------------------------------------------------------------------------------------------------------------------#
#  BaseHTTPServer implementation
#----------------------------------------------------------------------------------------------------------------------#

requestCount = 0

class MBRadio(BaseHTTPRequestHandler):
	
	def sendError(self, num, text):
		if not text:
			text = "Server error"
		if not num:
			num = 500
			
		self.send_response(num)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()
		self.wfile.write(text)
	
	#enddef sendError
	
	def do_GET(self):
			
		#---------------------------------------------------------------------------------------------------------------
		#  Acceptable GET parameters
		#  
		#  HTTP GET requests are received by the server in the format /command/?var1=value&var2=value....
		#---------------------------------------------------------------------------------------------------------------
		#
		#  Handled commands:
		#
		#	/search/
		#
		#		This interface is used to search the library for songs. This request is only sent from the
		#		radio station website to get the tracklist to allow users to request songs. It returns a list of
		#		songs in XML format.
		#
		#		Query string parameters:
		#			PARAM		TYPE	REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			for=		string	 Y		a string literal to search for
		#			by=			string	 Y		must be one of [letter|artist|title|genre|any]
		#			sort=		string	 N		Must be a list in the format "field1-direction,field2-direction..."
		#
		#										field is one of (artist|title|album|genre)
		#										direction is one of (asc|desc) - if unspecified, defaults to asc
		#
		#										If sort == "", defaults to "artist-asc,title-asc"
		#										If sort == "genre-[dir]", defaults to "genre-[dir],artist-asc,title-asc"
		#										If sort != "", and does not include 'title', then the sort will
		#											always be appended with sort+=",title-asc"
		#
		#										NOTE! At this time my implementation ignores the sort direction 
		#										      directive until I can write some better sorting code. All sorts
		#										      will be done ascending until then.
		#
		#			results=	integer	 N		the number of results to return  (defaults to 100)
		#			starting=	integer	 N		For continuation of search results, return songs starting at
		#										result #X (defaults to 0)
		#			compress=	string	 N		If compress == "", don't compress.
		#										If compress == "gzip", return results gzip'ed
		#
		#		Returns XML of the form:
		#			<songlist count="(count)" total="(all songs found)" first="(first result)" last="(last result)">
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#				...
		#			</songlist>
		#
		#	/new-requests/
		#
		#		This interface is only used internally by the request-list display app on the DJ's personal
		#		computer. It returns the current queue of song requests in XML format. Once the requests have been
		#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
		#		Any requests that do not originate from the localhost are ignored.
		#
		#		Query string parameters:
		#			PARAM		TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			clear=		string		N		must be one of [yes|no]  (defaults to 'yes')
		#			order=		string		N		must be one of [newest|oldest]  (defaults to 'newest')
		#
		#		Returns XML of the form:
		#			<requestlist count="(count)">
		#				<request id="(requestID)">
		#					<time></time><host></host><requestedby></requestedby><dedication></dedication>
		#					<song id="(songID)">
		#						<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#					</song>
		#				</request>
		#				...
		#			</requestlist>
		#
		#	/requests/
		#
		#		This interface is used by the webserver to get a list of recent requests to display on the website.
		#		Requests are always returned in descending order by the time the request was made.
		#
		#		Query string parameters:
		#			PARAM		TYPE			REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			results=	string|integer	Y		if results=='all', returns all requests
		#												if results==X, where X is an integer, returns the most recent X
		#													requests made to the server
		#
		#		Returns XML of the form: 
		#			<requestlist count="(count)">
		#				<request id="(requestID)">
		#					<time></time><host></host><requestedby></requestedby><dedication></dedication>
		#					<song id="(songID)">
		#						<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#					</song>
		#				</request>
		#				...
		#			</requestlist>
		#
		#	/time/
		#
		#		Returns the local time on the DJ's computer. Needed for certain things on the server.
		#
		#		Query string parameters: (none)
		#
		#		Returns XML of the form:
		#			<time>(current local time)</time>
		#
		#---------------------------------------------------------------------------------------------------------------
		
		try:
			# split the request into the "file name" and the "query string"
			fileStr, sepChar, queryStr = self.path.partition('?')
			
			if fileStr == '/search/' and queryStr:
			
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				if not args:
					self.sendError(500, 'Incomple search parameters')
					return

				if not args.has_key('by') or not args.has_key('for') or not args['by'] or not args['for']:
					self.sendError(500, 'Incomple search parameters: /search/?for=X&by=Y required')
					return
					
				searchBy = args['by'][0].lower()
				searchFor = args['for'][0]
				
				if args.has_key('results') and args['results']:
					numResults = int(args['results'][0])
				else:
					numResults = 100
					
				if args.has_key('starting') and args['starting']:
					startingFrom = int(args['starting'][0]) - 1
				else:
					startingFrom = 0
				
				# convert sort string "field1-dir,field2-dir..." to list: [(field1,dir), (field2,dir), ...]
				sortBy = []
				if args.has_key('sort') and args['sort']:
					sortStr = args['sort'][0].lower()
					if sortStr.find('title') == -1:
						sortStr += ',title=asc'
					terms = map(lambda t: t.partition('-'), map(lambda t: t.strip(), sortStr.split(',')))

					# verify that all (field,dir) pairs in the list are acceptable
					for field, dummy, dir in terms:
						if field in ['artist','title','album','genre']:
							# make sure it's not a duplicate
							if not filter(lambda pair: pair[0]==field, sortBy):
								if dir and dir in ['asc','desc']:
									sortBy.append( (field,dir) )
								else:
									sortBy.append( (field,'asc') )
				
				if not sortBy:
					sortBy = [('artist','asc'), ('title', 'asc')]
				if len(sortBy) == 1 and sortBy[0][0] == 'genre':
					sortBy.expand( [('artist', 'asc'), ('title', 'asc')] )

				# Execute the search on the music Library!
				
				if searchBy == "letter":
					resultSet = Library.searchBy_Letter(searchFor)
				elif searchBy == "artist":
					resultSet = Library.searchBy_Artist(searchFor)
				elif searchBy == "genre":
					resultSet = Library.searchBy_Genre(searchFor)
				elif searchBy == "title":
					resultSet = Library.searchBy_Title(searchFor)
				elif searchBy == "any":
					resultSet = Library.searchBy_Any(searchFor)
				else:
					self.sendError(500, 'Unknown search parameter by=' + searchBy)
					return
					
				if resultSet is None:
					self.sendError(500, 'Search error occurred')
					return

				# sort the results
				resultSet = SortSonglist(resultSet,sortBy)
				
				# packages the results as XML
				packagedResults = PackageSonglist(resultSet, numResults, startingFrom)
				headerContentType = 'text/xml'
				
				# gzip the results?
				if args.has_key('compress') and args['compress']:
					if args['compress'][0].lower() == 'gzip':
						headerContentType = 'application/x-gzip'
						packagedResults = zlib.compress(packagedResults)
				
				# send it back
				self.send_response(200)
				self.send_header('Content-type', headerContentType)
				self.end_headers()
				self.wfile.write(packagedResults)
				
				gc.collect()
				return
					
			#endif fileStr == '/search/'
			
			
			elif fileStr == '/new-requests/':
				global NewRequests
				
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				clear = 'yes'
				order = 'newest'
				if not args is None:
					if args.has_key('clear') and args['clear']:
						if args['clear'][0] == 'yes' or args['clear'][0] == 'no':
							clear = args['clear'][0]
					if args.has_key('order') and args['order']: 
						if args['order'][0] == 'newest' or args['order'][0] == 'oldest':
							order = args['order'][0]
				
				orderedRequests = list(NewRequests)
				if order == 'newest':
					orderedRequests.reverse()

				# package new requests as XML
				packageStr = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<requestlist count=\"' + str(len(orderedRequests)) + '\">\n'
	
				for requestID in orderedRequests:
					packageStr = packageStr + PackageRequest(requestID)
					
				packageStr = packageStr + '</requestlist>'
				
				# send it back
				self.send_response(200)
				self.send_header('Content-type', 'text/xml')
				self.end_headers()
				self.wfile.write(packageStr)
				
				# clear the list?
				if clear == 'yes':
					NewRequests = []
					
				gc.collect()
				return
				
			#endif fileStr == '/new-requests/':
			
			
			elif fileStr == '/requests/':
				
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				if args is None or not args.has_key('results') or not args['results']:
					self.sendError(500, 'Incomple query parameters')
					return
				
				# sort requests by timestamp desc:
				requestListToSort = map(lambda reqDict: (reqDict['info']['time'], reqDict['id']), Requests)
				requestListToSort.sort()
				requestListToSort.reverse()
				sortedRequestList = map(lambda pair: pair[1], requestListToSort)
					
				if args['results'][0] == 'all':
					numResults = len(sortedRequestList)
				else:
					numResults = int(args['results'][0])
					if numResults <= 0:
						numResults = 10
					if numResults > len(sortedRequestList):
						numResults = len(sortedRequestList)
				
				# take the slice:
				slicedRequestList = sortedRequestList[0:numResults]
				
				# package the requests as XML
				packageStr = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<requestlist count=\"' + str(len(slicedRequestList)) + '\">\n'
	
				for requestID in slicedRequestList:
					packageStr = packageStr + PackageRequest(requestID)
					
				packageStr = packageStr + '</requestlist>'
				
				# send it back
				self.send_response(200)
				self.send_header('Content-type', 'text/xml')
				self.end_headers()
				self.wfile.write(packageStr)
				
				gc.collect()
				return
				
			#endif fileStr == '/requests/':
			
			elif fileStr == '/time/':
				
				self.send_response(200)
				self.send_header('Content-type', 'text/xml')
				self.end_headers()
				self.wfile.write('<time>' + time.ctime() + '</time>')
				return
				
			#endif fileStr == '/time/':
			
			
			# error fall-through
			self.sendError(500, 'Server error')
			return

		except:
			self.sendError(500, 'Server error')
			pass
			
	#enddef do_GET
	
	def sendRequestError(self, code):

		if code == 601:
			message = 'Request limit reached: the same song can only be requested ' + str(Config['maxRequests_Song']) + ' times every 60 minutes'
		elif code == 602:
			message = 'Request limit reached: the same artist can only be requested ' + str(Config['maxRequests_Song']) + ' times every 60 minutes'
		elif code == 604:
			message = 'Request limit reached: the same album can only be requested ' + str(Config['maxRequests_Song']) + ' times every 60 minutes'
		elif code == 700:
			message = "Invalid request (Unknown error)"
		elif code == 701:
			message = "Your IP has been banned from making requests"
		elif code == 703:
			message = "Requested song ID invalid"
		elif code == 704:
			message = 'Request limit reached: you can only request ' + str(Config['maxRequests_User']) + ' songs every 60 minutes'
		elif code == 708:
			message = 'You have already requested this song'
		else:
			message = "Server Error"
			code = 700
			
		response = '''<?xml version="1.0" encoding="UTF-8"?>
					<request>
						<application><apptype>MBRadio Server</apptype><version>1.0</version></application>
						<status><code>''' + str(code) + '</code><message>' + message + '</message></status></request>'

		self.send_response(200)
		self.send_header('Content-type', 'text/xml')
		self.end_headers()
		self.wfile.write(response)
		return
	#enddef sendRequestError
	
	
	def do_POST(self):
		
		#---------------------------------------------------------------------------------------------------------------
		#  Acceptable POST parameters
		#  
		#  HTTP POST requests are received in the format /command/ along with standard HTTP Form Post Data
		#---------------------------------------------------------------------------------------------------------------
		#
		#  Handled commands:
		#
		#	/req/
		#		Form data parameters:
		#			NAME			TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			songID 			integer		Y		the iTunes track id
		#			host			string 		Y		IP address of requester
		#			requestedBy		string 		N		Name of the person making the request
		#			dedication		string		N		A short message (dedication) for the request
		#
		#		Returns XML of the form:
		#			<request>
		#				<application>
		#					<apptype>MBRadio</apptype><version>1.0</version>
		#				</application>
		#				<status>
		#					<code>(status code)</code><message>(status code desc.)</message><requestID>(new request ID)</requestID>
		#				</status>
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#			</request>
		#
		#		Status codes:
		#			200		OK		Request recieved!
		#			601		ERROR	Request limit reached: Song can only be requested xx times every 60 minutes
		#			602		ERROR	Request limit reached: Artist can only be requested xx times every 60 minutes
		#			604		ERROR	Request limit reached: Album can only be requested xx times every 60 minutes
		#			605		ERROR	Song is already in the request list
		#			700		ERROR	Invalid request. (Unknown error)
		#			701		ERROR	Host IP is Banned
		#			703		ERROR	Requested song ID invalid
		#			704		ERROR	Request limit reached: User can only request xx songs every 60 minutes
		#			708		ERROR	You have already requested this song.
		#
		#---------------------------------------------------------------------------------------------------------------
	
		try:
		
			# split the request into the "file name" and the "query string"
			fileStr, sepChar, queryStr = self.path.partition('?')
			
			if fileStr == '/req/':
			
				# get the form data
				form = cgi.parse_qs(self.rfile.read(int(self.headers.getheader('Content-Length'))))

				if not form:
					self.sendRequestError(700)
					return
				
				if form.has_key('songID') and form.has_key('host') and form['songID'] and form['host']:
					global requestCount
					
					songID = form['songID'][0]
					hostIP = form['host'][0]
					
					if form.has_key('requestedBy') and form['requestedBy']:
						requestedBy = form['requestedBy'][0]
					else:
						requestedBy = ''
						
					if form.has_key('dedication') and form['dedication']:
						dedication = form['dedication'][0]
					else:
						dedication = ''
					
					# is it a valid song?
					requestedSong = Library.getSong(songID)
					if requestedSong is None:
						self.sendRequestError(703)
						return
					
					# lookup in Hosts dict
					if not Hosts.has_key(hostIP):
						Hosts[hostIP] = { 'requests': [], 'banned': 0 }
					
					# is the host banned?
					if Hosts[hostIP]['banned']:
						self.sendRequestError(701)
						return
					
					curTime = time.time()
					oneHourAgo = curTime - (60 * 60)  # 1 hour = 60 minutes = 60 * 60 seconds
					tenMinAgo = curTime - (10 * 60)   # 10 mins = 10 * 60 seconds
					# check if the host request limit has been met:
					requestsInLastHour = 0
					requestedSongInLast10Minutes = 0
					for r in Hosts[hostIP]['requests']:
						if r['time'] >= oneHourAgo:
							requestsInLastHour += 1
							
						if r['time'] >= tenMinAgo:
							if r['songID'] == songID:
								requestedSongInLast10Minutes += 1
							
					if requestsInLastHour >= Config['maxRequests_User']:
						self.sendRequestError(704)
						return
						
					if requestedSongInLast10Minutes > 0:
						self.sendRequestError(708)
						return

					# check if the artist, album, or song limit been met:
					artistRequestsInLastHour = 0
					albumRequestsInLastHour = 0
					songRequestsInLastHour = 0
					for r in Requests:
						if r['info']['time'] >= oneHourAgo:
							thisSong = Library.getSong(r['info']['songID'])
							if not thisSong is None:
								if thisSong['artist'] == requestedSong['artist']:
									artistRequestsInLastHour += 1
								if thisSong['album'] == requestedSong['album']:
									albumRequestsInLastHour += 1
								if r['info']['songID'] == songID:
									songRequestsInLastHour += 1
							
					if songRequestsInLastHour >= Config['maxRequests_Song']:
						self.sendRequestError(601)
						return
					elif artistRequestsInLastHour >= Config['maxRequests_Artist']:
						self.sendRequestError(602)
						return
					elif albumRequestsInLastHour >= Config['maxRequests_Album']:
						self.sendRequestError(604)
						return
					
					# ok, all checks passed
					requestCount = requestCount + 1
					requestID = requestCount
					requestTime = long(time.time())
					
					# update Hosts list
					Hosts[hostIP]['requests'].append( {'id': requestID, 'songID': songID, 'time': requestTime } )
					
					# add request to Requests list
					Requests.append( { 'id': requestID, \
										'info': {	'songID': songID, 'time': requestTime, 'host': hostIP, \
													'requestedBy': requestedBy, 'dedication': dedication } } )

					# add to NewRequests list
					NewRequests.append( requestID )

					# send a response back in XML
					response = '''<?xml version="1.0" encoding="UTF-8"?>
								<request><application><apptype>MBRadio</apptype><version>1.0</version></application>
								<status><code>200</code><message>Request Received</message>
								<requestID>''' + str(requestID) + '</requestID></status>' + PackageSong(songID) + '</request>'

					self.send_response(200)
					self.send_header('Content-type', 'text/xml')
					self.end_headers()
					self.wfile.write(response)
					
					return
					
				#endif form.has_key('songID') and form.has_key('host') and form['songID'] and form['host']:
				
				# error fall-through
				self.sendRequestError(700)
				return
			
			#endif fileStr == '/req/'
			
		except :
			pass
			
	#enddef do_POST

#endclass MBRadio(BaseHTTPRequestHandler)

#----------------------------------------------------------------------------------------------------------------------#
#  Utility functions
#----------------------------------------------------------------------------------------------------------------------#
def PackageSonglist(songList, numResults, startingFrom):
	# packages a list of songs in XML for transmission
	# arugment(songList) should be a list of valid songID's from the library
	
	# sanitise the numResults & startingFrom
	if numResults is None or numResults < 0:
		numResults = 100
	if startingFrom is None or startingFrom < 0:
		startingFrom = 0
	elif startingFrom > len(songList):
		startingFrom = len(songList)
	
	endingAt = startingFrom + numResults
	if endingAt > len(songList):
		endingAt = len(songList)
	
	last = endingAt - 1
	if last < 0:
		last = 0
	
	# take the appropriate slice:
	slicedList = songList[startingFrom:endingAt]
	
	packageStr = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
					'<songlist count=\"' + str(len(slicedList)) + '\" ' + 'total=\"' + str(len(songList)) + '\" ' + \
					'first=\"' + str(startingFrom) + '\" ' + 'last=\"' + str(last) + '\"' + '>\n'
	
	for song in slicedList:
		packageStr = packageStr + PackageSong(song)
		
	packageStr = packageStr + '</songlist>'
	
	return packageStr
	
#enddef PackageSonglist

def PackageSong(songID):
	# packages the song info as an XML string
	
	song = Library.getSong(songID)
	if song is None:
		return ""
	
	packageStr = '\t<song id=\"' + str(songID) + '\">' + \
					'<artist>' + SafeXML(song['artist']) + '</artist>' + \
					'<title>' + SafeXML(song['title']) + '</title>' + \
					'<album>' + SafeXML(song['album']) + '</album>' + \
					'<genre>' + SafeXML(song['genre']) + '</genre>' + \
					'<duration>' +str(song['duration']) + '</duration></song>\n'

	return packageStr
	
#enddef PackageSong

def PackageRequest(requestID):
	# packages the request info as an XML string
	
	request = LookupRequest(requestID)
	if request is None:
		return ""
		
	packageStr = '\t<request id=\"' + str(requestID) + '\">' + \
					'<time>' + str(request['info']['time']) + '</time>' + \
					'<host>' + SafeXML(request['info']['host']) + '</host>' + \
					'<requestedby>' + SafeXML(request['info']['requestedBy']) + '</requestedby>' + \
					'<dedication>' + SafeXML(request['info']['dedication']) + '</dedication>' + \
					PackageSong(request['info']['songID']) + '</request>\n'

	return packageStr
	
#enddef PackageRequest

def LookupRequest(requestID):
	
	found = filter( lambda reqDict: reqDict['id'] == requestID, Requests)
	
	if found:
		return found[0]
	else:
		return None
	
#enddef LookupRequest

def SafeXML(theString):
	return cgi.escape(theString).encode('ascii', 'xmlcharrefreplace')
#enddef SafeXML

def SafeAscii(theString):
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
#enddef SafeAscii

def MakeSortingTuple(songID, sortBy):
	song = Library.getSong(songID)
	if song is None:
		return tuple(map(lambda x: None, range(len(sortBy)+1)))
	
	sortList=[]
	for field,dir in sortBy:
		try:
			if field == 'artist':
				sortList.append(SafeAscii(song['sortArtist']).lower())
			elif field == 'title':
				sortList.append(SafeAscii(song['sortTitle']).lower())
			elif field == 'album':
				sortList.append(SafeAscii(song['album']).lower())
			elif field == 'genre':
				sortList.append(SafeAscii(song['genre']).lower())
		except:
			pass
	sortList.append(songID)

	return tuple(sortList)

#enddef MakeSortingTuple

def SortSonglist(songList, sortBy):

	# make a list of tuples to correctly sort the songs
	songListToSort = map(lambda songID: MakeSortingTuple(songID, sortBy), songList)
	# sort!
	songListToSort.sort()
	# the songID is returned as the last item in the tuple
	sortedSongList = map(lambda tuple: tuple[len(tuple)-1], songListToSort)

	return sortedSongList
	
#enddef SortSonglist

#----------------------------------------------------------------------------------------------------------------------#
#  main()
#----------------------------------------------------------------------------------------------------------------------#
def main():
	
	#gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_OBJECTS | gc.DEBUG_COLLECTABLE )
	
	LoadConfig()
	
	try:
		server = HTTPServer(('', Config['Port']), MBRadio)
		Debug.out('Starting MBRadio Webserver')
		server.serve_forever()
		
	except KeyboardInterrupt:
		Debug.out('^C received, shutting down server')
		
		server.socket.close()
		

if __name__ == '__main__':
	main()