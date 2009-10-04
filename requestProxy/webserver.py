#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	webserver.py
#	
#	Implements the HTTP Request Server
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#----------------------------------------------------------------------------------------------------------------------#

# python library imports
import string, cgi, time, urlparse, zlib, os.path, unicodedata, datetime, time
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
		#			NAME		TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			for 		string		Y		string literal to search for
		#			by			option: 	Y		one of [letter|artist|title|genre|any]
		#			results 	integer 	N		Number of results to return  (defaults to 100)
		#			starting	integer		N		For continuation of search results, starting at this number result
		#												(defaults to 0)
		#		
		#	/new-requests/
		#
		#		This interface is only used internally by the request-list display app on the DJ's personal
		#		computer. It returns the current queue of song requests in XML format. Once the requests have been
		#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
		#		Any requests that do not originate from the localhost are ignored.
		#
		#		Query string parameters:
		#			NAME		TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			clear 		string		N		one of [yes|no]  (defaults to 'yes')
		#			order		string		N		one of [newest|oldest]  (defaults to 'newest')
		#
		#	/requests/
		#
		#		This interface is used by the webserver to get a list of recent requests to display on the website.
		#		Requests are always returned in descending order by the time the request was made.
		#
		#		Query string parameters:
		#			NAME		TYPE		REQ?	DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			results 	integer		Y		Number of results to return
		#
		#	/time/
		#
		#		Returns the local time on the DJ's computer. Needed for certain things on the server.
		#
		#		Query string parameters: (none)
		#
		#---------------------------------------------------------------------------------------------------------------
		
		#try:
			# split the request into the "file name" and the "query string"
			fileStr, sepChar, queryStr = self.path.partition('?')
			
			if fileStr == '/search/' and queryStr:
			
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				if not args:
					self.sendError(500, 'Incomple search parameters')
					return

				if args.has_key('by') and args.has_key('for') and args['by'] and args['for']:
					
					searchBy = args['by'][0].lower()
					searchFor = args['for'][0]
					
					if args.has_key('results') and args['results']:
						numResults = int(args['results'][0])
					else:
						numResults = 100
						
					if args.has_key('starting') and args['starting']:
						startingFrom = int(args['starting'][0])
					else:
						startingFrom = 0
					
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
					sortedResults = SortSonglist(resultSet)
					
					# packages the results as XML
					packagedResults = PackageSonglist(sortedResults, numResults, startingFrom)
					
					# gzip the results XML
					compressedResults = packagedResults
					#compressedResults = zlib.compress(resultSet)
					
					# send it back
					self.send_response(200)
					self.send_header('Content-type', 'text/xml')
					self.end_headers()
					self.wfile.write(compressedResults)
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
				
				return
				
			#endif fileStr == '/new-requests/':
			
			
			elif fileStr == '/requests/':
				
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				if args is None or not args.has_key('results') or not args['results']:
					self.sendError(500, 'Incomple query parameters')
					return

				numResults = int(args['results'][0])
				if numResults <= 0:
					numResults = 10
				
				# sort requests by timestamp desc:
				requestListToSort = map(lambda reqDict: (reqDict['info']['time'], reqDict['id']), Requests)
				requestListToSort.sort()
				requestListToSort.reverse()
				sortedRequestList = map(lambda pair: pair[1], requestListToSort)
				
				# take the slice:
				if numResults > len(sortedRequestList):
					numResults = len(sortedRequestList)
				
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

		#except:
		#	pass
			
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
		#			NAME		TYPE			DESCRIPTION
		#			----------------------------------------------------------------------------------------------------
		#			songID 		integer			the iTunes track id
		#			host		string 			IP address of requester
		#			requestedBy string 			Name of the person making the request
		#			dedication	string			A short message (dedication) for the request
		#
		#		Returns XML of the form:
		#			<request><application><apptype>MBRadio</apptype><version>1.0</version></application>
		#				<status><code></code><message></message><requestID></requestID></status>
		#				<song id=""><artist></artist><title></title><album></album><genre></genre><duration></duration></song>
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
	
	# take the appropriate slice:
	slicedList = songList[startingFrom:endingAt]
	
	packageStr = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
					'<songlist count=\"' + str(len(slicedList)) + '\" ' + 'total=\"' + str(len(songList)) + '\" ' + \
					'first=\"' + str(startingFrom) + '\" ' + 'last=\"' + str(endingAt-1) + '\"' + '>\n'
	
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

def MakeSortingTuple(songID):
	song = Library.getSong(songID)
	if song is None:
		return (None, None, None)
	
	if song.has_key('sortArtist') and song['sortArtist']:
		f1 = song['sortArtist']
	elif song.has_key('artist') and song['artist']:
		f1 = song['artist']
	elif song.has_key('title') and song['title']:
		f1 = song['title']
	else:
		f1 = None
		
	f1 = SafeAscii(f1).upper()
	
	if song.has_key('sortTitle') and song['sortTitle']:
		f2 = song['sortTitle']
	elif song.has_key('sortTitle') and song['title']:
		f2 = song['title']
	else:
		f2 = None
	
	if f1 is None or f2 is None:
		return (None, None, None)
	
	f2 = SafeAscii(f2).upper()
	
	return (f1, f2, songID)

#enddef makeSongName

def SortSonglist(songList):
	songListToSort = map(lambda songID: MakeSortingTuple(songID), songList)
	songListToSort.sort()
	sortedSongList = map(lambda triplet: triplet[2], songListToSort)
	
	return sortedSongList
#enddef SortSonglist

#----------------------------------------------------------------------------------------------------------------------#
#  main()
#----------------------------------------------------------------------------------------------------------------------#
def main():
	
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