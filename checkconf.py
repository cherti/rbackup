#!/usr/bin/env python3


import sys, os, configparser

def checkconfiguration(conffile):

	try:
		config = configparser.ConfigParser()
		config.read(conffile)
	except:
		print('error parsing conffile, is some basic syntax wrong?', file=sys.stderr)
		return True # early-errors_found

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


	def check_opt_validity(sec):
		global errors_found

		#pre
		try: pre = config.get(section, 'pre')
		except configparser.NoOptionError: pre = ''

		if pre != '' and not os.path.exists(pre):
			errors_found = True
			print('invalid path in {0}:pre'.format(section), file=sys.stderr)

		#post
		try: post = config.get(section, 'post')
		except configparser.NoOptionError: post = ''

		if post != '' and not os.path.exists(post):
			errors_found = True
			print('invalid path in {0}:pre'.format(section), file=sys.stderr)

		#backupdir
		#parse
		try: backupdir = config.get(section, 'backupdir')
		except configparser.NoOptionError:
			print('no backupdir specified', file=sys.stderr)
			errors_found = False



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
				print('labels: {0} is not int'.format(opt), file=sys.stderr)
				errors_found = True


	# cycle over backuptargets
	for key in config.sections():
		if key in ['main', 'general', 'labels']: # no backuptargets
			continue
		else:
			if not len(config.get(key, 'backupdir')) > 0: # if we have no backupdir...
				print("Problem with {0}-backupdir".format(key), file=sys.stderr)
				errors_found = True

	if errors_found:
		print('syntax-check of config-file finished with errors', file=sys.stderr)

	return errors_found




if __name__ == '__main__':

	conffile = sys.argv[1]

	if not os.path.exists(conffile):
		print('no such conffile', file=sys.stderr)
		sys.exit(1)

	errors_found = checkconfiguration(conffile)

	if not errors_found:
		print('check finished')
		print('no errors found')

