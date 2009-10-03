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
			#	/requests/
			#
			#		This interface is only used internally by the request-list display app on the DJ's personal
			#		computer. It returns the current queue of song requests in XML format. Once the requests have been
			#		retreived, the queue is emptied. (unless the 'clear' parameter is set to 'no')
			#
			#		Query string parameters:
			#			NAME		TYPE			DESCRIPTION
			#			------------------------------------------------------------------------------------------------
			#			clear 		string			one of [yes|no]  defaults to yes
			
			if fileStr == '/search/':

				if queryStr:
					
					# parse the query string 
					args = urlparse.parse_qs(queryStr);

					if args.has_key('by') and args.has_key('for'):
						
						searchBy = args['by'][0].lower()
						searchFor = args['for'][0]
						
						if args.has_key('results'):
							results = int(args['results'][0])
						else:
							results = 100
							
						if args.has_key('starting'):
							starting = int(args['starting'][0])
						else:
							starting = 0
						
						# Execute the search on the music Library!
						
						if searchBy == "letter":
							resultSet = Library.searchBy_Letter(searchFor, results, starting)
						elif searchBy == "artist":
							resultSet = Library.searchBy_Artist(searchFor, results, starting)
						elif searchBy == "genre":
							resultSet = Library.searchBy_Genre(searchFor, results, starting)
						elif searchBy == "title":
							resultSet = Library.searchBy_Title(searchFor, results, starting)
						elif searchBy == "any":
							resultSet = Library.searchBy_Any(searchFor, results, starting)
						else:
							self.send_response(500)
							self.send_header('Content-type', 'text/html')
							self.end_headers()
							self.wfile.write("Unknown search parameter " + searchBy)
							return
						
						# Return the results as an gzipped XML file

						compressedResults = resultSet
						#compressedResults = zlib.compress(resultSet)
						
						self.send_response(200)
						self.send_header('Content-type', 'text/plain')
						self.end_headers()
						self.wfile.write(compressedResults)
						return
						
						
			
			# error fall-through
			self.send_response(500)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write("Server error")
			return

		except:
			pass

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
				
				if form['songID'] and form['songID']:
					global requestCount
					
					songID = form['songID'][0]
					hostIP = form['host'][0]
					
					if form['name']:
						requestedBy = form['name'][0]
					else:
						requestedBy = ''
						
					if form['dedication']:
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
				self.send_response(500)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write("Server error")
				return
			
		except :
			pass


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