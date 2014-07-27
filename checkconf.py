#!/usr/bin/env python3


import sys, os, configparser

conffile = sys.argv[1]

if not os.path.exists(conffile):
	print('no such conffile')
	sys.exit(1)

config = configparser.ConfigParser()
config.read(conffile)

errors_found = False

def test_for_section(sec):
	global errors_found
	if sec in config.sections():
		return True
	else:
		print('section "{0}" missing'.format(sec))
		errors_found = True
		return False


def test_for_option(sec, opt):
	global errors_found
	if opt in config.options(sec):
		return True
	else:
		print('option "{0}" missing in section {1}'.format(opt, sec))
		errors_found = True
		return False


#check for mandatory labels
general	= test_for_section('general')
labels	= test_for_section('labels')
main	= test_for_section('main')

if general:
	test_for_option('general', 'backupsource')
	test_for_option('general', 'additional_rsync_args')


# check non-string-data types
if labels:
	for opt in config.options('labels'):
		try:
			int(config.get('labels', opt))
		except ValueError:
			print('labels: {0} is not int'.format(opt))
			errors_found = True


# cycle over backuptargets
for key in config.sections():
	if key in ['main', 'general', 'labels']: # no backuptargets
		continue
	else:
		if not len(config.get(key, 'backupdir')) > 0: # if we have no backupdir...
			print("Problem with {0}-backupdir".format(key))
			errors_found = True

print('check finished')
if not errors_found:
	print('no errors found')
