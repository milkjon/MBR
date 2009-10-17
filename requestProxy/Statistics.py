#	vim: set tabstop=4 columns=120 shiftwidth=4:
#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	Statistics.py
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#
#----------------------------------------------------------------------------------------------------------------------#

import string, unicodedata, time, os, os.path
import xml.parsers.expat
from xml.parsers.expat import ExpatError
import Debug

def NiceAscii(theString):
	"""	Transform a unicode string into an 8-bit ascii string, in a nice way.
		Makes use of the unicodedata.normalize() function to try to transform non-ascii characters into the closest
		ascii match. (simply calling .encode('ascii') results in not-very-nice results :P )
	"""
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
#enddef NiceAscii()

def TitleCase(s):
        return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                      lambda mo: mo.group(0)[0].upper() +
                                 mo.group(0)[1:].lower(),
                      s)
#enddef TitleCase()

class LogError(Exception):
	pass

class Statistics:
	
	def __init__(self):
		self.byArtist = {}
		self.byGenre = {}
		self.bySong = {}
		self.bySongID = {}
	
	def loadFromLog(self, logFile):
		
		Debug.out("Loading log " + logFile)
		
		if os.path.isfile(logFile):
			statinfo = os.stat(logFile)
			if not statinfo.st_size:
				raise LogError("Log has zero length")
		else:
			raise LogError("Log doesn't exist!")
		
		try:
			f = open(logFile, 'r')
		except IOError as err:
			raise LogError("Parsing log failed on IOError: " + str(errstr))
				
		t1 = time.time()
		
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		p.buffer_text = True
			
		try:
			p.ParseFile(f)
			Debug.out("   Loaded", self.numLoaded, "rows in", round(time.time() - t1,5), "seconds")
		except IOError as err:
			raise LogError("Parsing log failed on IOError: " + str(IOError))
		except ExpatError as err:
			raise LogError("Parsing log failed on XML ExpatError: " + str(err))
		finally:
			f.close()
			
	#enddef loadLog()
	
	def addSong(self, songInfo):
		
		songTitle = NiceAscii(songInfo['title'].strip()).lower()
		songArtist = NiceAscii(songInfo['artist'].strip()).lower()
		songGenre = NiceAscii(songInfo['genre'].strip()).lower()
		songID = songInfo['songID']
		timestamp = long(songInfo['time'])
		
		if songArtist and songArtist != '[Unknown]':
			songName = songArtist + ' - ' + songTitle
		else:
			songName = songTitle
		
		if songName:
			if not songName in self.bySong:
				self.bySong[songName] = []
			self.bySong[songName].append(timestamp)
			
		if songArtist:
			if not songArtist in self.byArtist:
				self.byArtist[songArtist] = []
			self.byArtist[songArtist].append(timestamp)
		
		if songGenre:
			if not songGenre in self.byGenre:
				self.byGenre[songGenre] = []
			self.byGenre[songGenre].append(timestamp)
			
		if songID:
			if not songID in self.bySongID:
				self.bySongID[songID] = []
			self.bySongID[songID].append(timestamp)
		
	
	def getTopArtists(self, count, numDays):
		
		if numDays == 'all':
			period = 0
		else:
			period = time.time() - (numDays * 24 * 60 * 60) # 24 hrs * 60 min * 60 sec

		listToSort = []
		for artist in self.byArtist.keys():
			filteredSongs = [tstamp for tstamp in self.byArtist[artist] if tstamp >= period]
			listToSort.append( (len(filteredSongs), artist) )
		listToSort.sort()
		listToSort.reverse()
		
		slicedList = listToSort[0:count]
		resultList = [ (TitleCase(artist), num) for (num, artist) in slicedList ]
		
		return resultList
		
	def getTopSongs(self, count, numDays):
	
		if numDays == 'all':
			period = 0
		else:
			period = time.time() - (numDays * 24 * 60 * 60) # 24 hrs * 60 min * 60 sec

		listToSort = []
		for title in self.bySong.keys():
			filteredSongs = [tstamp for tstamp in self.bySong[title] if tstamp >= period]
			listToSort.append( (len(filteredSongs), title) )
		listToSort.sort()
		listToSort.reverse()
		
		slicedList = listToSort[0:count]
		resultList = [ (TitleCase(song), num) for (num, song) in slicedList ]
		
		return resultList
		
	def getTopGenres(self, count, numDays):
	
		if numDays == 'all':
			period = 0
		else:
			period = time.time() - (numDays * 24 * 60 * 60) # 24 hrs * 60 min * 60 sec

		listToSort = []
		for genre in self.byGenre.keys():
			filteredSongs = [tstamp for tstamp in self.byGenre[genre] if tstamp >= period]
			listToSort.append( (len(filteredSongs), genre) )
		listToSort.sort()
		listToSort.reverse()
		
		slicedList = listToSort[0:count]
		resultList = [ (TitleCase(genre), num) for (num, genre) in slicedList ]
		
		return resultList
		
	def getMostRecentBy_SongID(self, songID):
	
		try:
			songIDList = self.bySongID[songID]
		except LookupError:
			return None
			
		if not songIDList:
			return None
			
		listToSort = list(songIDList)
		listToSort.sort()
		listToSort.reverse()
		
		return listToSort[0]
		
	def getMostRecentBy_Artist(self, artist):
		
		try:
			artistList = self.byArtist[artist]
		except LookupError:
			return None
			
		if not artistList:
			return None
			
		listToSort = list(artistList)
		listToSort.sort()
		listToSort.reverse()
		
		return listToSort[0]
	
	
#endclass Statistics


class PlayedStatistics(Statistics):
	
	currentTag = ''
	inSong = 0
	numLoaded = 0
	playData = {}
	
	def start_element(self, name, attrs):	
		if name == u'played':
			self.playData.update({'time': attrs['time'], 'songID':'', 'artist':'', 'title':'', 'genre':''})
		elif name == u'song':
			self.inSong = 1
			try:
				self.playData['songID'] = attrs['id']
			except LookupError:
				pass
		self.currentTag = name
	#enddef start_element()
	
	def end_element(self, name):
		if name == u'song':
			# add song to stat db
			self.addSong(self.playData)
			self.inSong = 0
			self.numLoaded += 1
	#enddef end_element()
	
	def char_data(self, data):
		if self.inSong:
			if self.currentTag == u'artist':
				self.playData['artist'] = data
			elif self.currentTag == u'title':
				self.playData['title'] = data
			elif self.currentTag == u'genre':
				self.playData['genre'] = data
	#enddef char_data()
		
#endclass PlayedStatistics(Statistics)

	
class RequestStatistics(Statistics):

	currentTag = ''
	inSong = 0
	numLoaded = 0
	playData = {}

	def start_element(self, name, attrs):	
		if name == u'request':
			self.playData.update({'time': '', 'songID':'', 'artist':'', 'title':'', 'genre':''})
		elif name == u'song':
			self.inSong = 1
			try:
				self.playData['songID'] = attrs['id']
			except LookupError:
				pass
		self.currentTag = name
	#enddef start_element()
	
	def end_element(self, name):
		if name == u'song' and self.inSong:
			# add song to stat db
			self.addSong(self.playData)
			self.inSong = 0
			self.numLoaded += 1
	#enddef end_element()
	
	def char_data(self, data):
		if self.inSong:
			if self.currentTag == u'artist':
				self.playData['artist'] = data
			elif self.currentTag == u'title':
				self.playData['title'] = data
			elif self.currentTag == u'genre':
				self.playData['genre'] = data
		elif self.currentTag == u'time':
			self.playData['time'] = data
	#enddef char_data()
	
#endclass RequestStatistics(Statistics)