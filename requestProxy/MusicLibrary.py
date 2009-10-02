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
			print "this letter = " + c
			self.byLetter[c] = []
			
		self.byLetter['0'] = []

		
	def load(self):
		# Must be implemented!
		
		# This should do whatever is required to initialize the library
		# Typical arguments might be a filename specifying the database path
		
		pass
	
		
	# Private methods:
	
	def addTrack(self, trackID, trackTitle, trackArtist, trackAlbum, trackGenre, trackDuration):
		
		theArtist = trackArtist.strip()
		theTitle = trackTitle.strip()
		if theArtist:
			theName = theArtist
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
			print "first letter = " + firstLetter
			
			if firstLetter.isalpha():
				self.byLetter[firstLetter].append(trackID)
			else:
				self.byLetter['0'].append(trackID)
		
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
		pass
		
	def searchBy_Artist(self, searchStr):
		pass
		
	def searchBy_Title(self, searchStr):
		pass
		
	def searchBy_Genre(self, searchStr):
		pass
		
	def searchBy_Any(self, searchStr):
		pass
		
	