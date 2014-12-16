#!/usr/bin/env python3


import sys, os, configparser

def checkconfiguration(conffile):

	dlabelvals = {'preexec':'', 'pretimeout':'60', 'postexec':'', 'posttimeout':60}
	dgeneral = {'lockfile':'/run/rbackup-lockfile', 'additional_rsync_args:':'', 'backupsource':None}

	try:
		config = configparser.ConfigParser()
		config.read(conffile)
	except:
		print('error parsing config-file, is some basic syntax wrong?', file=sys.stderr)
		sys.exit(1)  # early-errors_found, need to abort already

	# make config to *real* dict
	conf = dict(config)
	for key in conf:
		if key not in ['DEFAULT', 'labels']:
			conf[key] = dict(conf[key])

	# we need to give a special treatment to the label-section when converting
	# otherwise we risk loosing the order in the configuration which is necessary
	# in fact, when converting to a dict we end up having no order anymore, which
	# is bad for our concept 
	conf['general']['labelorder'] = list(conf['labels'])

	# now, as we have the labelorder, we can finish converting everything
	# to a dict for easier handling
	conf['labels'] = dict(conf['labels'])

	critical = False

	def warn(message):
		print('::(?) ' + message, file=sys.stderr)

	def crit(message):
		print('::(!) ' + message, file=sys.stderr)
		return True


	if not set(['general', 'labels']).issubset(conf):
		warn('section "general" and/or "label" missing')

	for section in conf:
		if section == 'general':
			for key in conf['general']:
				if key == 'lockfile':
					default = dgeneral.pop('lockfile')
					entry = conf['general'][key]

					if not os.path.isabs(entry):
						warn('general:lockfile - path not absolute, using ' + default)

					elif not os.path.isdir(os.path.dirname(entry)):
						warn("general:lockfile - directory doesn't exist, using " + default)

				elif key == 'backupsource':
					dgeneral.pop('backupsource')
					srcs = conf['general']['backupsource'].strip().split()
					for src in srcs:
						if not (os.path.isdir(src) or os.path.isfile(src)):
							warn('backupsource:{0} is neither directory nor file'.format(src))

				elif key == 'pendingfile':
					entry = conf['general'][key]
					if not os.path.isdir(os.path.dirname(entry)):
						warn('directory of pendingfile invalid, cannot store jobs')
						config['general']['pendingfile'] = os.devnull


			# now check remainings for necessary values:
			for key in dgeneral:
				if key in ['backupsorce']:
					critical = crit('general:{0} missing'.format(key))

			# now set the remaining missings as defaults
			for key in dgeneral:
				conf['general'][key] = dgeneral[key]

		elif section == 'labels':
			for key in conf['labels']:
				try:
					conf['labels'][key] = int(conf['labels'][key])
				except ValueError:
					critical = crit('labels:{0} is no int'.format(key))

		else:  # all the backup-targets

			secdict = conf[section]  # stortcut to shorten latter code

			if 'preexec' in secdict and secdict['preexec'] != '':
				prescript = secdict['preexec'].split()[0]  # cut off the command-line-args
				if not os.path.isfile(prescript):
					critical = crit('{0}:preexec is no file'.format(section))
				if not os.path.isabs(prescript):
					critical = crit('path of {0}:preexec is not absolute'.format(section))

				if 'pretimeout' in secdict:
					try:
						secdict['pretimeout'] = int(secdict['pretimeout'])
					except ValueError:
						warn('{0}:pretimeout is no int, using {1}'.format(section, dlabelvals['pretimeout']))
						secdict['pretimeout'] = dlabelvals['pretimeout']

			if 'postexec' in secdict and secdict['postexec'] != '':
				postscript = secdict['postexec'].split()[0]  # cut off the command-line-args
				if not os.path.isfile(postscript):
					critical = crit('{0}:postexec is no file'.format(section))
				if not os.path.isabs(postscript):
					critical = crit('path of {0}:postexec is not absolute'.format(section))

				if 'posttimeout' in secdict:
					try:
						secdict['posttimeout'] = int(secdict['posttimeout'])
					except ValueError:
						warn('{0}:posttimeout is no int, using {1}'.format(section, dlabelvals['posttimeout']))
						secdict['posttimeout'] = dlabelvals['posttimeout']


	if critical:
		sys.exit(1)

	return conf



def checkargs(args, config=None):

	if not os.path.exists(args.conffile):
		print('invalid configuration-file specified', file=sys.stderr)
		sys.exit(38)

	if args.dupl and args.backup: # too much to do
		print('select either duplication or backup', file=sys.stderr)
		sys.exit(37)

	if not (args.dupl or args.backup): # nothing to do
		print('no mode selected, doing nothing')
		sys.exit()

	# in case we didn't get a config, read it (and check it beforehand)
	if not config: 
		config = checkconfiguration(args.conffile)

	if not args.to:
		print('no destination-device specified', file=sys.stderr)
		sys.exit(37)
	else:
		# check if section is valid
		secs = list(config.keys()).copy()
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
			if args.label not in config['labels']:
				print('unknown label specified', file=sys.stderr)
				sys.exit(37)




if __name__ == '__main__':

	conffile = sys.argv[1]

	if not os.path.exists(conffile):
		print('no such conffile', file=sys.stderr)
		sys.exit(1)

	conf = checkconfiguration(conffile)

	print('check finished')
	print('no errors found')

