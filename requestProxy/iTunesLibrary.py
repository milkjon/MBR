#----------------------------------------------------------------------------------------------------------------------#
#  MBRadio
#
#  iTunes XML DB Implementation
#
#  iTunesLibrary subclasses MusicLibrary
#----------------------------------------------------------------------------------------------------------------------#

import MusicLibrary
import xml.parsers.expat

class iTunesLibrary(MusicLibrary.MusicLibrary):
		
	def load(self, path):
		
		print "   Parsing iTunes XML..."
		p = xml.parsers.expat.ParserCreate()
		p.StartElementHandler = self.start_element
		p.EndElementHandler = self.end_element
		p.CharacterDataHandler = self.char_data
		p.ParseFile(file(path))
		
		MusicLibrary.MusicLibrary.load(self)
		
		print "   Loaded " + str(self.songCount) + " songs!"
		
	# Private variables
	
	inDict = 0
	inKey = 0
	inTracks = 0
	inTrack = 0
	inData = 0
	currentKey = ''
	skipRest = 0
	songID = ''
	songTitle = ''
	songArtist = ''
	songAlbum = ''
	songGenre = ''
	songDuration = ''
					
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
				self.addSong(self.songID, self.songTitle, self.songArtist, self.songAlbum, self.songGenre, self.songDuration)
				self.inTrack = 0
				
		self.inData = 0
		
	def char_data(self, data):
		if self.skipRest:
			return
			
		if self.inKey:
			if data == u'Playlists':
				self.skipRest = 1
				return
			
			if self.inTracks:
				self.currentKey = data
				
				if data == u'Track ID':
					self.inTrack = 1
					self.songID = ''
					self.songTitle = ''
					self.songArtist = ''
					self.songAlbum = ''
					self.songGenre = ''
					self.songDuration = ''
					
			else:
				if data == u'Tracks':
					self.inTracks = 1
		
		elif self.inData and self.inTracks and self.inTrack:
				if self.currentKey == u'Track ID':
					self.songID = int(data)
				elif self.currentKey == u'Name':
					self.songTitle = data
				elif self.currentKey == u'Artist':
					self.songArtist = data
				elif self.currentKey == u'Album':
					self.songAlbum = data
				elif self.currentKey == u'Genre':
					self.songGenre = data
				elif self.currentKey == u'Total Time':
					self.songDuration = int(data)
					