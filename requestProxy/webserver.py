#	vim: set tabstop=4 columns=120 shiftwidth=4:
#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	webserver.py
#	
#	Implements the HTTP Request Server
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#
#----------------------------------------------------------------------------------------------------------------------#

# python library imports
import os.path, string, unicodedata, time, os, sys, cgi, gc, urlparse, zlib
import BaseHTTPServer

# local imports
import iTunesLibrary, Statistics, Debug

#----------------------------------------------------------------------------------------------------------------------#
#  Globals
#----------------------------------------------------------------------------------------------------------------------#

# Music library (instance of MusicLibrary class)
Library = None

# Config dictionary
Config = {}

# Song-play history stats
PlayStats = Statistics.PlayedStatistics()

# Request history stats
RequestStats = Statistics.RequestStatistics()

# Hosts dictionary - all remote hosts (users) that have made requests
#	Contents:
#		keys:		IP-address of host
#		values:		dict{ 'requests':	list[ dict{'id': (requestID), 'songID': (songID), 'time': (timestamp)}, ... ]
#					      'banned':		0 or 1 }
Hosts = {}

# Requests dictionary - all requests received by server
#	Contents:
#		keys:		requestID
#		values:		dict{ 'songID': (songID), 'time': (timestamp), 'host': (host IP), 'status': (waiting|played|queued), 
#					      'requestedBy': (requestor), 'dedication': (dedication info) }
Requests = {}

# RequestCount is used to generate the request ID. Incremented with each new request.
RequestCount = 0

# NewRequests list - requests waiting to be collected by the display program.
#	Contents:
#		list[ (requestID1), (requestID2), ... ]
NewRequests = []

# History list - list of songID's that have been played
#	Contents:
#		list[ (timestamp, songID1, requestID1), (timestamp, songID2, requestID2), ... ]
History = []

# SongQueue list - list of songID's in the queue to be played next
#	Contents:
#		list[ (songID1, requestID1), (songID2, requestID2), ... ]
SongQueue = []

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

newlinestripper = string.maketrans('\n\r\f','   ')

class MBRadio(BaseHTTPServer.BaseHTTPRequestHandler):
	
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
		#  Handled commands			Used				Type
		#  -----------------------------------------------------------
		#	/new-requests			Locally				Query
		#	/now-playing			Locally				Set
		#	/coming-up				Locally				Set
		#	/reload-library			Locally				Action
		#	/set-config				Locally				Set
		#	/terminate				Locally				Action
		#	/song					Local / Remote		Query
		#	/search					Remote webserver	Query
		#	/requests				Remote webserver	Query
		#	/queue					Remote webserver	Query
		#	/history				Remote webserver	Query
		#	/stats-top				Remote webserver	Query
		#	/time					Remote webserver	Query
		#---------------------------------------------------------------------------------------------------------------
		
		# is the client in the list of allowed clients?
		if not self.client_address[0] in Config['AllowedClients'] \
					and not self.address_string() in Config['AllowedClients']:
			self.sendError('Unauthorized', 401)
			return
		
		# split the request into the "file name" and the "query string"
		command, sepChar, queryStr = self.path.partition('?')
		if command.endswith('/'):
			command = command[0:len(command)-1]
		
		# parse the query string 
		args = urlparse.parse_qs(queryStr)
				
		#try:
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/new-requests'     - LOCALHOST ONLY -
		#
		#	Command returns the current queue of song requests in XML format. Once the requests have been
		#	retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
		#
		#	Query string parameters:
		#		PARAM		TYPE		REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		clear=		string		N		must be one of [yes|no]  (defaults to 'yes')
		#		order=		string		N		must be one of [newest|oldest]  (defaults to 'newest')
		#
		#	Returns XML of the form:
		#		<requestlist count="(count)">
		#			<request id="(requestID)">
		#				<time></time><host></host><requestedby></requestedby><dedication></dedication><status></status>
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#			</request>
		#			...
		#		</requestlist>
		#-----------------------------------------------------------------------------------------------------------
		if command == '/new-requests':
			global NewRequests
			
			# only answer requests from the localhost
			if self.client_address[0] != Config['LocalHost']:
				self.sendError('Unauthorized', 401)
				return
			
			clear = 'yes'
			try:
				if args['clear'][0] in ('yes','no'):
					clear = args['clear'][0]
			except LookupError:
				pass
			
			order = 'newest'
			try:
				if args['order'][0] in ('newest', 'oldest'):
					order = args['order'][0]
			except LookupError:
				pass
			
			orderedRequests = list(NewRequests)
			if order == 'newest':
				orderedRequests.reverse()

			# package new requests as XML
			packageStr =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
							'<requestlist count=\"' + str(len(orderedRequests)) + '\">\n' + \
							string.join(map(PackageRequest, orderedRequests), '\n') + \
							'</requestlist>'
			
			# send it back
			self.sendData(packageStr, 'text/xml')
			
			# clear the list?
			if clear == 'yes':
				NewRequests = []
			
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/now-playing'      - LOCALHOST ONLY -
		#
		#	Tells the proxy program what the currently playing song is. This is used to record the history
		#	of songs played on the radio. Needed because the website requests the currently playing song and 
		#	playlist history from this program through the /history/ command.
		#
		#	Query string parameters:
		#		PARAM		TYPE		REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		songid=		string		Y		library ID of the song currently playing
		#
		#	Returns plain text:
		#		'OK'			song recorded into history
		#		'INVALID'		unable to find songID in the library
		#		'DUPLICATE'		song is already the most recently reported 'now playing' song
		#		'FAIL'			unknown error occured
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/now-playing':
			
			# only answer requests from the localhost
			if self.client_address[0] != Config['LocalHost']:
				self.sendError('Unauthorized', 401)
				return
			
			if args is None or not args.has_key('songid') or not args['songid']:
				self.sendError('Incomple query parameters: /now-playing?songid=X required')
				return
			
			try:
				songID = args['songid'][0]
				
				thisSong = Library.getSong(songID)
				if not thisSong:
					self.sendData('INVALID')
					return

				# check that it's not already the most recent item in the list:
				try:
					if History[-1][1] == songID:
						self.sendData('DUPLICATE')
						return
				except LookupError:
					pass
				
				# let's assume that if there is a request for this songID sometime in the last 20 minutes, that
				# this song was 'fulfilling' that request.
				twentyMinAgo = time.time() - (20 * 60)   # 20 mins = 20 * 60 seconds
				
				foundReq = [reqID for (reqID, req) in Requests.items() \
								if req['songID'] == songID and req['time'] >= twentyMinAgo \
									and req['status'] != 'played']
				try:
					requestID = foundReq[0]
					Requests[requestID]['status'] = 'played'
				except LookupError:
					requestID = None
				
				theTime = long(time.time())
				History.append( (theTime, songID, requestID) )
				LogSong(theTime, songID, requestID)
				PlayStats.addSong({'songID': songID, 'artist':thisSong['artist'], 'title':thisSong['title'],
										'genre':thisSong['genre'], 'time':theTime})
										
				self.sendData('OK')
				
			except:
				self.sendData('FAIL')
				
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/coming-up'      - LOCALHOST ONLY -
		#
		#	Tells the proxy program what the next few songs in the playlist queue are.
		#
		#	Query string parameters:
		#		PARAM		TYPE		REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		songX=		string		Y		library ID of song number X in the queue. X = 1, 2, 3, ...
		#
		#	Returns plain text:
		#		'OK'			song recorded into history
		#		'INVALID'		one or more of the specified song id's is invalid
		#		'FAIL'			unknown error occured
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/coming-up':
			global SongQueue
			
			# only answer requests from the localhost
			if self.client_address[0] != Config['LocalHost']:
				self.sendError('Unauthorized', 401)
				return
			
			if args is None:
				self.sendError('Incomple query parameters')
				return
			
			try:
				queueList = []
				invalidSongIDs = []
				for x in range(1,5):
					try:
						songX = 'song' + str(x)
						songID = args[songX][0]
					except LookupError:
						break
					
					if Library.songExists(songID):
					
						# let's assume that if there is a request for this songID sometime in the last 20 minutes, that
						# this song was 'fulfilling' that request.
						twentyMinAgo = time.time() - (20 * 60)   # 20 mins = 20 * 60 seconds
						try:
							foundReq = [reqID for (reqID, req) in Requests.items() \
												if req['songID'] == songID and req['time'] >= twentyMinAgo \
													and req['status'] != 'played']
							requestID = foundReq[0]
							Requests[requestID]['status'] = 'queued'
						except:
							requestID = None
					
						queueList.append( (songID, requestID) )
						
					else:
						invalidSongIDs.append(songX + '=' + songID)
					
				SongQueue = queueList
				
				if invalidSongIDs:
					self.sendData('INVALID\n' + string.join(invalidSongIDs,'\n'))
				else:
					self.sendData('OK')
				
			except:
				self.sendData('FAIL')
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/reload-library'      - LOCALHOST ONLY -
		#
		#	Instructs this program to reload the music library. This is necessary if the user adds new
		#	songs to their library while DJing. Note, it is not adviseable to simply monitor the 'modified time'
		#	of the iTunes XML file, since iTunes is constantly updating that file with other inconsequential data.
		#
		#	Query string parameters: (none)
		#
		#	Returns plain text:
		#		'OK'	reload succeeded
		#		'FAIL'	unknown error occured
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/reload-library':
			# only answer requests from the localhost
			if self.client_address[0] != Config['LocalHost']:
				self.sendError('Unauthorized', 401)
				return
			
			try:
				LoadLibrary()
				self.sendData('OK')
			except:
				self.sendData('FAIL')
				
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/set-config'      - LOCALHOST ONLY -
		#
		#	Instructs this program to update a config option.
		#
		#	Query string parameters:
		#		Given a query string in the format 'configOpt1=value1&configOpt2=value2...'
		#		'configOptX' must be a valid entry in the Config dict
		#			For each 'configOptX=valueX' pair specified, the following command is issued:
		#				Config[configOptX] = valueX
		#			If 'valueX' appears to be a number (isnumeric() returns true) it will be converted into a long
		#
		#		Example:  /set-config?maxRequests_User=20&maxRequests_Artist=10
		#		Example:  /set-config?iTunesDB=/some/new/path/iTunes Music Library.xml
		#
		#		NOTE! No other checking is done to make sure the value set is of the right type or makes any sense
		#		      for the specified config option. This interface is something of a hack - use it correctly and
		#		      everything should be fine :)
		#
		#	Returns plain text:
		#		'OK'		config option changed
		#		'INVALID'	invalid entry in Config dict
		#		'FAIL'		unknown error occured
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/set-config':
			# only answer requests from the localhost
			if self.client_address[0] != Config['LocalHost']:
				self.sendError('Unauthorized', 401)
				return
				
			try:
				for configOpt in args.keys():
					if not Config.has_key(configOpt):
						self.sendData('INVALID')
						return
	
					val = args[configOpt][0]
					try:
						valUCStr = unicode(val)
						if valUCStr.isnumeric():
							val = long(valUCStr)
					except ValueError:
						pass
					
					Config[configOpt] = val
					Debug.out("Set config opt:", configOpt,"=",val)
				#endfor
				
				self.sendData('OK')
				
			except:
				self.sendData('FAIL')
				
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/terminate'      - LOCALHOST ONLY -
		#
		#	Instructs this program to terminate the webserver
		#
		#	Query string parameters: none
		#
		#	Returns: nothing
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/terminate':
		
			sys.exit()
			
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/song'
		#
		#	This interface is used to get information about a specific song.
		#
		#	Query string parameters:
		#		PARAM		TYPE			REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		songid=		string			Y		ID of song to retrieve
		#		stats=		string			N		if stats == "yes", send additional information about the song
		#		compress=	string	 		N		If compress == "", don't compress.
		#											If compress == "gzip", return results gzip'ed
		#
		#	Returns:
		#		<songinfo>
		#			<song id="(songID)">
		#				<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#			</song>
		#		[ optional: included if stats=='yes' ]
		#			<stats>
		#				<lastplayed>(timestamp|'none')</lastplayed>
		#				<lastrequested>(timestamp|'none')</lastrequested>
		#				<queued>('yes'|'no')</queued>
		#			</stats>
		#		[ /optional ]
		#		</songinfo>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/song':
			
			if args is None or not args.has_key('songid') or not args['songid']:
				self.sendError('Incomple query parameters:  /song?songid=X  required')
				return
				
			songID = args['songid'][0]
	
			if not Library.songExists(songID):
				self.sendError('INVALID')
				return
				
			includeStats = 'no'
			try:
				includeStats = args['stats'][0]
			except LookupError:
				pass
			
			# package the information
			packageList =	['<?xml version="1.0" encoding="UTF-8"?>\n',
								'<songinfo>',
								PackageSong(songID)]
			
			if includeStats == 'yes':
				packageList.append('<stats>')
				
				# find last play?
				lastplay = PlayStats.getMostRecentBy_SongID(songID)
				if lastplay:
					packageList.extend(['<lastplayed>', str(lastplay), '</lastplayed>'])
				else:
					packageList.append('<lastplayed>none</lastplayed>')
					
				# find last play?
				lastreq = RequestStats.getMostRecentBy_SongID(songID)
				if lastreq:
					packageList.extend(['<lastrequested>', str(lastreq), '</lastrequested>'])
				else:
					packageList.append('<lastrequested>none</lastrequested>')
				
				# find in SongQueue?
				found = [id for (id, dummy) in SongQueue if id == songID]
				if found:
					packageList.append('<queued>yes</queued>')
				else:
					packageList.append('<queued>no</queued>')
					
				packageList.append('</stats>')
				
			packageList.append('</songinfo>')
			
			contentType = 'text/xml'
			packagedResults = string.join(packageList, '')
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)
		
				
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/search'
		#
		#	This interface is used to search the library for songs. This request is only sent from the
		#	radio station website to get the tracklist to allow users to request songs. It returns a list of
		#	songs in XML format.
		#
		#	Query string parameters:
		#		PARAM		TYPE	REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		for=		string	 Y		a string literal to search for
		#		by=			string	 Y		must be one of [letter|artist|title|genre|any]
		#		sort=		string	 N		Must be a list in the format "field1-direction,field2-direction..."
		#
		#									field is one of (artist|title|album|genre)
		#									direction is one of (asc|desc) - if unspecified, defaults to asc
		#
		#									If sort == "", defaults to "artist-asc,title-asc"
		#									If sort == "genre-[dir]", defaults to "genre-[dir],artist-asc,title-asc"
		#									If sort != "", and does not include 'title', then the sort will
		#										always be appended with sort+=",title-asc"
		#
		#									NOTE! At this time my implementation ignores the sort direction 
		#										  directive until I can write some better sorting code. All sorts
		#									      will be done ascending until then.
		#
		#		results=	integer	 N		the number of results to return  (defaults to 100)
		#		starting=	integer	 N		For continuation of search results, return songs starting at
		#										result #X (defaults to 0)
		#		compress=	string	 N		If compress == "", don't compress.
		#									If compress == "gzip", return results gzip'ed
		#
		#	Returns XML of the form:
		#		<songlist count="(count)" total="(all songs found)" first="(first result)" last="(last result)">
		#			<song id="(songID)">
		#				<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#			</song>
		#			...
		#		</songlist>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/search':

			if not args or not args.has_key('by') or not args.has_key('for') or not args['by'] or not args['for']:
				self.sendError('Incomple query parameters: /search/?for=X&by=Y required')
				return
			
			searchBy = args['by'][0].lower()
			searchFor = args['for'][0]
			
			if not searchBy in ('letter','artist','title','genre','any'):
				self.sendError('Unknown search parameter by=' + searchBy)
				return
			
			try:
				numResults = int(args['results'][0])
				if numResults < 0:
					numResults = 100
			except (LookupError, ValueError):
				numResults = 100
				
			try:
				startingFrom = int(args['starting'][0])
				if startingFrom < 0:
					startingFrom = 0
			except (LookupError, ValueError):
				startingFrom = 0
			
			# convert sort string "field1-dir,field2-dir..." to list: [(field1,dir), (field2,dir), ...]
			sortBy = []
			if args.has_key('sort') and args['sort']:
				terms = [term.strip().partition('-') for term in args['sort'][0].lower().split(',')]
				terms = [(field,dir) for (field,dummy,dir) in terms if field in ('artist','title','album','genre')]
				
				# remove duplicates, fill in empty sort directions
				for field, dir in terms:
					if not field in [f for (f,d) in sortBy]:
						if dir in ('asc','desc'):
							sortBy.append( (field,dir) )
						else:
							sortBy.append( (field,'asc') )
			
			if not sortBy:
				sortBy = [('artist','asc'), ('title', 'asc')]
			else:
				if len(sortBy) == 1 and sortBy[0][0] == 'genre':
					sortBy.extend( [('artist', 'asc'), ('title', 'asc')] )
				if not 'title' in [f for (f,d) in sortBy]:
					sortBy.append( ('title', 'asc') )
			
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

			# make a list of tuples to correctly sort the songs
			t1 = time.time()
			songListToSort = [MakeSortingTuple(songID, sortBy) for songID in resultSet]
			songListToSort.sort()
			# the songID is returned as the last item in the tuple
			sortedSongList = [tuple[-1] for tuple in songListToSort]
			
			Debug.out("  Sorted", len(sortedSongList),"in", round(time.time()-t1,6), "seconds")
			
			# sanitise the numResults & startingFrom
			if startingFrom > len(sortedSongList):
				startingFrom = len(sortedSongList)
			
			endingAt = startingFrom + numResults
			if endingAt > len(sortedSongList):
				endingAt = len(sortedSongList)
			
			last = endingAt - 1
			if last < startingFrom:
				last = startingFrom
			
			# take the appropriate slice:
			slicedList = sortedSongList[startingFrom:endingAt]
			
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<songlist count=\"' + str(len(slicedList)) + '\" ' + \
									'total=\"' + str(len(sortedSongList)) + '\" ' + \
									'first=\"' + str(startingFrom) + '\" ' + 'last=\"' + str(last) + '\"' + '>\n' + \
								string.join(map(PackageSong, slicedList), '\n') + \
								'</songlist>'
			contentType = 'text/xml'
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)

		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/requests'
		#
		#	This interface is used to get a list of recent requests to display on the website.
		#	Requests are always returned in descending order by the time the request was made.
		#
		#	Query string parameters:
		#		PARAM		TYPE			REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		results=	string|integer	Y		if results=='all', returns all requests
		#											if results==X, where X is an integer, returns the most recent X
		#												requests made to the server
		#
		#		status=		string			N		if status=='s1[,s2[,...]]'  where s in (waiting|queued|played)
		#												returns those requests with the specified status
		#											if status is empty, returns all requests
		#
		#		compress=	string	 		N		If compress == "", don't compress.
		#											If compress == "gzip", return results gzip'ed
		#
		#	Returns XML of the form: 
		#		<requestlist count="(count)">
		#			<request id="(requestID)">
		#				<time></time><host></host><requestedby></requestedby><dedication></dedication><status></status>
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#			</request>
		#			...
		#		</requestlist>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/requests':
			
			if args is None or not args.has_key('results') or not args['results']:
				self.sendError('Incomple query parameters:  /requests?results=X  required')
				return
			
			# status string "type1,type2,..." to list: [type1,type2,...]
			filterStatus = None
			if args.has_key('status') and args['status']:
				filterStatus = [term for term in args['status'][0].lower().split(',') \
										if term in ('played','queued','waiting')]

			if filterStatus:
				requestList = [(info['time'], reqID) for (reqID,info) in Requests.items()
									if info['status'] in filterStatus]
			else:
				requestList = [(info['time'], reqID) for (reqID,info) in Requests.items()]
			
			# sort requests by timestamp desc:
			requestList.sort()
			requestList.reverse()
			requestList = [pair[1] for pair in requestList]
				
			if args['results'][0] == 'all':
				numResults = len(requestList)
			else:
				try:
					numResults = int(args['results'][0])
				except ValueError:
					numResults = 10
				
				if numResults <= 0:
					numResults = 10
			
			# take the slice:
			slicedRequestList = requestList[0:numResults]
			
			# package the requests as XML
			contentType = 'text/xml'
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<requestlist count=\"' + str(len(slicedRequestList)) + '\">\n' + \
								string.join(map(PackageRequest, slicedRequestList), '\n') + \
								'</requestlist>'
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)

		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/history'
		#
		#	This interface is used to get a list of recently played songs to display on the website.
		#	History results are always returned in descending order by the time the song was played.
		#
		#	Query string parameters:
		#		PARAM		TYPE			REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		results=	integer			Y		if results==X, where X is an integer, returns the most recent X
		#												songs in the history list
		#		compress=	string	 		N		If compress == "", don't compress.
		#											If compress == "gzip", return results gzip'ed
		#
		#	Returns XML of the form: 
		#		<historylist count="(count)">
		#			<played time="(time)">
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#			[ optional: ]
		#				<requested>
		#					<time></time><host></host><requestedby></requestedby><dedication></dedication><status></status>
		#				</requested>
		#			[ end optional ]
		#			</played>
		#			...
		#		</historylist>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/history':
		
			if args is None or not args.has_key('results') or not args['results']:
				self.sendError('Incomple query parameters: /history?results=X required')
				return
			
			# make a copy of the history list, then reverse it
			historyList = list(History)
			historyList.reverse()
			
			try:
				numResults = int(args['results'][0])
			except ValueError:
				numResults = 1
			if numResults <= 0:
				numResults = 1
			
			# take the slice:
			slicedHistoryList = historyList[0:numResults]
			
			# package the song list as XML
			contentType = 'text/xml'
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<historylist count="' + str(len(slicedHistoryList)) + '">\n' + \
								string.join([PackageHistoryItem(timestamp, songID, reqID) \
												for (timestamp, songID, reqID) in slicedHistoryList], '\n') + \
								'</historylist>'
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)
		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/queue'
		#
		#	This interface is used to get a list of upcoming (queued) songs.
		#
		#	Query string parameters:
		#		PARAM		TYPE			REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		compress=	string	 		N		If compress == "", don't compress.
		#											If compress == "gzip", return results gzip'ed
		#
		#	Returns XML of the form: 
		#		<queuelist count="(count)">
		#			<queued>
		#				<song id="(songID)">
		#					<artist></artist><title></title><album></album><genre></genre><duration></duration>
		#				</song>
		#			[ optional: ]
		#				<requested>
		#					<time></time><host></host><requestedby></requestedby><dedication></dedication><status></status>
		#				</requested>
		#			[ end optional ]
		#			</queued>
		#			...
		#		</queuelist>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/queue':

			# package the queue list as XML
			contentType = 'text/xml'
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<queuelist count="' + str(len(SongQueue)) + '">\n' + \
								string.join([PackageQueueItem(songID, reqID) \
												for (songID, reqID) in SongQueue], '\n') + \
								'</queuelist>'
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)

		
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/stats-top'
		#
		#	This interface is used to get a list of recently played songs to display on the website.
		#	History results are always returned in descending order by the time the song was played.
		#
		#	Query string parameters:
		#		PARAM		TYPE			REQ?	DESCRIPTION
		#		----------------------------------------------------------------------------------------------------
		#		get=		string			Y		One of ('artist','title','genre')
		#		from=		string			Y		One of ('requests','history')
		#		days=		integer			N		
		#		results=	integer			Y		Specifies the number of results to return
		#		compress=	string	 		N		If compress == "", don't compress.
		#											If compress == "gzip", return results gzip'ed
		#
		#	Returns XML of the form: 
		#		<toplist list_type="(from parameter)" entry_type="(get parameter)">
		#			<entry>
		#				<name></name><count></count>
		#			</entry>
		#			...
		#		<toplist>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/stats-top':
		
			if args is None:
				self.sendError('Incomple query parameters')
				return
				
			try:
				numResults = args['results'][0]
				getThis = args['get'][0]
				fromThis = args['from'][0]
			except LookupError:
				self.sendError('Incomple query parameters')
				return
			
			numDays = 'all'
			try:
				numDays = int(args['days'][0])
			except (LookupError, ValueError):
				pass
			
			try:
				numResults = int(numResults)
			except ValueError:
				numResults = 1
			
			if fromThis == 'requests':
				statObj = RequestStats
			elif fromThis == 'history':
				statObj = PlayStats
			else:
				self.sendError('Invalid query parameter: from=' + fromThis)
				return
				
			if getThis == 'artist':
				resultList = statObj.getTopArtists(numResults, numDays)
			elif getThis == 'title':
				resultList = statObj.getTopSongs(numResults, numDays)
			elif getThis == 'genre':
				resultList = statObj.getTopGenres(numResults, numDays)
			else:
				self.sendError('Invalid query parameter: get=' + getThis)
				return
			
			# package the result list as XML
			entryList = []
			for entry in resultList:
				if entry[1] > 0:
					entryList.append('<entry><name>' + SafeXML(entry[0]) + '</name>' + \
									'<count>' + str(entry[1]) + '</count></entry>')
			
			contentType = 'text/xml'
			packagedResults =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
								'<toplist count="' + str(len(entryList)) + '" list_type="' + fromThis + '" ' + \
									'entry_type="' + getThis + '">\n' + \
								string.join(entryList, '\n') + \
								'</toplist>'
			
			# gzip the results?
			if args.has_key('compress') and args['compress'] and args['compress'][0].lower() == 'gzip':
				contentType = 'application/x-gzip'
				packagedResults = zlib.compress(packagedResults)
			
			# send it back
			self.sendData(packagedResults, contentType)
			
		#-----------------------------------------------------------------------------------------------------------
		#  command == '/time'
		#
		#	Returns the local time on the DJ's computer. Needed for certain things on the server.
		#
		#	Query string parameters: (none)
		#
		#	Returns XML of the form:
		#			<time>(current local time)</time>
		#-----------------------------------------------------------------------------------------------------------
		elif command == '/time':
		
			self.sendData('<time>' + time.ctime() + '</time>', 'text/xml')
		
		
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
			
		response =	'<?xml version="1.0" encoding="UTF-8"?>\n' + \
					'<request><application><apptype>MBRadio Server</apptype><version>1.0</version></application>' + \
					'<status><code>' + str(code) + '</code><message>' + message + '</message></status></request>'

		self.sendData(response, 'text/xml')

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
	
		#try:
			
		# is the client in the list of allowed clients?
		if not self.client_address[0] in Config['AllowedClients'] \
				and not self.address_string() in Config['AllowedClients']:
			self.sendError('Unauthorized', 401)
			return
		
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
				
			global RequestCount
			
			songID = form['songID'][0]
			hostIP = form['host'][0]
			
			requestedBy = ''
			if form.has_key('requestedBy') and form['requestedBy']:
				requestedBy = form['requestedBy'][0].strip()
				# strip newlines
				requestedBy = requestedBy.translate(newlinestripper)
			
			dedication = ''
			if form.has_key('dedication') and form['dedication']:
				dedication = form['dedication'][0].strip()
				# strip newlines
				dedication = dedication.translate(newlinestripper)
			
			# is it a valid song?
			requestedSong = Library.getSong(songID)
			if requestedSong is None:
				self.sendRequestError(703)
				return

			# lookup in Hosts dict. if it doesn't exist, add an entry
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
			RequestCount = RequestCount + 1
			requestID = RequestCount
			requestTime = long(time.time())
			
			# update Hosts list
			Hosts[hostIP]['requests'].append( {'id': requestID, 'songID': songID, 'time': requestTime } )
			
			# add request to Requests list
			Requests[requestID] = {'songID': songID, 'time': requestTime, 'host': hostIP, 'status': 'waiting', 
									'requestedBy': requestedBy, 'dedication': dedication }

			# add to NewRequests list
			NewRequests.append(requestID)
			
			# log the request
			LogRequest(requestID)
			RequestStats.addSong({'songID': songID, 'artist':requestedSong['artist'], 'title':requestedSong['title'],
									'genre':requestedSong['genre'], 'time':requestTime})

			# send a response back in XML
			response = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
						'<request><application><apptype>MBRadio</apptype><version>1.0</version></application>' + \
						'<status><code>200</code><message>Request Received</message>' + \
						'<requestID>' + str(requestID) + '</requestID></status>' + PackageSong(songID) + '</request>'
			
			self.sendData(response, 'text/xml')
		
		#endif command == '/req'
			
		#except :
		#	self.sendError('Unknown server error')
			
	#enddef do_POST

#endclass MBRadio(BaseHTTPServer.BaseHTTPRequestHandler)

#----------------------------------------------------------------------------------------------------------------------#
#  Utility functions
#----------------------------------------------------------------------------------------------------------------------#
def PackageSong(songID):
	"""Packages the song info as an XML string"""
	
	song = Library.getSong(songID)
	if song is None:
		return ""
	
	packageStr = 	'<song id=\"' + str(songID) + '\">' + \
					'<artist>' + SafeXML(song['artist']) + '</artist>' + \
					'<title>' + SafeXML(song['title']) + '</title>' + \
					'<album>' + SafeXML(song['album']) + '</album>' + \
					'<genre>' + SafeXML(song['genre']) + '</genre>' + \
					'<duration>' + str(song['duration']) + '</duration></song>'

	return packageStr
	
#enddef PackageSong

def PackageRequest(requestID):
	"""Packages the request info as an XML string"""
	
	if requestID is None or not requestID in Requests:
		return ""
	
	reqInfo = Requests[requestID]
	
	packageStr = 	'<request id=\"' + str(requestID) + '\">' + \
					'<time>' + str(reqInfo['time']) + '</time>' + \
					'<host>' + SafeXML(reqInfo['host']) + '</host>' + \
					'<requestedby>' + SafeXML(reqInfo['requestedBy']) + '</requestedby>' + \
					'<dedication>' + SafeXML(reqInfo['dedication']) + '</dedication>' + \
					'<status>' + reqInfo['status'] + '</status>' + \
					PackageSong(reqInfo['songID']) + '</request>'

	return packageStr
	
#enddef PackageRequest

def PackageHistoryItem(timePlayed, songID, requestID):
	"""Packages a history item as an XML string"""
	
	if not Library.songExists(songID):
		return ''
		
	packageList = ['<played time=\"', str(timePlayed), '\">', PackageSong(songID)]
					
	if not requestID is None and requestID in Requests:
		reqInfo = Requests[requestID]
		
		packageList.extend(['<requested id="' + str(requestID) + '">',
							'<time>', str(reqInfo['time']), '</time>',
							'<host>', SafeXML(reqInfo['host']), '</host>', 
							'<requestedby>', SafeXML(reqInfo['requestedBy']), '</requestedby>',
							'<dedication>', SafeXML(reqInfo['dedication']), '</dedication>',
							'<status>', reqInfo['status'], '</status>', '</requested>'])
	
	packageList.append('</played>')
	return string.join(packageList,'')
	
#enddef PackageHistoryItem

def PackageQueueItem(songID, requestID):
	"""Packages a queue item as an XML string"""
	
	if not Library.songExists(songID):
		return ''
		
	packageList = 	['<queued>', PackageSong(songID)]
					
	if not requestID is None and requestID in Requests:
		reqInfo = Requests[requestID]
		
		packageList.extend(['<requested>',
							'<time>', str(reqInfo['time']), '</time>',
							'<host>', SafeXML(reqInfo['host']), '</host>',
							'<requestedby>', SafeXML(reqInfo['requestedBy']), '</requestedby>',
							'<dedication>', SafeXML(reqInfo['dedication']), '</dedication>',
							'<status>', reqInfo['status'], '</status>', '</requested>'])
	
	packageList.append('</queued>')
	return string.join(packageList, '')
	
#enddef PackageQueueItem

def SafeXML(theString):
	"""Escape a string for safe XML transmission as UTF-8"""
	
	return cgi.escape(theString).encode('ascii', 'xmlcharrefreplace')
#enddef SafeXML

def SafeAscii(theString):
	"""Return a string that only contains ASCII characters"""
	
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
#enddef SafeAscii

def MakeSortingTuple(songID, sortBy):
	"""	Create an n-tuple used to sort a song list, based on the sorting rules given by the sortBy argument.
		This takes advantage of the default lexicographic sorting behavior of sort() on lists of tuples
	"""
	
	song = Library.getSong(songID)
	if song is None:
		return tuple([None for i in range(len(sortBy)+1)])
	
	sortList=[]
	for field,dir in sortBy:
		try:
			if field == 'artist':
				field = 'sortArtist'
			elif field == 'title':
				field = 'sortTitle'
			
			if not song[field] or song[field] == '[Unknown]':
				sortList.append(chr(128))
			else:
				sortList.append(SafeAscii(song[field]).lower())
		except:
			pass
			
	sortList.append(songID)

	return tuple(sortList)

#enddef MakeSortingTuple

#----------------------------------------------------------------------------------------------------------------------#
#  Logging Functions
#----------------------------------------------------------------------------------------------------------------------#
def LogRequest(requestID):
	"""Writes a request to the log file"""
	
	if not requestID in Requests:
		return
		
	reqInfo = Requests[requestID]
	
	requestLogFile = os.path.join(Config['LogDir'], "requests.xml")
	# make sure the log file exists:
	try:
		File_CheckOrMakeDefault(requestLogFile, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<requestlog>\n</requestlog>\n")
	except:
		Debug.out("Request log file does not exist, or file could not be created.")
		return
		
	# make the log entry as XML
	requestXML =	'<request>' + \
					'<time>' + str(reqInfo['time']) + '</time>' + \
					'<host>' + SafeXML(reqInfo['host']) + '</host>' + \
					'<requestedby>' + SafeXML(reqInfo['requestedBy']) + '</requestedby>' + \
					'<dedication>' + SafeXML(reqInfo['dedication']) + '</dedication>' + \
					PackageSong(reqInfo['songID']) + \
					'</request>\n'
	
	# try to write to the xml file
	try:
		File_InsertAtLine(requestLogFile, requestXML, 3)
	except:
		Debug.out("Failed to write request to log file")

#enddef LogRequest


def LogSong(timePlayed, songID, requestID):
	"""Writes a song-play event to the log file"""
	
	if not Library.songExists(songID):
		return
	
	playedLogFile = os.path.join(Config['LogDir'], "played.xml")
	
	# make sure the log file and logs directory exist:
	try:
		File_CheckOrMakeDefault(playedLogFile, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<historylog>\n</historylog>\n")
	except:
		Debug.out("Played log file does not exist, or file could not be created.")
		return
		
	# make the log entry as XML
	playedXML =	PackageHistoryItem(timePlayed, songID, requestID) + '\n'
	
	# try to write to the xml file
	try:
		File_InsertAtLine(playedLogFile, playedXML, 3)
	except:
		Debug.out("Failed to write song to play history file")

#enddef LogSong

def File_InsertAtLine(fileName, insertThis, atLineNumber):
	"""	Inserts the string (insertThis) at line number (atLineNumber) in the file specified by (fileName)
		Note: (insertThis) must have a trailing '\n' to insert a new line!
	"""
	
	import fileinput

	lines = []
	f = fileinput.FileInput(fileName, inplace=1)
	for i in range(1, atLineNumber):
		lines.append(f.readline())
	lines.append(insertThis)
	sys.stdout.write(string.join(lines, ''))
	
	for line in f:
		sys.stdout.write(line)
	f.close()
	
#enddef File_InsertAtLine

def File_CheckOrMakeDefault(fileName, defaultContent):
	"""Checks if the file path (fileName) exists; otherwise, it creates the file and writes (defaultContent) into it"""
	
	createDefault = False
	if os.path.isfile(fileName):
		statinfo = os.stat(fileName)
		if not statinfo.st_size:
			createDefault = True
	else:
		createDefault = True
		
	if createDefault:
		f = open(fileName, 'w')
		f.write(defaultContent)
		f.close()
	
#enddef File_CheckOrMakeDefault

#----------------------------------------------------------------------------------------------------------------------#
#  Load configuration
#----------------------------------------------------------------------------------------------------------------------#
class ConfigError(Exception):
    pass

def LoadConfig():
	global Library, Config
	import platform
	
	Debug.out("Loading Config...")
	
	# port (if not already specified from command line)
	if not Config.has_key('Port'):
		Config['Port'] = 15800
	
	# which Library DB to use?  Currently the only acceptable option is "iTunes"
	Config['Library'] = "iTunes"

	# directory for saving prefs and logs
	isMac = 'Darwin' == platform.system() 
	
	# App settings directory
	if Config.has_key('AppDir'):
		if not os.path.exists(Config['AppDir']):
			sys.stderr.write("Could not find application settings directory: " + Config['AppDir'] + '\n')
			raise ConfigError
	else:
		if isMac:
			Config['AppDir'] = os.path.expanduser('~/Library/Application Support/MBRadio')
		else:
			Config['AppDir'] = os.path.abspath(os.curdir)
			
		try:
			if not os.path.exists(Config['AppDir']):
				os.makedirs(Config['AppDir'])
		except:
			sys.stderr.write("Could not find (or make) application settings directory: " + Config['AppDir'] + '\n')
			raise ConfigError
			
	# Logs directory
	if not Config.has_key('LogDir'):
		Config['LogDir'] = os.path.join(Config['AppDir'], "Logs")
		
	try:
		if not os.path.exists(Config['LogDir']):
			os.makedirs(Config['LogDir'])
	except:
		sys.stderr.write("Could not find (or make) application logs directory: " + Config['LogDir'] + '\n')
		raise ConfigError
		
	# iTunesDB
	if not Config.has_key('iTubesDB'):
		if isMac:
			# FIXME
			Config['iTunesDB'] = '/Users/Shared/iTunes/iTunes Music Library.xml'
		else:
			Config['iTunesDB'] = os.path.expanduser('~\Music\iTunes\iTunes Music Library.xml')
	
	if not os.path.exists(Config['iTunesDB']):
		sys.stderr.write("Could not find iTunes XML DB at: " + Config['iTunesDB'] + '\n')
		raise ConfigError
		

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
	Config['LocalHost'] = '127.0.0.1'
	
#enddef LoadConfig

#----------------------------------------------------------------------------------------------------------------------#
#  Command line handler
#----------------------------------------------------------------------------------------------------------------------#

def HandleCommandline(argv):
	import optparse
	
	if argv is None:
		argv = sys.argv[1:]

	# initialize the parser object:
	usage = "usage: %prog [options]"
	parser = optparse.OptionParser(formatter=optparse.IndentedHelpFormatter(width=78, max_help_position=6))

	# define options here:
	parser.add_option("-p", "--port", dest="port", 
						action="store", type="long", 
						help="Specifies port the HTTP server binds to")
	parser.add_option("-L", "--library", dest="xmldb",metavar="FILE",
						action="store", type="string", 
						help="Path to the iTunes DB XML file.")
	parser.add_option("--app-dir", dest="appdir",metavar="PATH",
						action="store", type="string", 
						help="Path to the application's settings directory.")
	parser.add_option("--log-dir", dest="logdir",metavar="PATH",
						action="store", type="string", 
						help="Path to the application's logs directory. Defaults to '$AppDir/logs'")
	parser.add_option("-v", "--verbose", dest="verbose", 
						action="store_true",default=True,  # FIXME
						help="Prints debugging output to stderr")
						
	settings, args = parser.parse_args(argv)

	return settings, args
	
#enddef HandleCommandline()

#----------------------------------------------------------------------------------------------------------------------#
#  main()
#----------------------------------------------------------------------------------------------------------------------#
def main(argv=None):

	#gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_OBJECTS | gc.DEBUG_COLLECTABLE )
	
	# handle commandline
	try:
		settings, args = HandleCommandline(argv)
		if settings.verbose:
			Debug.DEBUG = 1
		else:
			Debug.DEBUG = 0
			
		if settings.port:
			Config['Port'] = settings.port
			
		if settings.xmldb:
			Config['iTunesDB'] = settings.xmldb
			
		if settings.appdir:
			Config['AppDir'] = settings.appdir
		
		if settings.logdir:
			Config['LogDir'] = settings.logdir
			
	except:
		sys.stderr.write('Failed to parse commandline')
		sys.exit(2)

	# load configuation:
	try:
		LoadConfig()
	except ConfigError:
		sys.stderr.write('Failed to load configuration')
		sys.exit(1)
	
	# load music library
	try:
		LoadLibrary()
	except:
		sys.stderr.write('Failed to load music library')
		sys.exit(1)
	
	# load history from the logs
	try:
		PlayStats.loadFromLog(os.path.join(Config['LogDir'], "played.xml"))
	except:
		pass
	try:
		RequestStats.loadFromLog(os.path.join(Config['LogDir'], "requests.xml"))
	except:
		pass
	
	
	# FIXME
	# create some dummy data for debugging
	Requests[1] = {'songID': 'EDE3C749777F9376', 'time': long(time.time()), 'host': '127.0.1', 'status': 'waiting', 
									'requestedBy': 'Jon', 'dedication': 'Erich' }
	
	Requests[2] = {'songID': 'BE3F7187F3FBC986', 'time': long(time.time()), 'host': 'localhost', 'status': 'waiting', 
									'requestedBy': 'erich', 'dedication': 'Jon' }
	
	NewRequests.append(1)
	NewRequests.append(2)
	
	RequestCount = 2
		
	# start the HTTP server
	import socket
	try:
		server = BaseHTTPServer.HTTPServer(('', Config['Port']), MBRadio)
	except socket.error as (errno, strerror):
		sys.stderr.write('Failed to create HTTP Server: ' + strerror)
		sys.exit(1)
	except:
		sys.stderr.write('Failed to create HTTP Server (unknown error)')
		sys.exit(1)
	
	try:
		sys.stderr.write('Starting MBRadio Webserver\n')
		server.serve_forever()
	except (KeyboardInterrupt, SystemExit):
		Debug.out('^C received, shutting down server')

	server.socket.close()
	return 0
	
#enddef main()

if __name__ == '__main__':
    status = main()
    sys.exit(status)

