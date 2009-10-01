# Will read and parse iTunes Library

# FIXME! Dirty implementation just a proof of concept

import plistlib

path = '/Users/Shared/iTunes/iTunes Music Library.xml'

# Reads the whole plist and iterates thru it. Takes 9 seconds :(
# Will need to use a real xml library.
p = plistlib.readPlist(path)
keys = p['Tracks'].keys()
for k in keys:
  t =  p['Tracks'][k]
  try:
    print t['Track ID'], t['Genre'], t['Artist'], '-', t['Album'], '-',  t['Name']
  except:
    pass

