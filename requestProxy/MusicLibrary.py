#	vim: set tabstop=4 columns=120 shiftwidth=4:
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

import string, re, unicodedata, time, gc

# local imports
import Debug


def SafeAscii(theString):
	# transforms a string (which may be in unicode) into 7-bit ASCII
	
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
	
#enddef SafeAscii()

def	String2SafeAsciiWordList(theString):
	# Transforms a string into a list consisting of the individual words in the string, where each word has
	# been translated into lower-case 7-bit ASCII and escaped for use in a regular-expression search.
	#
	# NB: a "word" is specified by the presence of whitespace characters found inbetween any non-whitespace
	#     characters, as specified by the python method str.split()
	#
	#	arguments:
	#		theString  as  string  "word1 word2..."
	#	returns:
	#		list  as [word1, word2, ... ]
	
	# transform string into lower-case ASCII:
	asciiStr = SafeAscii(theString).lower()
	
	# split string into individual words using the .split() method
	asciiWords = asciiStr.split()
	
	return asciiWords
			
#enddef	String2SafeAsciiWordList()

def FirstAlphanumericChar(theString):
	asciiStr = SafeAscii(theString).lower()
	for c in theString:
		if c.isalnum():
			return c.lower()
	return '0'

class MusicLibrary:
	
	#------------------------------------------------------------------------------------------------------------------#
	# Init
	#------------------------------------------------------------------------------------------------------------------#
	
	def __init__(self):
		
		# songs dictionary
		#	Holds all of the songs in the library
		#	Format:		keys: 	 <songID> (string)
		#				values:	 dict{ 'artist': (ustring), 'title': (ustring), 'album': (ustring), 'genre': (ustring), 
		#						       'duration': (integer), 'sort-artist': (ustring), 'sort-title': (ustring) }
		self.songs = {}
		
		# byLetter dictionary
		#	Holds lists of songIDs organized by first letter (for fast searching)
		#	Format:		keys:	 '0', 'A', 'B', 'C', .... 'Z'
		#				values:	 list[(songID1), (songID2),...]
		self.byLetter = {}
		
		# byGenre dictionary
		#	Holds lists of songIDs organized by song genre (for fast searching)
		#	Format:		keys:	 <genre-name>  (as string)
		#				values:	 list[(songID1), (songID2),...]
		self.byGenre = {}
		
		# byArtist dictionary
		#	Holds lists of songIDs organized by song artist (for fast searching)
		#	Format:		keys:	 <artist-name>  (as string)
		#				values:	 list[(songID1), (songID2),...]
		self.byArtist = {}
		
		asciiLetters = string.ascii_lowercase
		for c in asciiLetters:
			self.byLetter[c] = []
		self.byLetter['0'] = []
		
	#enddef __init__()
		
	def load(self):
		# Details must be implemented by the subclass!!
		pass
		
	#enddef load()
	
	def reset(self):
		
		self.songs.clear()
		self.byGenre.clear()
		self.byArtist.clear()
		for letter in self.byLetter.keys():
			del self.byLetter[letter]
			self.byLetter[letter] = []
			
		gc.collect()
		
	#enddef reset()
	
	
	
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#

	def addSong(self, songData):
		# Add a song to the library and update entries in the search lookuptables
		#	arguments:
		#		songData  as  dict { 'id', 'artist', 'title', 'album', 'genre', 'duration', ('sortTile', 'sortArtist') }
		# 	returns:
		#		(void)
		
		songID = songData['id']
		songArtist = songData['artist'].strip()
		songTitle = songData['title'].strip()

		if not songArtist and not songTitle:
			# no good tag data (no artist, no title) just skip it. too bad.
			return
		
		if not songArtist:
			songArtist = u'[Unknown]'
		if not songTitle:
			songTitle = u'[Unknown]'
		
		songGenre = songData['genre'].strip()
		songAlbum = songData['album'].strip()

		songDuration = 0
		try:
			songDuration = long(songData['duration'].strip())
		except ValueError:
			pass
			
		
		songSortTitle = ''
		if songData.has_key('sortTitle') and songData['sortTitle']:
			songSortTitle = songData['sortTitle'].strip()
		if not songSortTitle:
			songSortTitle = songTitle
		
		songSortArtist = ''
		if songData.has_key('sortArtist') and songData['sortArtist']:
			songSortArtist = songData['sortArtist'].strip()
		if not songSortArtist:
			songSortArtist = songArtist
		
		self.songs[songID] = {'title': songTitle, 'artist': songArtist, 'album': songAlbum, 'genre': songGenre, 
								'duration': songDuration, 'sortTitle': songSortTitle, 'sortArtist': songSortArtist }
								
		# place song in the "byLetter" dictionary for quick and easy searching later
		if songSortArtist != u'[Unknown]':
			firstLetter = FirstAlphanumericChar(songSortArtist)
		else:
			firstLetter = FirstAlphanumericChar(songSortTitle)
		
		if not firstLetter.isalpha():
			firstLetter = '0'
		self.byLetter[firstLetter].append(songID)
		
		# place song in the "byArtist" dictionary to quick and easy searching later
		if songArtist != u'[Unknown]':
			a = SafeAscii(songArtist).lower()
			if not self.byArtist.has_key(a):
				self.byArtist[a] = []
			self.byArtist[a].append(songID)
		
		# place song in the "byGenre" dictionary for quick and easy searching later
		if songGenre:
			g = SafeAscii(songGenre).lower()
			if not self.byGenre.has_key(g):
				self.byGenre[g] = []
			self.byGenre[g].append(songID)
			
	#enddef addSong()
	
	
	#------------------------------------------------------------------------------------------------------------------#
	# Public methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def songExists(self, songID):
		# Verify a song is in the library
		#	arguments:
		#		songID	as  string
		#	returns:
		#		boolean
		
		return songID in self.songs
		
	#enddef songExists()
	
	def getSong(self, songID):
		# Lookup a song in the database by songID
		#	arguments:
		#		songID	as  string
		#	returns:
		#		dict	if song exists, the song dictionary object
		#		None	if the song does not exist
		
		if songID in self.songs:
			return self.songs[songID]
		else:
			return None
			
	#enddef getSong()
	
	def searchBy_Letter(self, theLetter):
		# Search the library by a single letter. This returns all "(Artist -) Title" where the first letter begins
		# with the specified letter.
		#
		#	arguments:
		#		theLetter	as  string of length 1, where (theLetter == '0' OR theLetter in string.ascii_lowercase)
		#	returns:
		#		None	On error only
		#		list	If results are found, [songID1, songID2, ...]
		#		list	If no results are found, []
		
		# sanitize data:
		theLetter = theLetter[0].lower()
		
		if (theLetter.isalpha() or theLetter == '0') and self.byLetter.has_key(theLetter):
			Debug.out("Searching letter", theLetter)
			
			songList = self.byLetter[theLetter]
			return songList
		else:
			return None
			
	#enddef searchBy_Letter()
	
	def searchBy_Artist(self, searchStr):
		# Search the library by Artist Name where searchStr matches the artist name.
		# NB: If searchStr consists of multiple words then ALL words must be found within the artist name to make a match.
		#
		#	arguments:
		#		searchStr	as  string	"word1 word2..."
		#	returns:
		#		None	On error only
		#		list	If results are found, [songID1, songID2, ...]
		#		list	If no results are found, []
		
		try:
			wordList = String2SafeAsciiWordList(searchStr)
			
			# find artists where all words match
			
			Debug.out("Searching", len(self.byArtist.keys()), "artists")
			t1 = time.time()
			
			matchedSongs = []
			for artist in self.byArtist.keys():
				matches = [word for word in wordList if word in artist]
				if len(matches) == len(wordList):
					matchedSongs.extend(self.byArtist[artist])
			
			Debug.out("  Found", len(matchedSongs), "in", round(time.time()-t1,6), "seconds")

			return matchedSongs

		except:
			return None
			
	#enddef searchBy_Artist()
	
	def searchBy_Genre(self, searchStr):
		# Search the library by Genre Name where searchStr matches the genre name.
		# NB: If searchStr consists of multiple words then ALL words must be found within the genre name to make a match.
		#
		#	arguments:
		#		searchStr	as  string	"word1 word2..."
		#	returns:
		#		None	On error only
		#		list	If results are found, [songID1, songID2, ...]
		#		list	If no results are found, []
		
		try:
			wordList = String2SafeAsciiWordList(searchStr)
			
			# find genres where all words match
			
			Debug.out("Searching", len(self.byGenre.keys()), "genres")
			t1 = time.time()
			
			matchedSongs = []
			for genre in self.byGenre.keys():
				matches = [word for word in wordList if word in genre]
				if len(matches) == len(wordList):
					matchedSongs.extend(self.byGenre[genre])
			
			Debug.out("  Found", len(matchedSongs), "in", round(time.time()-t1,6), "seconds")

			return matchedSongs

		except:
			return None
	#enddef searchBy_Genre
	
	def searchBy_Title(self, searchStr):
		# Search the library by song title where searchStr matches the title.
		# NB: If searchStr consists of multiple words then ALL words must be found within the title to make a match.
		#
		#	arguments:
		#		searchStr	as  string	"word1 word2..."
		#	returns:
		#		None	On error only
		#		list	If results are found, [songID1, songID2, ...]
		#		list	If no results are found, []
		
		try:
			wordList = String2SafeAsciiWordList(searchStr)
			
			# find titles where all words match
			
			Debug.out("Searching", len(self.songs.items()), "song titles")
			t1 = time.time()
			
			matchedSongs = []
			for songID, songData in self.songs.items():
				songTitle = SafeAscii(songData['title']).lower()
				matches = [word for word in wordList if word in songTitle]
				if len(matches) == len(wordList):
					matchedSongs.append(songID)
			
			Debug.out("  Found", len(matchedSongs), "in", round(time.time()-t1,6), "seconds")

			return matchedSongs
			
		except:
			return None
	#enddef searchBy_Title
	
	def searchBy_Any(self, searchStr):
		# Search the library where searchStr matches any of (title|artist|genre)
		# NB: If searchStr consists of multiple words then ALL words must be found within at least ONE of the
		#     fields (title|artist|genre) to make a match.
		#
		#	arguments:
		#		searchStr	as  string	"word1 word2..."
		#	returns:
		#		None	On error only
		#		list	If results are found, [songID1, songID2, ...]
		#		list	If no results are found, []
		
		try:
			wordList = String2SafeAsciiWordList(searchStr)
			
			# find songs where all words match at least 1 of (artist, title, genre)
			
			Debug.out("Searching", len(self.songs.items()), "songs")
			t1 = time.time()
			
			matchedSongs = []
			for songID, songData in self.songs.items():
				
				# search by artist first
				songArtist = SafeAscii(songData['artist']).lower()
				matches = [word for word in wordList if word in songArtist]
				if len(matches) == len(wordList):
					matchedSongs.append(songID)
					continue
				
				# search by title
				songTitle = SafeAscii(songData['title']).lower()
				matches = [word for word in wordList if word in songTitle]
				if len(matches) == len(wordList):
					matchedSongs.append(songID)
					continue
					
				# search by genre
				songGenre = SafeAscii(songData['genre']).lower()
				matches = [word for word in wordList if word in songGenre]
				if len(matches) == len(wordList):
					matchedSongs.append(songID)
					continue
			#endfor

			Debug.out("  Found", len(matchedSongs), "in", round(time.time()-t1,6), "seconds")

			return matchedSongs
		
		except:
			return None
	#enddef searchBy_Any
	
