#----------------------------------------------------------------------------------------------------------------------#
#  MBRadio
#
#  Base class for the MusicLibrary class
#
#  This is to ensure compatibility with any future modifications that might use another source for the user's
#  music library.
#----------------------------------------------------------------------------------------------------------------------#

import string
import re
import cgi

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
			
			# Each list item is currently a tuple of the format: ("song artist - title", trackID)
			# Here we remove the first element of the tuple (the song name)
			# The song artist/title string is no longer needed once the list has been sorted - just hogs memory
			self.byLetter[k] = map(lambda pair: pair[1], self.byLetter[k])
			
			
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#

	def addSong(self, songID, songTitle, songArtist, songAlbum, songGenre, songDuration):
		
		theArtist = songArtist.strip()
		theTitle = songTitle.strip()
		theGenre = songGenre.strip()
		if not (theArtist is None and theTitle is None):
			theName = theArtist + ' - ' + theTitle
		elif not (theTitle is None):
			theName = theTitle
		else:
			# no good tag data. skip it.
			return
		
		theName = theName.encode('ascii','replace').upper()
		
		self.songs[songID] = {'title': theTitle, 'artist': theArtist, \
								'album': songAlbum.strip(), 'genre': theGenre, 'duration': songDuration}
								
		self.songCount = self.songCount + 1
		
		# place song in the "byLetter" dictionary for quick and easy searching later
		if theName:
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
		
		if not self.songs.has_key(songID):
			return ""
		
		song = self.songs[songID]
		
		packageStr = '\t<song id=\"' + str(songID) + '\">' + \
						'<artist>' + self.unicodeToHTML(song['artist']) + '</artist>' + \
						'<title>' + self.unicodeToHTML(song['title']) + '</title>' + \
						'<album>' + self.unicodeToHTML(song['album']) + '</album>' + \
						'<genre>' + self.unicodeToHTML(song['genre']) + '</genre>' + \
						'<duration>' +str(song['duration']) + '</duration></song>\n'

		return packageStr
		
	def packageSonglist(self, songList, numResults, startingFrom):
		# packages a list of songs in XML for transmission
		# arugment(songList) should be a list of valid songID's from the library
		
		slicedList = self.sliceSonglist(songList, numResults, startingFrom)
		
		packageStr = '<songlist count=\"' + str(len(slicedList)) + '\" total=\"' + str(len(songList)) + '\">\n'
		
		for t in slicedList:
			packageStr = packageStr + self.packageSong(t)
			
		packageStr = packageStr + '</songlist>'
		
		return packageStr
		
	def unicodeToHTML(self, theString):
		return cgi.escape(theString).encode('ascii', 'xmlcharrefreplace')
	
	def makeSongName(self, songID):
		if not self.songs[songID]['artist'] is None:
			theName = self.songs[songID]['artist'] + ' - ' + self.songs[songID]['title']
		else:
			theName = self.songs[songID]['title']
			
		return theName.encode('ascii','replace').upper()
	
	def sortSonglist(self, songList):
		
		songListToSort = map(lambda songID: (self.makeSongName(songID), songID), songList)
		songListToSort.sort()
		sortedSongList = map(lambda pair: pair[1], songListToSort)
		
		return sortedSongList
	
	def sliceSonglist(self, songList, numResults, startingFrom):
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
		return songList[startingFrom:endingAt]
	
	#------------------------------------------------------------------------------------------------------------------#
	# Public methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def searchBy_Letter(self, theLetter, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# sanitize data:
		theLetter = theLetter[0].upper()
		
		if (theLetter.isalpha() or theLetter == '0') and self.byLetter.has_key(theLetter):
		
			songList = self.byLetter[theLetter]

			# pass it to get packaged!
			s = self.packageSonglist(slicedList, numResults, startingFrom)
			return s
			
		return -1
		
	def searchBy_Artist(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# sanitize data:
		searchStr = searchStr.encode('ascii','replace').upper()
		
		# split into words
		searchWords = searchStr.split()
		escapedWords = []
		for w in searchWords:
			escapedWords.append(re.escape(w))
		
		# find artists where all words match
		matchedSongs = []
		allArtists = self.byArtist.keys()
		
		for artist in allArtists:
			allMatched = 0
			for word in escapedWords:
				if re.search(word, artist):
					allMatched = 1
				else:
					allMatched = 0
					break
					
			if allMatched:
				matchedSongs.extend(self.byArtist[artist])
		
		# sort the matchedSongs list
		songList = self.sortSonglist(matchedSongs)
		
		# pass it to get packaged!
		return self.packageSonglist(songList, numResults, startingFrom)
		
	def searchBy_Genre(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# sanitize data:
		searchStr = searchStr.encode('ascii','replace').upper()
		
		# split into words
		searchWords = searchStr.split()
		escapedWords = []
		for w in searchWords:
			escapedWords.append(re.escape(w))
		
		# find artists where all words match
		matchedSongs = []
		allGenres = self.byGenre.keys()
		
		for genre in allGenres:
			allMatched = 0
			for word in escapedWords:
				if re.search(word, genre ):
					allMatched = 1
				else:
					allMatched = 0
					break
					
			if allMatched:
				matchedSongs.extend(self.byGenre[genre])
		
		# sort the matchedSongs list
		songList = self.sortSonglist(matchedSongs)
		
		# pass it to get packaged!
		return self.packageSonglist(songList, numResults, startingFrom)
	
	def searchBy_Title(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# sanitize data:
		searchStr = searchStr.encode('ascii','replace').upper()
		
		# split into words
		searchWords = searchStr.split()
		escapedWords = []
		for w in searchWords:
			escapedWords.append(re.escape(w))
		
		# find artists where all words match
		matchedSongs = []

		for songID, songData in self.songs.items():
			allMatched = 0
			songTitle = songData['title'].encode('ascii','replace').upper()
			for word in escapedWords:
				if re.search(word, songTitle):
					allMatched = 1
				else:
					allMatched = 0
					break
					
			if allMatched:
				matchedSongs.append(songID)
		
		# sort the matchedSongs list
		songList = self.sortSonglist(matchedSongs)
		
		# pass it to get packaged!
		return self.packageSonglist(songList, numResults, startingFrom)

	def searchBy_Any(self, searchStr, numResults, startingFrom):
		# returns:
		#	(int)     -1    on error
		#	(string)        the XML data representing the songlist
		
		# sanitize data:
		searchStr = searchStr.encode('ascii','replace').upper()
		
		# split into words
		searchWords = searchStr.split()
		escapedWords = []
		for w in searchWords:
			escapedWords.append(re.escape(w))
		
		# find artists where all words match
		matchedSongs = []

		for songID, songData in self.songs.items():
			titleMatched = 0
			artistMatched = 0
			genreMatched = 0
			songTitle = songData['title'].encode('ascii','replace').upper()
			songArtist = songData['artist'].encode('ascii','replace').upper()
			songGenre = songData['genre'].encode('ascii','replace').upper()
			
			for word in escapedWords:
				if re.search(word, songTitle):
					titleMatched = 1
				else:
					titleMatched = 0
					break
			for word in escapedWords:
				if re.search(word, songArtist):
					artistMatched = 1
				else:
					artistMatched = 0
					break
			for word in escapedWords:
				if re.search(word, songGenre):
					genreMatched = 1
				else:
					genreMatched = 0
					break
					
			if titleMatched or artistMatched or genreMatched:
				matchedSongs.append(songID)
		
		# sort the matchedSongs list
		songList = self.sortSonglist(matchedSongs)
		
		# pass it to get packaged!
		return self.packageSonglist(songList, numResults, startingFrom)
		
	