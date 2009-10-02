#----------------------------------------------------------------------------------------------------------------------#
#  MBRadio
#
#  Base class for the MusicLibrary class
#
#  This is to ensure compatibility with any future modifications that might use another source for the user's
#  music library.
#----------------------------------------------------------------------------------------------------------------------#

import string

class MusicLibrary:
	
	tracks = {}
	byLetter = {}
	trackCount = 0
	
	# Initialization:
	
	def __init__(self):
		
		asciiLetters = string.ascii_uppercase
		for c in asciiLetters:
			self.byLetter[c] = []
			
		self.byLetter['0'] = []

		
	def load(self):
		# Details must be implemented by the subclass, and then call this function to finish
		# creating the lookup tables
		
		# sort the "song by letter" lists
		for k in self.byLetter.keys():
			self.byLetter[k].sort()

		
			
	# Private methods:
	
	def addTrack(self, trackID, trackTitle, trackArtist, trackAlbum, trackGenre, trackDuration):
		
		theArtist = trackArtist.strip()
		theTitle = trackTitle.strip()
		if theArtist:
			theName = theArtist + ' - ' + theTitle
		else:
			theName = theTitle
		
		self.tracks[trackID] = {'title': theTitle, 'artist': theArtist, \
								'album': trackAlbum.strip(), 'genre': trackGenre.strip(), 'duration': trackDuration}
		
		if theName:
			firstLetter = theName[0]
		else:
			firstLetter = ''
		
		if firstLetter:
			firstLetter = firstLetter.encode('ascii','replace')
			firstLetter = firstLetter.upper()
			
			if not firstLetter.isalpha():
				firstLetter = '0'
			
			self.byLetter[firstLetter].append((theName, trackID))
		
		self.trackCount = self.trackCount + 1
		
	def packageTrack(self, trackID):
		
		# packages the track info as an XML string
		
		track = tracks[trackID]
		
		packageStr = '<song><songid>' + trackID + '</songid>' + \
						'<artist>' + track['artist'] + '</artist>' + \
						'<title>' + track['title'] + '</title>' + \
						'<album>' + track['album'] + '</album>' + \
						'<genre>' + track['genre'] + '</genre>' + \
						'<duration>' + track['duration'] + '</duration></song>'
		return packageStr
		
	def packageTracklist(self, trackList):
	
		# packages a list of tracks in XML for transmission
		
		# arugment(trackList) should be a list of valid trackID's from the library
		
		packageStr = '<tracklist count="' + len(packagedTracks) + '">'
		
		for t in trackList:
			packageStr = packageStr + self.packageTrack(t)
			
		packageStr = packageStr + '</tracklist>'
		
		return packageStr
		
		
	
	# Public methods:
	
	def searchBy_Letter(self, theLetter):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the tracklist
		
		# oh, just in case:
		theLetter = theLetter[0]
		theLetter = theLetter.upper()
		
		if not theLetter.isalpha() and theLetter != '0':
			return -1
			
		
		
		pass
		
	def searchBy_Artist(self, searchStr):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the tracklist
		
		pass
		
	def searchBy_Title(self, searchStr):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the tracklist
		
		pass
		
	def searchBy_Genre(self, searchStr):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the tracklist
		
		pass
		
	def searchBy_Any(self, searchStr):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the tracklist
		
		pass
		
	