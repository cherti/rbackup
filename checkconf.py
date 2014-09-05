#!/usr/bin/env python3


import sys, os, configparser

def checkconfiguration(conffile):

	try:
		config = configparser.ConfigParser()
		config.read(conffile)
	except:
		print('error parsing conffile, is some basic syntax wrong?', file=sys.stderr)
		return True # early-errors_found, need to abort already

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


	def check_absolute_path(path):
		global errors_found # Fixme: seems not to work

		if not os.path.isabs(path):
			print('path {0} is not absolute, only absolute paths are allowed'.format(path), file=sys.stderr)
			errors_found = True
			return False
		else:
			return True


	def check_opt_validity(sec):
		global errors_found

		#pre
		try: pre = config.get(section, 'pre')
		except configparser.NoOptionError: pre = ''

		if pre != '':
			if os.path.exists(pre):
				check_absolute_path(pre)
			else:
				errors_found = True
				print('invalid path in {0}:pre'.format(section), file=sys.stderr)

		#post
		try: post = config.get(section, 'post')
		except configparser.NoOptionError: post = ''

		if post != '':
			if os.path.exists(post):
				check_absolute_path(post)
			else:
				errors_found = True
				print('invalid path in {0}:pre'.format(section), file=sys.stderr)

		#backupdir
		#parse
		try:
			backupdir = config.get(section, 'backupdir')
			check_absolute_path(backupdir)
		except configparser.NoOptionError:
			print('no backupdir specified', file=sys.stderr)
			errors_found = False



	#check for mandatory labels
	general	= test_for_section('general')
	labels	= test_for_section('labels')
	main	= test_for_section('main')

	if general:
		test_for_option('general', 'additional_rsync_args')
		test_for_option('general', 'backupsource')
		test_for_option('general', 'pendingfile')

		# everything except for additional_rsync_args should be (absolute) paths
		for opt in config.options('general'):
			if opt != 'additional_rsync_args':
				check_absolute_path(config.get('general', opt))



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
		sys.exit(35)



def checkargs(args, config=None):

	if not os.path.exists(args.conffile):
		print('invalid configuration specified', file=sys.stderr)
		sys.exit(38)

	if args.dupl == args.backup: # too much to do
		print('select either duplication or backup', file=sys.stderr)
		sys.exit(37)

	if not (args.dupl or args.backup): # nothing to do
		print('no mode selected, doing nothing')
		sys.exit()
	
	# in case we didn't get a config, read it (and check it beforehand)
	if not config: 
		checkconfiguration(args.conffile)
		config = configparser.ConfigParser()
		config.read(args.conffile)

	if not args.to:
		print('no destination-device specified', file=sys.stderr)
		sys.exit(37)
	else:
		# check if section is valid
		secs = config.sections()
		secs.remove('general')
		secs.remove('labels')

		if args.to not in secs:
			print('unknown destination-device specified', file=sys.stderr)
			sys.exit(37)

	if args.dupl:
		if not args.fro: # sourcedevice missing
			print('no source-device specified', file=sys.stderr)
			sys.exit(37)
		else:
			# check if section is valid
			if args.fro not in secs:
				print('unknown source-device specified', file=sys.stderr)
				sys.exit(37)

		if args.to == args.fro:
			print('What the heck is your plan, dude!?')
			print("I'm a backup-tool, I'm not joining your crazyness.")
	else: # args.backup
		if not args.label: # label to backup to missing
			print('no label to backup to specified', file=sys.stderr)
			sys.exit(37)
		elif args.label in ['labels', 'general']:
			print('invalid label specified', file=sys.stderr)
			sys.exit(37)
		else:
			# check if label is valid
			if args.label not in config.options('labels'):
				print('unknown label specified', file=sys.stderr)
				sys.exit(37)
				



if __name__ == '__main__':

	conffile = sys.argv[1]

	if not os.path.exists(conffile):
		print('no such conffile', file=sys.stderr)
		sys.exit(1)

	errors_found = checkconfiguration(conffile)

	if not errors_found:
		print('check finished')
		print('no errors found')

