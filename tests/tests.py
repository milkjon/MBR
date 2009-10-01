# Will read and parse iTunes Library

# FIXME! Dirty implementation just a proof of concept

import time
import plistlib
import xml.parsers.expat
import os

path = '/Users/Shared/iTunes/iTunes Music Library.xml'
state = 0


def test(f):
	t1 = time.time()
	f()
	t2 = time.time()
	f()
	t3 = time.time()
	print t2-t1
	print t3-t2

def plist():
	print "begin"
	# Reads the whole plist and iterates thru it. Takes 9 seconds :(
	# Will need to use a real xml library.
	p = plistlib.readPlist(path)
	keys = p['Tracks'].keys()
	print "end"

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

def start_element(name, attrs):
    global state, track
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
            print 'dict'
            state = 5
    elif state == 5:
        if name == 'dict':
            track = []
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
            state = os.exit()
    elif state == 6:
        if name == 'dict':
            print track
            state = 5
    elif state == 7:
        if name == 'key':
            state = 6
    
def char_data(data):
    global state, track
    if state == 3:
        if data == u'Tracks':
            print 'Character data:', repr(data)
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
	print "begin"
	p = xml.parsers.expat.ParserCreate()
	p.StartElementHandler = start_element
	p.EndElementHandler = end_element
	p.CharacterDataHandler = char_data
	p.ParseFile(file(path))
	print "end"

#test(expat)
expat()