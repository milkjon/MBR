import sys

global DEBUG
DEBUG = 1

def out(*args):
	if DEBUG:
		foo = " "
		sys.stderr.write(foo.join(args) + '\n')