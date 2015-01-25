import sys

#verbosity = conf['verbosity']

level = {'debug': 3, 'moreinfo': 2, 'info': 1}

def error(msg):
	print(':(!): {0}'.format(msg), file=sys.stderr)


def warning(msg):
	print(':(?): {0}'.format(msg), file=sys.stderr)


def debug(msg):
	if verbosity >= level['debug']:
		print(':: {0}'.format(msg), file=sys.stdout)


def moreinfo(msg):
	if verbosity >= level['moreinfo']:
		print(':: {0}'.format(msg), file=sys.stdout)


def info(msg):
	if verbosity >= level['info']:
		print(':: {0}'.format(msg), file=sys.stdout)
