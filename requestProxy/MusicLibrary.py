#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	MusicLibrary.py
#	
#	Implements the base class for the MusicLibrary.
#
#	This is to ensure compatibility with any future modifications that might use another source for the music library.
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#----------------------------------------------------------------------------------------------------------------------#

import string, re, unicodedata
import Debug

def SafeAscii(theString):
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')

class MusicLibrary:
	
	# songs dictionary
	#	Holds all of the songs in the library
	#	Format:		keys: 	 <songID> (string)
	#				values:	 dict{ 'artist': (ustring), 'title': (ustring), 'album': (ustring), 'genre': (ustring), 
	#						       'duration': (integer), 'sort-artist': (ustring), 'sort-title': (ustring) }
	songs = {}
	
	# byLetter dictionary
	#	Holds lists of songIDs organized by first letter (for fast searching)
	#	Format:		keys:	 '0', 'A', 'B', 'C', .... 'Z'
	#				values:	 list[(songID1), (songID2),...]
	byLetter = {}
	
	# byGenre dictionary
	#	Holds lists of songIDs organized by song genre (for fast searching)
	#	Format:		keys:	 <genre-name>  (as string)
	#				values:	 list[(songID1), (songID2),...]
	byGenre = {}
	
	# byArtist dictionary
	#	Holds lists of songIDs organized by song artist (for fast searching)
	#	Format:		keys:	 <artist-name>  (as string)
	#				values:	 list[(songID1), (songID2),...]
	byArtist = {}
	
	
	#------------------------------------------------------------------------------------------------------------------#
	# Init
	#------------------------------------------------------------------------------------------------------------------#
	
	def __init__(self):
		
		asciiLetters = string.ascii_uppercase
		for c in asciiLetters:
			self.byLetter[c] = []
			
		self.byLetter['0'] = []

		
	def load(self):
		# Details must be implemented by the subclass!!
		
		pass
			
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#

	def addSong(self, songData):
		
		songID = songData['id']
		songArtist = unicode(songData['artist']).strip()
		songTitle = unicode(songData['title']).strip()
		
		if not songArtist and not songTitle:
			# no good tag data. skip it.
			return
		
		songGenre = unicode(songData['genre']).strip()
		songAlbum = unicode(songData['album']).strip()
		songDuration = unicode(songData['duration']).strip()
		songSortTitle = unicode(songData['sortTitle']).strip()
		songSortArtist = unicode(songData['sortArtist']).strip()
		
		if songSortArtist:
			firstLetter = songSortArtist[0]
		elif songArtist:
			firstLetter = songArtist[0]
		elif songSortTitle:
			firstLetter = songSortTitle[0]
		elif songTitle:
			firstLetter = songTitle[0]
		firstLetter = SafeAscii(firstLetter).upper()
		
		if not songArtist:
			songArtist = u'[Unknown]'
		if not songTitle:
			songTitle = u'[Unknown]'
		
		self.songs[songID] = {'title': songTitle, 'artist': songArtist, 'album': songAlbum, 'genre': songGenre, 
								'duration': songDuration, 'sortTitle': songSortTitle, 'sortArtist': songSortArtist }
								
		# place song in the "byLetter" dictionary for quick and easy searching later
		if firstLetter:
		
			if not firstLetter.isalpha():
				firstLetter = '0'
			
			self.byLetter[firstLetter].append(songID)
		
		# place song in the "byArtist" dictionary to quick and easy searching later
		if songArtist:
			a = SafeAscii(songArtist).upper()
			
			if not self.byArtist.has_key(a):
				self.byArtist[a] = []
				
			self.byArtist[a].append(songID)
		
		# place song in the "byGenre" dictionary for quick and easy searching later
		if songGenre:
			g = SafeAscii(songGenre).upper()
			
			if not self.byGenre.has_key(g):
				self.byGenre[g] = []
				
			self.byGenre[g].append(songID)
			
		
	
	#------------------------------------------------------------------------------------------------------------------#
	# Public methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def songExists(self, songID):
		# verify a song is in the library
		return self.songs.has_key(songID)
	#enddef songExists
	
	def getSong(self, songID):
		if self.songs.has_key(songID):
			return self.songs[songID]
		else:
			return None
	#enddef getSong
	
	def searchBy_Letter(self, theLetter):
		# returns:
		#	None	on error
		#	list	list of songIDs matching the search
		
		# sanitize data:
		theLetter = theLetter[0].upper()
		
		if (theLetter.isalpha() or theLetter == '0') and self.byLetter.has_key(theLetter):
		
			songList = self.byLetter[theLetter]
			return songList
		else:
			return None
	#enddef searchBy_Letter
	
	def searchBy_Artist(self, searchStr):
		# returns:
		#	None	on error
		#	list	list of songIDs matching the search
		
		try:
			# sanitize data:
			searchStr = SafeAscii(searchStr).upper()
			
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
			
			return matchedSongs

		except:
			return None
	#enddef searchBy_Artist
	
	def searchBy_Genre(self, searchStr):
		# returns:
		#	None	on error
		#	list	list of songIDs matching the search
		
		try:
			# sanitize data:
			searchStr = SafeAscii(searchStr).upper()
			
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
			
			return matchedSongs
			
		except:
			return None
	#enddef searchBy_Genre
	
	def searchBy_Title(self, searchStr):
		# returns:
		#	None	on error
		#	list	list of songIDs matching the search
		
		try:
			# sanitize data:
			searchStr = SafeAscii(searchStr).upper()
			
			# split into words
			searchWords = searchStr.split()
			escapedWords = []
			for w in searchWords:
				escapedWords.append(re.escape(w))
			
			# find artists where all words match
			matchedSongs = []

			for songID, songData in self.songs.items():
				allMatched = 0
				songTitle = SafeAscii(songData['title']).upper()
				for word in escapedWords:
					if re.search(word, songTitle):
						allMatched = 1
					else:
						allMatched = 0
						break
						
				if allMatched:
					matchedSongs.append(songID)
			
			return matchedSongs
			
		except:
			return None
	#enddef searchBy_Title
		
	def searchBy_Any(self, searchStr):
		# returns:
		#	None	on error
		#	list	list of songIDs matching the search
		
		try:
			# sanitize data:
			searchStr = SafeAscii(searchStr).upper()
			
			# split into words
			searchWords = searchStr.split()
			escapedWords = []
			for w in searchWords:
				escapedWords.append(re.escape(w))
			
			# find songs where all words match at least 1 of (artist, title, genre)
			matchedSongs = []

			for songID, songData in self.songs.items():
			
				artistMatched = 0
				songArtist = SafeAscii(songData['artist']).upper()
				for word in escapedWords:
					if re.search(word, songArtist):
						artistMatched = 1
					else:
						artistMatched = 0
						break
				if artistMatched:
					matchedSongs.append(songID)
				else:
					titleMatched = 0
					songTitle = SafeAscii(songData['title']).upper()
					for word in escapedWords:
						if re.search(word, songTitle):
							titleMatched = 1
						else:
							titleMatched = 0
							break
					if titleMatched:
						matchedSongs.append(songID)
					else:
						genreMatched = 0
						songGenre = SafeAscii(songData['genre']).upper()
						for word in escapedWords:
							if re.search(word, songGenre):
								genreMatched = 1
							else:
								genreMatched = 0
								break
						if genreMatched:
							matchedSongs.append(songID)
							
					#endif titleMatched
				#endif artistMatched
				
			#endfor 
			
			return matchedSongs
		
		except:
			return None
	#enddef searchBy_Any
	