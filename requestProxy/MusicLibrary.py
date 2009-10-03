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
	
	songs = {}
	byLetter = {}
	byGenre = {}
	byArtist = {}
	songCount = 0
	
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
	
	def addSong(self, songID, songTitle, songArtist, songAlbum, songGenre, songDuration):
		
		theArtist = songArtist.strip()
		theTitle = songTitle.strip()
		theGenre = songGenre.strip()
		if theArtist:
			theName = theArtist + ' - ' + theTitle
		else:
			theName = theTitle
		
		self.songs[songID] = {'title': theTitle, 'artist': theArtist, \
								'album': songAlbum.strip(), 'genre': theGenre, 'duration': songDuration}
								
		self.songCount = self.songCount + 1
		
		# place song in the "byLetter" dictionary for quick and easy searching later
		if theName and theName[0]:
			firstLetter = theName[0].encode('ascii','replace').upper()
			
			if not firstLetter.isalpha():
				firstLetter = '0'
			
			self.byLetter[firstLetter].append((theName, songID))
		
		# place song in the "byGenre" dictionary for quick and easy searching later
		if theGenre:
			g = theGenre.encode('ascii','replace').upper()
			
			if not self.byGenre.has_key(g):
				self.byGenre[g] = []
				
			self.byGenre[g].append(songID)
			
		# place song in the "byArtist" dictionary to quick and easy searching later
		if theArtist:
			a = theArtist.encode('ascii','replace').upper()
			
			if not self.byArtist.has_key(a):
				self.byArtist[a] = []
				
			self.byArtist[a].append(songID)
		
	def packageSong(self, songID):
		
		# packages the song info as an XML string
		
		song = songs[songID]
		
		packageStr = '<song><songid>' + songID + '</songid>' + \
						'<artist>' + song['artist'] + '</artist>' + \
						'<title>' + song['title'] + '</title>' + \
						'<album>' + song['album'] + '</album>' + \
						'<genre>' + song['genre'] + '</genre>' + \
						'<duration>' + song['duration'] + '</duration></song>'
		return packageStr
		
	def packageSonglist(self, songList):
	
		# packages a list of songs in XML for transmission
		
		# arugment(songList) should be a list of valid songID's from the library
		
		packageStr = '<songlist count="' + len(packagedSongs) + '">'
		
		for t in songList:
			packageStr = packageStr + self.packageSong(t)
			
		packageStr = packageStr + '</songlist>'
		
		return packageStr
		
		
	
	# Public methods:
	
	def searchBy_Letter(self, theLetter, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# oh, just in case:
		theLetter = theLetter[0]
		theLetter = theLetter.upper()
		
		if not theLetter.isalpha() and theLetter != '0':
			return -1
			
		
		
		pass
		
	def searchBy_Artist(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		pass
		
	def searchBy_Title(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		pass
		
	def searchBy_Genre(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		pass
		
	def searchBy_Any(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		pass
		
	