#!/usr/bin/env python3

import os, subprocess

def jobstring(args):
	"""
	create unique jobstring for the job triggered by the given arguments
	"""

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
	"""
	store unique job-identifier in a file to do it later
	"""

	jobstr = jobstring(args)

	# check whether filesystem-structure of storefile exists
	# create if not
	if not os.path.exists(storefile):
		directory = os.path.dirname(storefile)
		os.makedirs(directory, exist_ok=True)

	# store this run
	with open(storefile, 'a') as f:
		print(jobstr, file=f)

	if args.verbosity > 0:
		print('jobstring {0} stored to be done later'.format(jobstr))


def run_stored(storefile, skip_job=None, verbosity=0):
	"""
	try to run all stored jobs in subshell
	"""

	if os.path.exists(storefile):

		with open(storefile, 'r') as f:
			# read jobstrings into list;
			# list(set(somelist)) is an easy way of removing
			# duplicates from a list
			runs = list(set(f.read().strip().split('\n')))

			if verbosity > 0:
				for run in runs:
					print(run)

			if skip_job and skip_job in runs:
				# we don't need to run the exact same job
				# twice at the same time, would be pointless
				runs.remove(skip_job)

		# remove storefile, if jobs of it fail again they will be
		# rewritten automatically to a new storefile
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

			# extract an option, take the first one as rbackup doesn't store it twice
			opt_to = [ to for to in options if to.startswith('to') ]
			if len(opt_to) > 0:
				_, to = opt_to[0].split('=')
				cmdstring += ['--to', to]

			# extract an option, take the first one as rbackup doesn't store it twice
			opt_fro = [ fro for fro in options if fro.startswith('fro') ]
			if len(opt_fro) > 0:
				_, fro = opt_fro[0].split('=')
				cmdstring += ['--from', fro]

			# extract an option, take the first one as rbackup doesn't store it twice
			opt_label = [ l for l in options if l.startswith('label') ]
			if len(opt_label) > 0:
				_, label = opt_label[0].split('=')
				cmdstring += ['--label', label]

			return cmdstring


		for backupset in backups:
			# evaluate optionstring and build cmdlinestring
			options = backupset.split(' ')
			# --no-pending is especially importaint, otherwise we have an infinite loop
			cmdstr = ['rbackup.py', '--backup', '--store', '--no-pending']
			cmdstr = finish_cmdlinestring(cmdstr, options)

			# finally we have a cmdlinestring, now GO FOR IT:
			#os.system(' '.join(cmdstr))
			subprocess.call(cmdstr)


		for duplset in duplis:
			# evaluate optionstring and build cmdlinestring
			options = duplset.split(' ')
			cmdstr = ['rbackup.py', '--duplication', '--store']
			cmdstr = finish_cmdlinestring(cmdstr, options)

			# finally we have a cmdlinestring, now GO FOR IT:
			#os.system(' '.join(cmdstr))
			subprocess.call(cmdstr)
