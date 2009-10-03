#----------------------------------------------------------------------------------------------------------------------#
#  MBRadio
#
#  HTTP Request Server
#----------------------------------------------------------------------------------------------------------------------#

# python library imports
import string, cgi, time, urlparse, zlib, os.path
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# local imports
import iTunesLibrary

Library = iTunesLibrary.iTunesLibrary()

#----------------------------------------------------------------------------------------------------------------------#
#  Config
#----------------------------------------------------------------------------------------------------------------------#

serverPort = 15800

# Application directory
# Jonathan: this may need to be changed on the Mac
rootDir = "mbradio"
rootPath = os.path.join(os.path.expanduser('~'), rootDir)

# Jonathan: This will need to be changed for Mac
iTunesDB = os.path.join(os.path.expanduser('~'), 'Music\iTunes\iTunes Music Library.xml')

maxRequests_HostPerHour = 10
maxRequests_ArtistPerHour = 5
maxRequests_AlbumPerHour = 5
maxRequests_SongPerHour = 2


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
		try:

			# split the request into the "file name" and the "query string"
			fileStr, sepChar, queryStr = self.path.partition('?')
			
			# Acceptable "file names"
			#
			#	/search/
			#
			#		This interface is used to search the library for songs. This request is only sent from the
			#		radio station website to get the tracklist to allow users to request songs. It returns a list of
			#		songs in XML format.
			#
			#		Query string parameters:
			#			NAME		TYPE			DESCRIPTION
			#			------------------------------------------------------------------------------------------------
			#			for 		string			string literal to search for
			#			by			option: 		one of [letter|artist|title|genre|any]
			#			results 	integer 		Number of results to return
			#			starting	integer			For continuation of search results, starting at this number result
			#		
			#	/new-requests/
			#
			#		This interface is only used internally by the request-list display app on the DJ's personal
			#		computer. It returns the current queue of song requests in XML format. Once the requests have been
			#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
			#		Any requests that do not originate from the localhost are ignored.
			#
			#		Query string parameters:
			#			NAME		TYPE			DESCRIPTION
			#			------------------------------------------------------------------------------------------------
			#			clear 		string			one of [yes|no]  defaults to yes
			#
			#	/new-requests/
			#
			#		This interface is only used internally by the request-list display app on the DJ's personal
			#		computer. It returns the current queue of song requests in XML format. Once the requests have been
			#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
			#		Any requests that do not originate from the localhost are ignored.
			#
			#		Query string parameters:
			#			NAME		TYPE			DESCRIPTION
			#			------------------------------------------------------------------------------------------------
			#			clear 		string			one of [yes|no]  defaults to yes
			
			if fileStr == '/search/' and queryStr:
			
				# parse the query string 
				args = urlparse.parse_qs(queryStr);
				
				if not args:
					sendError(500, 'Invalid search parameters')
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
						sendError(500, 'Unknown search parameter by=' + searchBy)
						return
						
					if resultSet is None:
						sendError(500, 'Search error occurred')
						return				
					
					# sort the results
					sortedResults = sortSonglist(resultSet)
					
					# packages the results as XML
					packagedResults = packageSonglist(sortedResults, numResults, startingFrom)
					
					# gzip the results XML
					compressedResults = packagedResults
					#compressedResults = zlib.compress(resultSet)
					
					# send it back
					self.send_response(200)
					self.send_header('Content-type', 'text/plain')
					self.end_headers()
					self.wfile.write(compressedResults)
					return
					
			#endif fileStr == '/search/'
			
			
			if fileStr == '/new-requests/':
				
				return
			#endif fileStr == '/new-requests/':
			
			
			if fileStr == '/requests/':
			
				return
			#endif fileStr == '/requests/':
			
			
			# error fall-through
			sendError(500, 'Server error')
			return

		except:
			pass
			
	#enddef do_GET
	
	
	def do_POST(self):

		try:
		
			# split the request into the "file name" and the "query string"
			fileStr, sepChar, queryStr = self.path.partition('?')
			
			# Acceptable "file names"
			#	/req/
			#		Form data parameters:
			#			NAME		TYPE			DESCRIPTION
			#			------------------------------------------------------------------------------------------------
			#			songID 		integer			the iTunes track id
			#			host		string 			IP address of requester
			#			name 		string 			Name of the person making the request
			#			dedication	string			A short message (dedication) for the request
			
			if fileStr == '/req/':
			
				# get the form data
				form = cgi.parse_qs(self.rfile.read(int(self.headers.getheader('Content-Length'))))
				
				if not form:
					sendError(500, 'Invalid post data')
					return
				
				if form.has_key('songID') and form.has_key('songID') and form['songID'] and form['host']:
					global requestCount
					
					songID = form['songID'][0]
					hostIP = form['host'][0]
					
					if form.has_key('name') and form['name']:
						requestedBy = form['name'][0]
					else:
						requestedBy = ''
						
					if form.has_key('dedication') and form['dedication']:
						dedication = form['dedication'][0]
					else:
						dedication = ''
					
					requestCount = requestCount + 1
					
					# dump to requests XML file (or to stdout???)
					
					# FINISH ME!
					
					
					
					# send a response back in XML
					response = '''<?xml version="1.0" encoding="UTF-8"?>
								<REQUEST><application><apptype>MBRadio Server</apptype><version>1.0</version></application>
								<status><code>200</code><message>Request Received</message><requestID>''' + str(requestCount) + '''</requestID></status>
								<song><artist></artist><title></title><album></album><duration></duration></song>
								</REQUEST>'''

					self.send_response(200)
					self.send_header('Content-type', 'text/xml')
					self.end_headers()
					self.wfile.write(response)
					
					return
				
				# error fall-through
				sendError(500, 'Server error')
				return
			
			#endif fileStr == '/req/'
			
		except :
			pass
			
	#enddef do_POST

#endclass MBRadio(BaseHTTPRequestHandler)

#----------------------------------------------------------------------------------------------------------------------#
#  Utility functions
#----------------------------------------------------------------------------------------------------------------------#
def packageSonglist(songList, numResults, startingFrom):
	# packages a list of songs in XML for transmission
	# arugment(songList) should be a list of valid songID's from the library
	
	# sanitise the numResults & startingFrom
	if numResults is None or numResults < 0:
		numResults = 50
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
		packageStr = packageStr + packageSong(song)
		
	packageStr = packageStr + '</songlist>'
	
	return packageStr
	
#enddef packageSonglist
	
def packageSong(songID):
	# packages the song info as an XML string
	
	song = Library.getSong(songID)
	if song is None:
		return ""
	
	packageStr = '\t<song id=\"' + str(songID) + '\">' + \
					'<artist>' + unicodeToHTML(song['artist']) + '</artist>' + \
					'<title>' + unicodeToHTML(song['title']) + '</title>' + \
					'<album>' + unicodeToHTML(song['album']) + '</album>' + \
					'<genre>' + unicodeToHTML(song['genre']) + '</genre>' + \
					'<duration>' +str(song['duration']) + '</duration></song>\n'

	return packageStr
	
#enddef packageSong

def unicodeToHTML(theString):
	return cgi.escape(theString).encode('ascii', 'xmlcharrefreplace')
#enddef unicodeToHTML

def makeSortTuple(songID):
	song = Library.getSong(songID)
	if song is None:
		return (None, None, None)
	
	if song['artist']:
		return (song['artist'].encode('ascii','replace').upper(), song['title'].encode('ascii','replace').upper(), songID)
	else:
		theTitle = song['title'].encode('ascii','replace').upper()
		return (theTitle, theTitle, songID)

#enddef makeSongName

def sortSonglist(songList):
	songListToSort = map(lambda songID: makeSortTuple(songID), songList)
	songListToSort.sort()
	sortedSongList = map(lambda triplet: triplet[2], songListToSort)
	
	return sortedSongList
#enddef sortSonglist

#----------------------------------------------------------------------------------------------------------------------#
#  main()
#----------------------------------------------------------------------------------------------------------------------#
def main():
	global serverPort
	
	try:
		print 'Loading song database...'
		Library.load(iTunesDB)
		
		server = HTTPServer(('', serverPort), MBRadio)
		print 'Starting MBRadio Webserver'
		server.serve_forever()
		
	except KeyboardInterrupt:
		print '^C received, shutting down server'
		server.socket.close()

if __name__ == '__main__':
	main()