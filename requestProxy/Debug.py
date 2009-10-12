#	vim: set tabstop=4 columns=120 shiftwidth=4:
import sys, string

global DEBUG
DEBUG = 1

def out(*args):
	if DEBUG:
		sys.stderr.write(string.join(map(lambda x: str(x), args), ' ') + '\n')