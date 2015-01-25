#!/usr/bin/env python3


import sys, os, configparser
from rbackup import logger

def checkconfiguration(conffile):

	dlabelvals = {'preexec':'', 'pretimeout':'60', 'postexec':'', 'posttimeout':60}
	dgeneral = {'lockfile':'/run/rbackup-lockfile', 'additional_rsync_args:':'', 'backupsource':None}

	try:
		config = configparser.ConfigParser()
		config.read(conffile)
	except:
		logger.error('error parsing config-file, is some basic syntax wrong?')
		sys.exit(1)  # early-errors_found, need to abort already

	# make config to *real* dict
	parsedconf = dict(config)
	for key in parsedconf:
		if key not in ['DEFAULT', 'labels']:
			parsedconf[key] = dict(parsedconf[key])

	# we need to give a special treatment to the label-section when converting
	# otherwise we risk loosing the order in the configuration which is necessary
	# in fact, when converting to a dict we end up having no order anymore, which
	# is bad for our concept 
	parsedconf['general']['labelorder'] = list(parsedconf['labels'])

	# now, as we have the labelorder, we can finish converting everything
	# to a dict for easier handling
	parsedconf['labels'] = dict(parsedconf['labels'])

	critical = False

	def warn(message):
		logger.warning(message)

	def crit(message):
		logger.error(message)
		return True


	if not set(['general', 'labels']).issubset(parsedconf):
		warn('section "general" and/or "label" missing')

	for section in parsedconf:
		if section == 'general':
			for key in parsedconf['general']:
				if key == 'lockfile':
					default = dgeneral.pop('lockfile')
					entry = parsedconf['general'][key]

					if not os.path.isabs(entry):
						warn('general:lockfile - path not absolute, using ' + default)

					elif not os.path.isdir(os.path.dirname(entry)):
						warn("general:lockfile - directory doesn't exist, using " + default)

				elif key == 'backupsource':
					dgeneral.pop('backupsource')
					srcs = parsedconf['general']['backupsource'].strip().split()
					for src in srcs:
						if not (os.path.isdir(src) or os.path.isfile(src)):
							warn('backupsource:{0} is neither directory nor file'.format(src))

				elif key == 'pendingfile':
					entry = parsedconf['general'][key]
					if not os.path.isdir(os.path.dirname(entry)):
						warn('directory of pendingfile invalid, cannot store jobs')
						config['general']['pendingfile'] = os.devnull


			# now check remainings for necessary values:
			for key in dgeneral:
				if key in ['backupsorce']:
					critical = crit('general:{0} missing'.format(key))

			# now set the remaining missings as defaults
			for key in dgeneral:
				parsedconf['general'][key] = dgeneral[key]

		elif section == 'labels':
			for key in parsedconf['labels']:
				try:
					parsedconf['labels'][key] = int(parsedconf['labels'][key])
				except ValueError:
					critical = crit('labels:{0} is no int'.format(key))

		else:  # all the backup-targets

			secdict = parsedconf[section]  # stortcut to shorten latter code

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
			else:
				secdict['preexec'] = ''

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
			else:
				secdict['postexec'] = ''


	if critical:
		sys.exit(1)

	return parsedconf



def checkargs(args, config=None):

	if not os.path.exists(args.conffile):
		logger.error('invalid configuration-file specified')
		sys.exit(38)

	if args.dupl and args.backup: # too much to do
		logger.error('select either duplication or backup')
		sys.exit(37)

	if not (args.dupl or args.backup): # nothing to do
		logger.info('no mode selected, doing nothing')
		sys.exit()

	# in case we didn't get a config, read it (and check it beforehand)
	if not config: 
		config = checkconfiguration(args.conffile)

	if not args.to:
		logger.error('no destination-device specified')
		sys.exit(37)
	else:
		# check if section is valid
		secs = list(config.keys()).copy()
		secs.remove('general')
		secs.remove('labels')

		if args.to not in secs:
			logger.error('unknown destination-device specified')
			sys.exit(37)

	if args.dupl:
		if not args.fro: # sourcedevice missing
			logger.error('no source-device specified')
			sys.exit(37)
		else:
			# check if section is valid
			if args.fro not in secs:
				logger.error('unknown source-device specified')
				sys.exit(37)

		if args.to == args.fro:
			logger.info('What the heck is your plan, dude!?')
			logger.info("I'm a backup-tool, I'm not joining your crazyness.")
			sys.exit()
	else: # args.backup
		if not args.label: # label to backup to missing
			logger.error('no label to backup to specified')
			sys.exit(37)
		elif args.label in ['labels', 'general']:
			logger.error('invalid label specified')
			sys.exit(37)
		else:
			# check if label is valid
			if args.label not in config['labels']:
				logger.error('unknown label specified')
				sys.exit(37)




if __name__ == '__main__':

	conffile = sys.argv[1]

	if not os.path.exists(conffile):
		logger.error('no such conffile')
		sys.exit(1)

	parsedconf = checkconfiguration(conffile)

	logger.info('check finished')
	logger.info('no errors found')

