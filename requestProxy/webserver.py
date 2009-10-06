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

global Hosts, Requests, NewRequests, History
# Hosts dictionary - all remote hosts (users) that have made requests
#	Contents:
#		keys:		IP-address of host
#		values:		dict{ 'requests':	list[ dict{'id': (requestID), 'songID': (songID), 'time': (timestamp)}, ... ]
#					      'banned':		0 or 1 }
Hosts = {}

# Requests dictionary - all requests received by server
#	Contents:
#		keys:		requestID
#		values:		dict{ 'songID': (songID), 'time': (timestamp), 'host': (host IP),
#					      'requestedBy': (requestor), 'dedication': (dedication info) }
Requests = {}

# NewRequests list - requests waiting to be collected by the display program.
#	Contents:
#		list[ (requestID1), (requestID2), ... ]
NewRequests = []

# History list - list of songID's that have been played
#	Contents:
#		list[ (songID1, timestamp), (songID2, timestamp), ... ]
History = []

#----------------------------------------------------------------------------------------------------------------------#
#  Load configuration
#----------------------------------------------------------------------------------------------------------------------#
def LoadConfig():
	global Config
	
	# which Library DB to use?  Currently the only acceptable option is "iTunes"
	Config['Library'] = "iTunes"

	# port to which the HTTP request server binds
	Config['Port'] = 15800

	# directory for saving prefs and logs
	# *Jonathan* this may need to be changed on the Mac
	Config['AppDir'] = os.path.abspath(os.curdir)
	Config['LogDir'] = os.path.join(Config['AppDir'], "logs")

	# iTunes DB location   *Jonathan* this will need to be changed for Mac
	Config['iTunesDB'] = os.path.join(os.path.expanduser('~'), 'Music\iTunes\iTunes Music Library.xml')

	# Max requests are enforced on sliding hour-long timeframe
	Config['maxRequests_User'] = 10
	Config['maxRequests_Artist'] = 5
	Config['maxRequests_Album'] = 5
	Config['maxRequests_Song'] = 2
	
	# Only handle HTTP requests from the following IPs and/or hostnames
	# *Jonathan* I'm not sure how the localhost shows up on MacOS.
	# On windows, BaseHTTPRequestHandler.client_address[0] returns "127.0.0.1". May need to look into that.
	Config['AllowedClients'] =	[ '127.0.0.1', 'localhost', \
								  '67.205.28.237', 'bugsy.dreamhost.com' ]
	
#enddef LoadConfig

#----------------------------------------------------------------------------------------------------------------------#
#  Load music library
#----------------------------------------------------------------------------------------------------------------------#
def LoadLibrary():
	global Library
	
	Debug.out('Loading song database...')

	if Library:
		Library.reset()
		
	if Config['Library'] == "iTunes":
		Library = iTunesLibrary.iTunesLibrary()
		Library.load(Config['iTunesDB'])
	
#enddef LoadLibrary

#----------------------------------------------------------------------------------------------------------------------#
#  BaseHTTPServer implementation
#----------------------------------------------------------------------------------------------------------------------#

requestCount = 0

class MBRadio(BaseHTTPRequestHandler):
	
	def sendError(self, text = 'Server error', num = 500):
		self.send_response(num)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()
		self.wfile.write(text)
	#enddef sendError()
	
	def sendData(self, data, mimeType = 'text/plain', num = 200):
		self.send_response(num)
		self.send_header('Content-type', mimeType)
		self.end_headers()
		self.wfile.write(data)
	#enddef sendData()
	
	def do_GET(self):
			
		#---------------------------------------------------------------------------------------------------------------
		#  Acceptable GET parameters
		#  
		#  HTTP GET requests are received by the server in the format /command/?var1=value&var2=value....
		#---------------------------------------------------------------------------------------------------------------
		#
		#  Handled commands:
		#
		#	/new-requests
		#
		#		LOCALHOST ONLY
		#
		#		Command returns the current queue of song requests in XML format. Once the requests have been
		#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
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
		#	/now-playing
		#
		#		LOCALHOST ONLY
		#
		#		Command tells the proxy program what the currently playing song is. This is used to record the history
		#		of songs played on the radio. Needed because the website requests the currently playing song and 
		#		playlist history from this program through the /history/ command.
		#
		#		Query string parameters:
		#			PARAM		TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			songid=		string		Y		library ID of the song currently playing
		#
		#		Returns plain text:
		#			'OK'			song recorded into history
		#			'INVALID'		unable to find songID in the library
		#			'FAIL'			unknown error occured
		#
		#	/reload-library
		#
		#		LOCALHOST ONLY
		#
		#		Command instructs this program to reload the music library. This is necessary if the user adds new
		#		songs to their library while DJing. Note, it is not adviseable to simply monitor the 'modified time'
		#		of the iTunes XML file, since iTunes is constantly updating that file with other inconsequential data.
		#
		#		Query string parameters: (none)
		#
		#		Returns plain text:
		#			'OK'	reload succeeded
		#			'FAIL'	unknown error occured
		#
		#	/reload-config
		#
		#		LOCALHOST ONLY
		#
		#		Command instructs this program to reload the config file. This is necessary if the user changes config
		#		options like "max requests per user per hour", etc.
		#
		#		Query string parameters: (none)
		#
		#		Returns plain text:
		#			'OK'	reload succeeded
		#			'FAIL'	unknown error occured
		#
		#	/search
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
		#	/requests
		#
		#		This interface is used to get a list of recent requests to display on the website.
		#		Requests are always returned in descending order by the time the request was made.
		#
		#		Query string parameters:
		#			PARAM		TYPE			REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			results=	string|integer	Y		if results=='all', returns all requests
		#												if results==X, where X is an integer, returns the most recent X
		#													requests made to the server
		#			compress=	string	 		N		If compress == "", don't compress.
		#												If compress == "gzip", return results gzip'ed
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
		#	/history
		#
		#		This interface is used to get a list of recently played songs to display on the website.
		#		History results are always returned in descending order by the time the song was played.
		#
		#		Query string parameters:
		#			PARAM		TYPE			REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			results=	string|integer	Y		if results=='all', returns all requests
		#												if results==X, where X is an integer, returns the most recent X
		#													requests made to the server
		#			compress=	string	 		N		If compress == "", don't compress.
		#												If compress == "gzip", return results gzip'ed
		#
		#		Returns XML of the form: 
		#			<historylist count="(count)">
		#				<played time="(time)">
		#					<song id="(songID)">
		#						<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#					</song>
		#				</played>
		#				...
		#			</historylist>
		#
		#	/time
		#
		#		Returns the local time on the DJ's computer. Needed for certain things on the server.
		#
		#		Query string parameters: (none)
		#
		#		Returns XML of the form:
		#			<time>(current local time)</time>
		#
		#---------------------------------------------------------------------------------------------------------------
		
		# is the client in the list of allowed clients?
		if not (self.client_address[0] in Config['AllowedClients'] \
				or self.address_string() in Config['AllowedClients']):
			self.sendError('Unauthorized')
			return
		
		# split the request into the "file name" and the "query string"
		command, sepChar, queryStr = self.path.partition('?')
		
		if command.endswith('/'):
			command = command[0:len(command)-1]
		
		# parse the query string 
		args = urlparse.parse_qs(queryStr)
				
		#try:
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/search'
		#-----------------------------------------------------------------------------------------------------------
		if command == '/search':

			if not args or not args.has_key('by') or not args.has_key('for') or not args['by'] or not args['for']:
				self.sendError('Incomple search parameters: /search/?for=X&by=Y required')
				return
			
			searchBy = args['by'][0].lower()

			if not searchBy in ['letter','artist','title','genre','any']:
				self.sendError('Unknown search parameter by=' + searchBy)
				return
				
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
				terms = filter(lambda triplet: triplet[0] in ['artist','title','album','genre'], terms)
				
				# remove duplicates, fill in empty sort directions
				for field, dummy, dir in terms:
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
				
			if resultSet is None:
				self.sendError('Search error occurred')
				return

			# sort the results
			resultSet = SortSonglist(resultSet,sortBy)
			
			# packages the results as XML
			packagedResults = PackageSonglist(resultSet, numResults, startingFrom)
			contentType = 'text/xml'
			
			# gzip the results?
			if args.has_key('compress') and args['compress']:
				if args['compress'][0].lower() == 'gzip':
					contentType = 'application/x-gzip'
					packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)
			
			gc.collect()
				
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/new-requests'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/new-requests':
			global NewRequests
			
			# only answer requests from the localhost
			if self.client_address[0] != '127.0.0.1':
				self.sendError('Unauthorized')
				return
			
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
			self.sendData(packageStr, 'text/xml')
			
			# clear the list?
			if clear == 'yes':
				NewRequests = []
				
			gc.collect()
			
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/now-playing'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/now-playing':
			
			# only answer requests from the localhost
			if self.client_address[0] != '127.0.0.1':
				self.sendError('Unauthorized')
				return

			if args is None or not args.has_key('songid') or not args['songid']:
				self.sendError('Incomple query parameters: /now-playing?songid=X required')
				return
					
			try:
				songID = args['songid'][0]
				
				song = Library.getSong(songID)
				if song is None:
					self.sendData('INVALID')
				
				theTime = long(time.time())
				
				# append if it's not already in the list
				if not filter(lambda pair: pair[0]==songID, History):
					History.append( (songID, theTime) )
					LogSong(songID, theTime)
				
				self.sendData('OK')
				
			except:
				self.sendData('FAIL')
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/requests'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/requests':
			
			if args is None or not args.has_key('results') or not args['results']:
				self.sendError('Incomple query parameters')
				return
			
			# sort requests by timestamp desc:
			requestList = map(lambda (reqID,reqInfo): (reqInfo['time'], reqID), Requests.items())
			requestList.sort()
			requestList.reverse()
			requestList = map(lambda pair: pair[1], requestList)
				
			if args['results'][0] == 'all':
				numResults = len(requestList)
			else:
				numResults = int(args['results'][0])
				if numResults <= 0:
					numResults = 10
				if numResults > len(requestList):
					numResults = len(requestList)
			
			# take the slice:
			slicedRequestList = requestList[0:numResults]
			
			# package the requests as XML
			contentType = 'text/xml'
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<requestlist count=\"' + str(len(slicedRequestList)) + '\">\n'

			for requestID in slicedRequestList:
				packagedResults = packagedResults + PackageRequest(requestID)
				
			packagedResults = packagedResults + '</requestlist>'
			
			# gzip the results?
			if args.has_key('compress') and args['compress']:
				if args['compress'][0].lower() == 'gzip':
					contentType = 'application/x-gzip'
					packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)
			
			gc.collect()
			
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/time'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/time':
		
			self.sendData('<time>' + time.ctime() + '</time>', 'text/xml')
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/reload-library'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/reload-library':
			# only answer requests from the localhost
			if self.client_address[0] != '127.0.0.1':
				self.sendError('Unauthorized')
				return
			
			try:
				LoadLibrary()
				self.sendData('OK')
			except:
				self.sendData('FAIL')

		#-----------------------------------------------------------------------------------------------------------
		#  command == '/reload-config'
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/reload-config':
			# only answer requests from the localhost
			if self.client_address[0] != '127.0.0.1':
				self.sendError('Unauthorized')
				return
				
			try:
				LoadConfig()
				self.sendData('OK')
			except:
				self.sendData('FAIL')
		
		
		#-----------------------------------------------------------------------------------------------------------
		#  command unknown!
		#-----------------------------------------------------------------------------------------------------------
		else:
			self.sendError('Unknown command', 404)
			
		#except:
		#	self.sendError('Unknown server error')
			
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

		self.sendData(response, 'text/xml')
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
		#	/req
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
			command, sepChar, queryStr = self.path.partition('?')
			
			if command.endswith('/'):
				command = command[0:len(command)-1]
			
			# get the form data
			form = cgi.parse_qs(self.rfile.read(int(self.headers.getheader('Content-Length'))))
			
			if command == '/req':

				if not form or not form.has_key('songID') or not form.has_key('host') or not form['songID'] or not form['host']:
					self.sendRequestError(700)
					return
					
				global requestCount
				
				songID = form['songID'][0]
				hostIP = form['host'][0]
				
				if form.has_key('requestedBy') and form['requestedBy']:
					requestedBy = form['requestedBy'][0].strip()
				else:
					requestedBy = ''
					
				if form.has_key('dedication') and form['dedication']:
					dedication = form['dedication'][0].strip()
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
				for reqInfo in Requests.values():
					if reqInfo['time'] >= oneHourAgo:
						thisSong = Library.getSong(reqInfo['songID'])
						if not thisSong is None:
							if thisSong['artist'] == requestedSong['artist']:
								artistRequestsInLastHour += 1
							if thisSong['album'] == requestedSong['album']:
								albumRequestsInLastHour += 1
							if reqInfo['songID'] == songID:
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
				Requests[requestID] = dict( { 'songID': songID, 'time': requestTime, 'host': hostIP, \
												'requestedBy': requestedBy, 'dedication': dedication } )

				# add to NewRequests list
				NewRequests.append( requestID )
				
				# log the request
				LogRequest(requestID)

				# send a response back in XML
				response = '''<?xml version="1.0" encoding="UTF-8"?>
							<request><application><apptype>MBRadio</apptype><version>1.0</version></application>
							<status><code>200</code><message>Request Received</message>
							<requestID>''' + str(requestID) + '</requestID></status>' + PackageSong(songID) + '</request>'
				
				self.sendData(response, 'text/xml')
				return
			
			#endif command == '/req'
			
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
	
	if not Requests.has_key(requestID):
		return ""
	
	reqInfo = Requests[requestID]
	if reqInfo is None:
		return ""
	
	packageStr = 	'\t<request id=\"' + str(requestID) + '\">' + \
					'<time>' + str(reqInfo['time']) + '</time>' + \
					'<host>' + SafeXML(reqInfo['host']) + '</host>' + \
					'<requestedby>' + SafeXML(reqInfo['requestedBy']) + '</requestedby>' + \
					'<dedication>' + SafeXML(reqInfo['dedication']) + '</dedication>' + \
					PackageSong(reqInfo['songID']) + '</request>\n'

	return packageStr
	
#enddef PackageRequest

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

def LogRequest(requestID):
	
	if not Requests.has_key(requestID):
		return
		
	reqInfo = Requests[requestID]
	if reqInfo is None:
		return
	
	song = Library.getSong(reqInfo['songID'])
	if song is None:
		return
	
	# make sure the log file and logs directory exist:
	try:
		if not os.path.exists(Config['LogDir']):
			os.mkdir(Config['LogDir'])

		requestLogFile = os.path.join(Config['LogDir'], "requests.xml")
		
		if not os.path.isfile(requestLogFile):
			f = open(requestLogFile, 'w')
			f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
			f.write("<requestlog>\n") 
			f.write("</requestlog>\n")
			f.close()
	except:
		Debug.out("Request log file does not exist, or file could not be created.")
		return
		
	# make the log entry as XML
	requestXML =	'<request>' + \
					'<time>' + str(reqInfo['time']) + '</time>' + \
					'<host>' + SafeXML(reqInfo['host']) + '</host>' + \
					'<requestedby>' + SafeXML(reqInfo['requestedBy']) + '</requestedby>' + \
					'<dedication>' + SafeXML(reqInfo['dedication']) + '</dedication>'
					
	songXML = 		'<song>' + \
					'<artist>' + SafeXML(song['artist']) + '</artist>' + \
					'<title>' + SafeXML(song['title']) + '</title>' + \
					'<album>' + SafeXML(song['album']) + '</album>' + \
					'<genre>' + SafeXML(song['genre']) + '</genre>' + \
					'</song>'
					
	requestXML +=	songXML + '</request>'
	
	# write the log entry to the file
	try:
		# get current logfile contents:
		f = open(requestLogFile, 'r')
		logLines = f.readlines()
		f.close()

		f = open(requestLogFile, 'w')
		for i, line in enumerate(logLines):
			# print the new request when i == 2
			#	(when i==0, line should be "<?xml ... ?>", when i==1, line should be "<requestlog>")
			if i == 2:
				f.write(requestXML + '\n')
			f.write(line.strip() + '\n')
			
		f.close()
	except:
		Debug.out("Failed to write request to log file")
	
	gc.collect()

#enddef LogRequest

def LogSong(songID, timePlayed):

	song = Library.getSong(songID)
	if song is None:
		return
	
	# make sure the log file and logs directory exist:
	try:
		if not os.path.exists(Config['LogDir']):
			os.mkdir(Config['LogDir'])

		playedLogFile = os.path.join(Config['LogDir'], "played.xml")
		
		if not os.path.isfile(playedLogFile):
			f = open(playedLogFile, 'w')
			f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
			f.write("<historylog>\n") 
			f.write("</historylog>\n")
			f.close()
	except:
		Debug.out("Played log file does not exist, or file could not be created.")
		return
		
	# make the log entry as XML
	playedXML =		'<played time=\"' + str(timePlayed) + '\">'
					
	songXML = 		'<song>' + \
					'<artist>' + SafeXML(song['artist']) + '</artist>' + \
					'<title>' + SafeXML(song['title']) + '</title>' + \
					'<album>' + SafeXML(song['album']) + '</album>' + \
					'<genre>' + SafeXML(song['genre']) + '</genre>' + \
					'</song>'
					
	playedXML +=	songXML + '</played>'
	
	# write the log entry to the file
	try:
		# get current logfile contents:
		f = open(playedLogFile, 'r')
		logLines = f.readlines()
		f.close()

		f = open(playedLogFile, 'w')
		for i, line in enumerate(logLines):
			# print the new request when i == 2
			#	(when i==0, line should be "<?xml ... ?>", when i==1, line should be "<historylog>")
			if i == 2:
				f.write(playedXML + '\n')
			f.write(line.strip() + '\n')
			
		f.close()
	except:
		Debug.out("Failed to write song to play history file")
	
	gc.collect()

#enddef LogSong

#----------------------------------------------------------------------------------------------------------------------#
#  main()
#----------------------------------------------------------------------------------------------------------------------#
def main():
	
	#gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_OBJECTS | gc.DEBUG_COLLECTABLE )
	
	LoadConfig()
	LoadLibrary()
	
	try:
		server = HTTPServer(('', Config['Port']), MBRadio)
		Debug.out('Starting MBRadio Webserver')
		server.serve_forever()
		
	except KeyboardInterrupt:
		Debug.out('^C received, shutting down server')
		
		server.socket.close()
		

if __name__ == '__main__':
	main()