#	vim: set tabstop=4 columns=120 shiftwidth=4:
#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	Statistics.py
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#
#----------------------------------------------------------------------------------------------------------------------#

import string, unicodedata, re, time, xml.parsers.expat
import Debug

def SafeAscii(theString):
	return unicodedata.normalize('NFKD', unicode(theString)).encode('ascii','ignore')
#enddef SafeAscii()

def TitleCase(s):
        return re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                      lambda mo: mo.group(0)[0].upper() +
                                 mo.group(0)[1:].lower(),
                      s)
#enddef TitleCase()

class Statistics:
	
	def __init__(self):
		self.byArtist = {}
		self.byGenre = {}
		self.bySong = {}
	
	def loadFromLog(self, logFile):
		# must be implemented by the subclass
		pass
	
	def addSong(self, songInfo):
		
		songTitle = SafeAscii(songInfo['title'].strip()).lower()
		songArtist = SafeAscii(songInfo['artist'].strip()).lower()
		songGenre = SafeAscii(songInfo['genre'].strip()).lower()
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
		for title in self.byTitle.keys():
			filteredSongs = [tstamp for tstamp in self.byTitle[title] if tstamp >= period]
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
		
#endclass Statistics


class PlayedStatistics(Statistics):
	
	currentTag = ''
	inSong = 0
	numLoaded = 0
	playData = {}
	
	def loadFromLog(self, logFile):
		
		Debug.out("Loading played.xml...")

		t1 = time.time()
		
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		p.buffer_text = True
		try:
			p.ParseFile(file(logFile))
			Debug.out("   Loaded", self.numLoaded, "rows in", round(time.time() - t1,5), "seconds")
		except IOError:
			pass
			
	def start_element(self, name, attrs):	
		if name == u'played':
			self.playData.update({'time': attrs['time'], 'artist':'', 'title':'', 'genre':''})
		elif name == u'song':
			self.inSong = 1
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
	
	def loadFromLog(self, logFile):
		
		Debug.out("Loading requests.xml...")

		t1 = time.time()
		
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		p.buffer_text = True
		try:
			p.ParseFile(file(logFile))
			Debug.out("   Loaded", self.numLoaded, "rows in", round(time.time() - t1,5), "seconds")
		except IOError:
			pass

	def start_element(self, name, attrs):	
		if name == u'request':
			self.playData.update({'time': '', 'artist':'', 'title':'', 'genre':''})
		elif name == u'song':
			self.inSong = 1
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