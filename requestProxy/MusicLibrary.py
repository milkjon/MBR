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

import string, unicodedata, time

# local imports
import Debug

def NiceAscii(theString):
	"""	Transform a unicode string into an 8-bit ascii string, in a nice way.
		Makes use of the unicodedata.normalize() function to try to transform non-ascii characters into the closest
		ascii match. (simply calling .encode('ascii') results in not-very-nice results :P )
	"""
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
#enddef NiceAscii()

ascii_alphanumchars =  string.ascii_lowercase + string.digits

def FirstAlnum(asciiStr):
	"""	Return the first character of the string that is alphanumeric
		Assumes theString is already a lower-case ascii string.
	"""
	for c in asciiStr:
		if c in ascii_alphanumchars:
			return c
	return '0'
#enddef FirstAlnum()

def StripLeadingNonAlnum(theString):
	"""	Strip any leading characters of theString that are not alphanumeric, as defined by .isalnum()
		This is used to help the sorting function so that items beginning with punctuation are not sorted
		to the top of the list. This results in a more natural sort result.
	"""
	i = 0
	for c in theString:
		if c.isalnum():
			break
		i += 1
	return theString[i:]
#enddef StripLeadingNonAlnum()

def MakeWordlist(theString):
	"""	Turn a string in a list of 2-tuples (lowercase-ascii-word, lowercase-unicode-word) for each "word" in the string,
		where a word is defined by the presence of whitespae as defined by string.split()
	"""
	return [ (NiceAscii(word).lower(), word.lower()) for word in theString.split() ]
#enddef MakeWordlist()

class MusicLibrary:
	
	#------------------------------------------------------------------------------------------------------------------#
	# Init
	#------------------------------------------------------------------------------------------------------------------#
	
	def __init__(self):
		
		# songs dictionary
		#	Holds all of the songs in the library
		#	Format:		keys: 	 <songID> (string)
		#				values:	 dict{ 'artist': (ustring), 'title': (ustring), 'album': (ustring), 
		#								'genre': (ustring), 'duration': (long) }
		#						       
		self.songs = {}
		
		# byLetter dictionary
		#	Holds lists of songIDs organized by first letter (for fast searching)
		#	Format:		keys:	 '0', 'A', 'B', 'C', .... 'Z'
		#				values:	 list[(songID1), (songID2),...]
		self.byLetter = {}
		
		# byGenre dictionary
		#	Holds lists of songIDs organized by song genre (for fast searching)
		#	Format:		keys:	 <genre-name>  (as ascii-string)
		#				values:	 list[(songID1), (songID2),...]
		self.byGenre = {}
		
		# byArtist dictionary
		#	Holds lists of songIDs organized by song artist (for fast searching)
		#	Format:		keys:	 <artist-name>  (as unicode-string)
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
		
	#enddef reset()
	
	
	
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#

	def addSong(self, songData):
		""" Add a song to the library and update entries in the search lookuptables
			arguments:
				songData  as  dict { 'id', 'artist', 'title', 'album', 'genre', 'duration', 'sortTile', 'sortArtist' }
		 	returns:
				(void)
		"""
		
		songID = songData['id']
		songArtist = songData['artist'].strip()
		songTitle = songData['title'].strip()

		if not songArtist and not songTitle:
			# no good tag data (no artist, no title) just skip it. too bad.
			return
		
		songGenre = songData['genre'].strip()
		songAlbum = songData['album'].strip()

		songDuration = 0
		try:
			songDuration = long(songData['duration'].strip())
		except ValueError:
			pass
		
		songSortTitle = ''
		if songData['sortTitle']:
			songSortTitle = songData['sortTitle'].strip()
		if not songSortTitle:
			songSortTitle = songTitle
		songSortTitle = NiceAscii(songSortTitle).lower()
		
		songSortArtist = ''
		if songData['sortArtist']:
			songSortArtist = songData['sortArtist'].strip()
		if not songSortArtist:
			songSortArtist = songArtist
		songSortArtist = NiceAscii(songSortArtist).lower()
		
		# place song in the "byLetter" dictionary for quick and easy searching later
		if songSortArtist:
			firstLetter = FirstAlnum(songSortArtist)
		else:
			firstLetter = FirstAlnum(songSortTitle)
			
		if not firstLetter in string.ascii_lowercase:
			firstLetter = '0'
		self.byLetter[firstLetter].append(songID)
		
		
		songTitleLower = songTitle.lower()
		songArtistLower = songArtist.lower()
		songGenreLower = songGenre.lower()
		
		# place song in the "byArtist" dictionary to quick and easy searching later
		if songArtistLower:
			if not songArtistLower in self.byArtist:
				self.byArtist[songArtistLower] = []
			self.byArtist[songArtistLower].append(songID)
		
		# place song in the "byGenre" dictionary for quick and easy searching later
		if songGenreLower:
			if not songGenreLower in self.byGenre:
				self.byGenre[songGenreLower] = []
			self.byGenre[songGenreLower].append(songID)
		
		# add to the songs dictionary
		if not songArtist:
			songArtist = u'[Unknown]'
		if not songTitle:
			songTitle = u'[Unknown]'
		
		self.songs[songID] = \
			{	'title': songTitle, 'sortTitle': StripLeadingNonAlnum(songSortTitle), 
					'searchTitle': songTitleLower, 'searchTitleAscii': NiceAscii(songTitleLower).lower(),
				'artist': songArtist, 'sortArtist': StripLeadingNonAlnum(songSortArtist), 
					'searchArtist': songArtistLower, 'searchArtistAscii': NiceAscii(songArtistLower).lower(),
				'genre': songGenre, 'searchGenre': songGenreLower, 'searchGenreAscii': NiceAscii(songGenreLower).lower(), 
				'album': songAlbum, 'duration': songDuration
			}
			
	#enddef addSong()
	
	def makeSortingTuple(self, songID, sortBy):
		"""	Create an n-tuple used to sort a song list, based on the sorting rules given by the sortBy argument.
			This takes advantage of the default lexicographic sorting behavior of sort() on lists of tuples
		"""
		
		try:
			song = self.songs[songID]
		except LookupError:
			return tuple([chr(128) for i in range(len(sortBy)+1)])
		
		sortList=[]
		for field, dir in sortBy:
			try:
				if field == 'artist':
					fieldVal = song['sortArtist']
				elif field == 'title':
					fieldVal = song['sortTitle']
				else:
					fieldVal = StripLeadingNonAlnum(NiceAscii(song[field]).lower())
			except LookupError:
				sortList.append(chr(128))
			else:
				if not fieldVal or fieldVal == u'[Unknown]':
					sortList.append(chr(128))
				else:
					sortList.append(fieldVal)
		#end for
				
		sortList.append(songID)
		return tuple(sortList)

	#enddef makeSortingTuple()
	
	
	#------------------------------------------------------------------------------------------------------------------#
	# Public methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def songExists(self, songID):
		"""	Verify a song is in the library
			arguments:
				songID	as  string
			returns:
				boolean
		"""
		
		return songID in self.songs
		
	#enddef songExists()
	
	def getSong(self, songID):
		"""	Lookup a song in the database by songID
			arguments:
				songID	as  string
			returns:
				dict	if song exists, the song dictionary object
				None	if the song does not exist
		"""
		
		try:
			song = self.songs[songID]
			return song
		except LookupError:
			return None
			
	#enddef getSong()
	
	def sort_Songs(self, songlist, sortby):
		"""	Sort a list of songID's by the specified sortby paramaters
			arguments:
				songlist	as  list[songID, ... ] of valid songID's in the library
				sortby		as  list[ (field, direction), ... ] 
									where field in (title,artist,album,genre) and direction in (asc, desc)
			returns:
				list		as [songID, ... ] sorted by the sortby criteria
		"""
		t1 = time.time()
		
		listToSort = [self.makeSortingTuple(songID, sortby) for songID in songlist]
		listToSort.sort()
		listSorted = [sortTuple[-1] for sortTuple in listToSort]
		
		Debug.out("  Sorted", len(listSorted),"songs in", round(time.time()-t1,6), "seconds")
		
		return listSorted
		
	#enddef sort_Songs()
	
	def searchBy_Letter(self, theLetter):
		"""	Search the library by a single letter. This returns all "(Artist -) Title" where the first letter begins
			with the specified letter.
			
			arguments:
				theLetter	as  string of length 1, where (theLetter == '0' OR theLetter in string.ascii_lowercase)
			returns:
				None	On error only
				list	[songID1, songID2, ...]
		"""
		
		# sanitize data:
		theLetter = theLetter[0].lower()
		
		if (theLetter in string.ascii_lowercase or theLetter == '0') and theLetter in self.byLetter:
			Debug.out("Searching letter", theLetter)
			
			songList = self.byLetter[theLetter]
			return songList
		else:
			return None
			
	#enddef searchBy_Letter()
	
	def searchBy_Artist(self, searchStr):
		"""	Search the library by Artist Name where searchStr matches the artist name.
			NB: If searchStr consists of multiple words then ALL words must be found within the artist name to make a match.
			
			arguments:
				searchStr	as  string	"word1 word2..."
			returns:
				list	[songID1, songID2, ...] of songIDs that match the search criteria
		"""
		
		Debug.out("Searching", len(self.byArtist), "artists")
		t1 = time.time()
		
		wordList = MakeWordlist(searchStr)
		
		matchedSongs = []
		for artist in self.byArtist:
			asciiArtist = NiceAscii(artist)
			matches = [1 for (asciiWord, word) in wordList if asciiWord in asciiArtist or word in artist]
			if len(matches) == len(wordList):
				matchedSongs.extend(self.byArtist[artist])
		
		Debug.out("  Found", len(matchedSongs), "songs in", round(time.time()-t1,6), "seconds")

		return matchedSongs
			
	#enddef searchBy_Artist()
	
	def searchBy_Genre(self, searchStr):
		"""	Search the library by Genre Name where searchStr matches the genre name.
			NB: If searchStr consists of multiple words then ALL words must be found within the genre name to make a match.
			
			arguments:
				searchStr	as  string	"word1 word2..."
			returns:
				list	[songID1, songID2, ...] of songIDs that match the search criteria
		"""
		
		Debug.out("Searching", len(self.byGenre), "genres")
		t1 = time.time()
		
		wordList = MakeWordlist(searchStr)

		matchedSongs = []
		for genre in self.byGenre:
			asciiGenre = NiceAscii(genre)
			matches = [1 for (asciiWord, word) in wordList if asciiWord in asciiGenre or word in genre]
			if len(matches) == len(wordList):
				matchedSongs.extend(self.byGenre[genre])
		
		Debug.out("  Found", len(matchedSongs), "songs in", round(time.time()-t1,6), "seconds")

		return matchedSongs

	#enddef searchBy_Genre
	
	def searchBy_Title(self, searchStr):
		"""	Search the library by song title where searchStr matches the title.
			NB: If searchStr consists of multiple words then ALL words must be found within the title to make a match.
			
			arguments:
				searchStr	as  string	"word1 word2..."
			returns:
				list	[songID1, songID2, ...] of songIDs that match the search criteria
		"""
		
		Debug.out("Searching", len(self.songs), "song titles")
		t1 = time.time()
		
		wordList = MakeWordlist(searchStr)
		
		matchedSongs = []
		for songID, songData in self.songs.iteritems():
			songTitle = songData['searchTitle']
			asciiSongTitle = songData['searchTitleAscii']
			matches = [1 for (asciiWord, word) in wordList if asciiWord in asciiSongTitle or word in songTitle]
			if len(matches) == len(wordList):
				matchedSongs.append(songID)
		
		Debug.out("  Found", len(matchedSongs), "songs in", round(time.time()-t1,6), "seconds")

		return matchedSongs

	#enddef searchBy_Title
	
	def searchBy_Any(self, searchStr):
		"""	Search the library where searchStr matches any of (title|artist|genre)
			NB:	If searchStr consists of multiple words then ALL words must be found within at least ONE of the
				fields (title|artist|genre) to make a match.
			
			arguments:
				searchStr	as  string	"word1 word2..."
			returns:
				list	[songID1, songID2, ...] of songIDs that match the search criteria
		"""

		Debug.out("Searching", len(self.songs), "songs (artist, title, genre)")
		t1 = time.time()
		
		wordList = MakeWordlist(searchStr)
		
		matchedSongs = []
		for songID, songData in self.songs.iteritems():
			
			# search by artist first
			songArtist = songData['searchArtist']
			asciiSongArtist = songData['searchArtistAscii']
			matches = [1 for (asciiWord, word) in wordList if asciiWord in asciiSongArtist or word in songArtist]
			if len(matches) == len(wordList):
				matchedSongs.append(songID)
				continue
			
			# search by title
			songTitle = songData['searchTitle']
			asciisongTitle = songData['searchTitleAscii']
			matches = [1 for (asciiWord, word) in wordList if asciiWord in asciisongTitle or word in songTitle]
			if len(matches) == len(wordList):
				matchedSongs.append(songID)
				continue
				
			# search by genre
			songGenre = songData['searchGenre']
			songGenreAscii = songData['searchGenreAscii']
			matches = [1 for (asciiWord, word) in wordList if asciiWord in songGenreAscii or word in songGenre]
			if len(matches) == len(wordList):
				matchedSongs.append(songID)
				continue
		#endfor

		Debug.out("  Found", len(matchedSongs), "songs in", round(time.time()-t1,6), "seconds")

		return matchedSongs

	#enddef searchBy_Any
	
