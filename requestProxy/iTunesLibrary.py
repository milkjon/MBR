#	vim: set tabstop=4 columns=120 shiftwidth=4:
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

import xml.parsers.expat
import time

# local imports
import MusicLibrary
import Debug

class ParserData:
	skipRest = 0
	inKey = 0
	inDict = 0
	inTracklist = 0
	inTrack = 0
	inData = 0
	inKind = 0
	dontAddThisTrack = 0
	key = ''
	songData = {}
	def resetSongData(self):
		self.songData.update( {'id':u'','title':u'','artist':u'','sortTitle':u'','sortArtist':u'',\
								'album':u'','genre':u'','duration':u''} )
#endclass ParserData

class iTunesLibrary(MusicLibrary.MusicLibrary):
	
	parser = None
	
	#------------------------------------------------------------------------------------------------------------------#
	# Load the library from the itunes xml
	#------------------------------------------------------------------------------------------------------------------#
	
	def load(self, path):
		
		Debug.out("   Parsing iTunes XML...")
		
		# reset parse variables
		self.parser = ParserData()
		
		t1 = time.time()
		
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		
		# important! if you don't set buffer_text to true, the CharacterDataHandler does not always return the
		# full text inside of a <tag></tag> pair! this will cause some data to be loaded incompletely unless
		# the code implements its own buffering!
		p.buffer_text = True
		
		p.ParseFile(file(path))
		
		t2 = time.time()
		
		Debug.out("   Loaded", len(self.songs), "songs!")
		Debug.out("   Parsing took", round(t2 - t1,4), "seconds")
		
	#enddef load()
	
		
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def start_element(self, name, attrs):
		if self.parser.skipRest:
			return
			
		if name == u'key':
			self.parser.inKey = 1
		elif name == u'dict':
			self.parser.inDict = 1
		elif name == u'string' or name == u'integer':
			self.parser.inData = 1
	#enddef start_element()
	
	def end_element(self, name):
		if self.parser.skipRest:
			return
			
		if name == u'key':
			self.parser.inKey = 0
		elif name == u'dict':
			self.parser.inDict = 0

			if self.parser.inTracklist and self.parser.inTrack:
				if not self.parser.dontAddThisTrack:
					self.addSong(self.parser.songData)
				self.parser.dontAddThisTrack = 0
				self.parser.inTrack = 0
				self.parser.key = ""
		elif name == u'string':
			if self.parser.inKind:
				self.parser.inKind = 0
				
		self.parser.inData = 0
	#enddef end_element()
	
	def char_data(self, data):
		if self.parser.skipRest:
			return
		
		if self.parser.inKind:
			if "video" in data or "stream" in data or "URL" in data:
				self.parser.dontAddThisTrack = 1
		
		if self.parser.inKey:
			if data == u'Playlists':
				self.parser.skipRest = 1
				return
			elif data == u'Tracks':
				self.parser.inTracklist = 1
				return
			
			if self.parser.inTracklist:
				self.parser.key = data
				
				if data == u'Track ID':
					self.parser.inTrack = 1
					self.parser.resetSongData()
				elif data == u'Kind':
					self.parser.inKind = 1
					
		#endif self.parser.inKey
					
		elif self.parser.inData and self.parser.inTrack:
			if self.parser.key == u'Persistent ID':
				self.parser.songData['id'] = data
			elif self.parser.key == u'Name':
				self.parser.songData['title'] = data
			elif self.parser.key == u'Artist':
				self.parser.songData['artist'] = data
			elif self.parser.key == u'Album':
				self.parser.songData['album'] = data
			elif self.parser.key == u'Genre':
				self.parser.songData['genre'] = data
			elif self.parser.key == u'Total Time':
				self.parser.songData['duration'] = data
			elif self.parser.key == u'Sort Name':
				self.parser.songData['sortTitle'] = data
			elif self.parser.key == u'Sort Artist':
				self.parser.songData['sortArtist'] = data
		#endif self.parser.inData and self.parser.inTrack
		
	#enddef char_data()

#endclass iTunesLibrary
