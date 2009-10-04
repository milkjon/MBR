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

class iTunesLibrary(MusicLibrary.MusicLibrary):
		
	def load(self, path):
		
		Debug.out("   Parsing iTunes XML...")
		
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
	# Private variables (used by the XML parser)
	#------------------------------------------------------------------------------------------------------------------#
	
	inDict = 0
	inKey = 0
	inTracks = 0
	inTrack = 0
	inData = 0
	currentKey = ''
	skipRest = 0
	songData = { }
		
	#------------------------------------------------------------------------------------------------------------------#
	# Private methods:
	#------------------------------------------------------------------------------------------------------------------#
	
	def start_element(self, name, attrs):
		if self.skipRest:
			return
			
		if name == u'key':
			self.inKey = 1
		elif name == u'dict':
			self.inDict = 1
		elif name == u'string' or name == u'integer':
			self.inData = 1
	#enddef start_element()
	
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
	#enddef end_element()
	
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
					self.songData.update({'id':u'', 'title':u'', 'artist':u'', 'album':u'', 'genre':u'',
											'duration':u'', 'sortTitle':u'', 'sortArtist':u''})
					
		#endif self.inKey
					
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
		#endif self.inData and self.inTracks and self.inTrack
		
	#enddef char_data()

#endclass iTunesLibrary