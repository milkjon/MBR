#----------------------------------------------------------------------------------------------------------------------#
#	MBRadio
#	iTunesLibrary.py
#	
#	Implements reading iTunes XML library
#
#	The class iTunesLibrary subclasses MusicLibrary
#
#	Please set tab-width to 4 characters! Lines should be 120 characters wide.
#----------------------------------------------------------------------------------------------------------------------#


import MusicLibrary
import xml.parsers.expat
import Debug

class iTunesLibrary(MusicLibrary.MusicLibrary):
		
	def load(self, path):
		
		Debug.out("   Parsing iTunes XML...")
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		p.buffer_text = True
		p.ParseFile(file(path))
		
		MusicLibrary.MusicLibrary.load(self)
		
		Debug.out("   Loaded " + str(len(self.songs)) + " songs!")
		
	# Private variables
	
	inDict = 0
	inKey = 0
	inTracks = 0
	inTrack = 0
	inData = 0
	currentKey = ''
	skipRest = 0
	songData = { }
		
	# Private methods:
	
	def start_element(self, name, attrs):
		if self.skipRest:
			return
			
		if name == u'key':
			self.inKey = 1
		elif name == u'dict':
			self.inDict = 1
		elif name == u'string' or name == u'integer':
			self.inData = 1

	def end_element(self, name):
		if self.skipRest:
			return
			
		if name == u'key':
			self.inKey = 0
		elif name == u'dict':
			self.inDict = 0

			if self.inTracks and self.inTrack:
				self.addSong(self.songData)
				self.inTrack = 0
				self.currentKey = ""
				songData = { }
				
		self.inData = 0
		
	def char_data(self, data):
		if self.skipRest:
			return
			
		if self.inKey:
			if data == u'Playlists':
				self.skipRest = 1
				return
			elif data == u'Tracks':
				self.inTracks = 1
				return
			elif self.inTracks:
				self.currentKey = data
				
				if data == u'Track ID':
					self.inTrack = 1
					self.songData = {}
					self.songData['id'] = u''
					self.songData['title'] = u''
					self.songData['artist'] = u''
					self.songData['album'] = u''
					self.songData['genre'] = u''
					self.songData['duration'] = u''
					self.songData['sortTitle'] = u''
					self.songData['sortArtist'] = u''
					
		elif self.inData and self.inTracks and self.inTrack:
			if self.currentKey == u'Track ID':
				self.songData['id'] = data
			elif self.currentKey == u'Name':
				self.songData['title'] = data
			elif self.currentKey == u'Artist':
				self.songData['artist'] = data
			elif self.currentKey == u'Album':
				self.songData['album'] = data
			elif self.currentKey == u'Genre':
				self.songData['genre'] = data
			elif self.currentKey == u'Total Time':
				self.songData['duration'] = data
			elif self.currentKey == u'Sort Name':
				self.songData['sortTitle'] = data
			elif self.currentKey == u'Sort Artist':
				self.songData['sortArtist'] = data
					