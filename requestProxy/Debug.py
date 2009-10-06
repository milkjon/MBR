#	vim: set tabstop=4 columns=120 shiftwidth=4:
import sys

global DEBUG
DEBUG = 1

def out(*args):
	if DEBUG:
		foo = " "
		sys.stderr.write(foo.join(map(lambda x: str(x), args)) + '\n')
