#!/usr/bin/env python3

conffile = 'sample.conf'

import syncer, configparser, sys, os, checkconf

section = sys.argv[1]

#
# preparations
#

conferrors = checkconf.checkconfiguration(conffile)

if conferrors:
	sys.exit(5)
	# error announcement already made within checkconf

config = configparser.ConfigParser()
config.read(conffile)

# parse configuration
#pre
try: pre = config.get(section, 'pre')
except configparser.NoOptionError: pre = ''

if not os.path.exists(pre): #fallback to nothing in case pre is invalid
	pre = ''


#post
try: post = config.get(section, 'post')
except configparser.NoOptionError: post = ''

if not os.path.exists(post): #fallback to nothing in case post is invalid
	post = ''


#backupdir
#parse
try: backupdir = config.get(section, 'backupdir')
except configparser.NoOptionError:
	print('no backupdir specified', file=sys.stderr)
	sys.exit(3)

#check validity
if not os.path.exists(backupdir):
	print('invalid backupdir specified', file=sys.stderr)
	sys.exit(4)


#
# everything fine, time to do some magic!
#


