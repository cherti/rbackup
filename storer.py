#!/usr/bin/env python3

import os

def jobstring(args):
	options = []
	if args.backup:
		options += ['backup']
	else:
		options += ['duplication']

	options += ['to={0}'.format(args.to)]

	if args.fro:
		options += ['fro={0}'.format(args.fro)]

	if args.label:
		options += ['label={0}'.format(args.label)]

	if args.quiet:
		options += ['quiet']

	return ' '.join(options)


def store(args, storefile):

	jobstr = jobstring(args)

	# check whether filesystem-structure of storefile exists
	# create if not
	if not os.path.exists(storefile):
		directory = os.path.dirname(storefile)
		os.makedirs(directory, exist_ok=True)

	# store this run
	with open(storefile, 'a') as f:
		print(jobstring, file=f)


def run_stored(storefile, skip_job=None):

	if os.path.exists(storefile):

		with open(storefile, 'r') as f:
			# read jobstrings into list;
			# list(set(somelist)) is an easy way of removing
			# duplicates from a list
			runs = list(set(f.read().strip().split('\n')))

			if skip_job and skip_job in runs:
				# we don't need to run the exact same job
				# twice at the same time, would be pointless
				runs.remove(skip_job)

		# remove storefile, if jobs of it fail they will be rewritten
		# automatically to a new storefile
		os.remove(storefile)

		backups = [ run for run in runs if run.startswith('backup') ]
		duplis  = [ run for run in runs if run.startswith('duplication') ]

		# try to do stored backups first, so that duplications are as
		# up-to-date as possible if successfull

		def finish_cmdlinestring(cmdstring, options):
			"""
			go over all possible options and attach them to
			cmdstring if they are present within options
			"""
			if 'quiet' in options:
				args += ['--quiet']

			opt_to = [ to for to in options if to.startswith('to') ]
			if opt_to:
				_, to = opt_to.split('=')
				cmdstring += ['--to', to]

			opt_from = [ fro for fro in options if fro.startswith('fro') ]
			if opt_fro:
				_, fro = opt_fro.split('=')
				cmdstring += ['--from', fro]

			opt_label = [ l for l in options if l.startswith('label') ]
			if opt_label:
				_, label = opt_label.split('=')
				cmdstring += ['--label', label]

			return cmdstring


		for backupset in backups:
			# evaluate optionstring and build cmdlinestring
			options = backupset.split(' ')
			cmdstr = ['rbackup', '--backup', '--store']
			cmdstr = finish_cmdlinestring(cmdstr, options)

			# finally we have a cmdlinestring, now GO FOR IT:
			os.system(' '.join(cmdstr))


		for duplset in duplis:
			# evaluate optionstring and build cmdlinestring
			options = duplset.split(' ')
			cmdstr = ['rbackup', '--duplication', '--store']
			cmdstr = finish_cmdlinestring(cmdstr, options)

			# finally we have a cmdlinestring, now GO FOR IT:
			os.system(' '.join(cmdstr))
