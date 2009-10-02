# Will read and parse iTunes Library

# FIXME! Dirty implementation just a proof of concept

import time
import plistlib
import xml.parsers.expat
import os
import os.path
import xml.dom.minidom
import xml.sax.handler
import xml.sax
import pprint

path = os.path.join(os.path.expanduser('~'), 'Music\iTunes\iTunes Music Library.xml')
#path = '/Users/Shared/iTunes/iTunes Music Library.xml'
state = 0


def test():
	t1 = time.time()
	plist()
	t2 = time.time()
	print "time: ", t2-t1
	
	t1 = time.time()
	expat()
	t2 = time.time()
	print "time: ", t2-t1
	
	t1 = time.time()
	expat2()
	t2 = time.time()
	print "time: ", t2-t1
	
	t1 = time.time()
	sax()
	t2 = time.time()
	print "time: ", t2-t1

	#t1 = time.time()
	#minidom()
	#t2 = time.time()
	#print "time: ", t2-t1
	
def minidom():
	global path
	print "\nbegin minidom"
	d = xml.dom.minidom.parse(path)
	print "end minidom"

def plist():
	print "\nbegin plist"
	# Reads the whole plist and iterates thru it. Takes 9 seconds :(
	# Will need to use a real xml library.
	p = plistlib.readPlist(path)
	keys = p['Tracks'].keys()
	print str(len(keys)) + " tracks processed"
	print "end plist"

def _read():
	print "begin"
	with open(path) as f:
		s = f.read()
	print "end"

##### Expat

# States:
#   1 plist
#   2 dict
#   3 key ... Tracks
#   4 inside key
#   5 tracks dict
#   6 track dict
#   7 inside key
#   8 interesting key

track = []
trackCount = 0

def start_element(name, attrs):
	global state, track, trackCount
	if state == 0:
		if name == 'plist':
			state = 1
	elif state == 1: 
		if name == 'dict':
			state = 2
	elif state == 2:
		if name == 'key':
			state = 3
	elif state == 4:
		if name == 'dict':
			#print 'dict'
			state = 5
	elif state == 5:
		if name == 'dict':
			track = []
			trackCount = trackCount + 1
			state = 6
	elif state == 6:
		if name == 'key':
			state = 7

def end_element(name):
	global state
	if state == 3:
		if name == 'key':
			state = 2
	elif state == 5:
		if name == 'dict':
			state = 0
	elif state == 6:
		if name == 'dict':
			#print track
			state = 5
	elif state == 7:
		if name == 'key':
			state = 6
    
def char_data(data):
	global state, track
	if state == 3:
		if data == u'Tracks':
			#print 'Character data:', repr(data)
			state = 4
	elif state == 7:
		if data == u'Artist' or data == u'Name' or \
			data == u'Album' or data == u'Genre' or data == 'Track ID':
			state = 8
	elif state == 8:
		if data == u'':
			track.append(u'')
			
		track.append(data)
		state = 6

def expat():
	global trackCount
	trackCount = 0
	print "\nbegin expat"
	p = xml.parsers.expat.ParserCreate()
	p.StartElementHandler = start_element
	p.EndElementHandler = end_element
	p.CharacterDataHandler = char_data
	p.ParseFile(file(path))
	print str(trackCount) + " tracks processed"
	print "end expat"


gInDict = 0
gInKey = 0
gInTracks = 0
gInTrack = 0
gInData = 0
gCurrentKey = ""
gSkipAll = 0
	
def start_element2(name, attrs):
	global gSkipAll
	if gSkipAll:
		return
		
	global gInDict, gInKey, gInData
	if name == u'key':
		gInKey = 1
	elif name == u'dict':
		gInDict = 1
	elif name == u'string' or name == u'integer':
		gInData = 1

def end_element2(name):
	global gSkipAll
	if gSkipAll:
		return
		
	global trackCount, gInDict, gInKey, gInTracks, gInTrack, gInData
	global gTrackID, gTrackName, gTrackArtist, gTrackAlbum, gTrackGenre, gTrackDuration
	if name == u'key':
		gInKey = 0
	elif name == u'dict':
		gInDict = 0

		if gInTracks and gInTrack:
			gInTrack = 0
			trackCount = trackCount + 1
			try:
				print str(gTrackID) + " " + gTrackArtist + " - " + gTrackName
			except:
				pass
	gInData = 0
    
def char_data2(data):
	global gSkipAll
	if gSkipAll:
		return
		
	global trackCount, gInDict, gInKey, gInTracks, gInTrack, gInData, gCurrentKey
	global gTrackID, gTrackName, gTrackArtist, gTrackAlbum, gTrackGenre, gTrackDuration
	if gInKey:
		
		if data == u'Playlists':
			gSkipAll = 1
			return
		
		if gInTracks:
			gCurrentKey = data
			
			if data == u'Track ID':
				gInTrack = 1
				gTrackID = ''
				gTrackName = ''
				gTrackArtist = ''
				gTrackAlbum = ''
				gTrackGenre = ''
				gTrackDuration = ''
				
		else:
			if data == u'Tracks':
				gInTracks = 1
	
	elif gInData and gInTracks and gInTrack:
			if gCurrentKey == u'Track ID':
				gTrackID = int(data)
			elif gCurrentKey == u'Name':
				gTrackName = data
			elif gCurrentKey == u'Artist':
				gTrackArtist = data
			elif gCurrentKey == u'Album':
				gTrackAlbum = data
			elif gCurrentKey == u'Genre':
				gTrackGenre = data
			elif gCurrentKey == u'Total Time':
				gTrackDuration = int(data)

def expat2():
	global trackCount
	trackCount = 0
	print "\nbegin expat2"
	p = xml.parsers.expat.ParserCreate()
	p.StartElementHandler = start_element2
	p.EndElementHandler = end_element2
	p.CharacterDataHandler = char_data2
	p.ParseFile(file(path))
	print str(trackCount) + " tracks processed"
	print "end expat2"
 
class TrackHandler(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.inKey = 0
		self.inDict = 0
		self.inTracks = 0
		self.inTrack = 0
		self.inData = 0
		self.skipAll = 0
		
		self.reset()
		
	def reset(self):
		self.trackID = ""
		self.trackName = ""
		self.trackArtist = ""
		self.trackAlbum = ""
		self.trackGenre = ""
		self.trackDuration = ""
		
	def startElement(self, name, attributes):
		if self.skipAll:
			return
			
		if name == u'key':
			self.inKey = 1
		elif name == u'dict':
			self.inDict = 1
		elif name == u'string' or name == u'integer':
			self.inData = 1
					
	def endElement(self, name):
		if self.skipAll:
			return
			
		global trackCount
		if name == u'key':
			self.inKey = 0
		elif name == u'dict':
			self.inDict = 0
			if self.inTracks and self.inTrack:
				self.inTrack = 0
				trackCount = trackCount + 1
				trackstr = str(self.trackID) + " " + self.trackArtist + " - " + self.trackName
				print trackstr.encode('ascii','ignore')

		
		self.inData = 0

	def characters(self, data):
		if self.skipAll:
			return
			
		if self.inKey:
			self.currentKey = data
			
			if data == u'Playlists':
				self.skipAll = 1
				return
			
			if self.inTracks:
				if data == u'Track ID':
					self.inTrack = 1
					self.reset()
			else:
				if data == u'Tracks':
					self.inTracks = 1
		
		elif self.inData and self.inTracks and self.inTrack:
				if self.currentKey == u'Track ID':
					self.trackID = int(data)
				elif self.currentKey == u'Name':
					self.trackName = data
				elif self.currentKey == u'Artist':
					self.trackArtist = data
				elif self.currentKey == u'Album':
					self.trackAlbum = data
				elif self.currentKey == u'Genre':
					self.trackGenre = data
				elif self.currentKey == u'Total Time':
					self.trackDuration = int(data)

def sax():
	global trackCount
	trackCount = 0
	print "\nbegin sax"
	parser = xml.sax.make_parser(  )
	handler = TrackHandler(  )
	parser.setContentHandler(handler)
	parser.parse(path)
	#pprint.pprint(handler.mapping)
	print str(trackCount) + " tracks processed"
	print "end sax"
		
test()