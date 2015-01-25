#!/usr/bin/env python3

#confdir = '/etc/newrbackup'
conffile = 'sample.conf'

import os, sys, shutil, configparser, datetime, subprocess
from rbackup import logger


def simple_sync(src, dst, add_args=None):
	"""
	simply sync two directories using the additional rsync-arguments provided
	"""

	rsync_cmd = ["rsync", "-a", "--delete"]
	rsync_cmd += conf['general']['additional_rsync_args'].split()

	if add_args:
		rsync_cmd += add_args

	if src[-1] == '/': # make abspath while preserving trailing '/'
		src = os.path.abspath(src) + '/'
	else:
		src = os.path.abspath(src)
	dst = os.path.abspath(dst)

	rsync_cmd += [src, dst]


	# sync to target
	logger.info('starting with rsync')
	logger.debug(" ".join(rsync_cmd))

	rsync_ret = subprocess.call(rsync_cmd)

	logger.info('finished with rsync')

	return rsync_ret


def reorder_backupdirs(label, maxcount, dir):
	"""
	shifting all directories of the given label back by one
	to make space for the new backup as label.0
	includes a mechanism to delete the last one if too many directorys
	are present
	also includes a mechanism to collect backups that seem to violate
	the system to order the backups. Shouldn't have to be used, but
	one never knows
	"""

	"""
	olddir = None # used in case of chdir

	if directory: # then switch to directory to ease latter code
		# and save currentdir, of course, to switch back later
		olddir = os.path.abspath(os.path.curdir)
		os.chdir(directory)
	"""

	# get the directories in question to be reordered
	dirs = sorted([ os.path.join(dir, d) for d in os.listdir(dir) if d.startswith(label) ])

	# handle "overgrowth"
	if len(dirs) >= maxcount: # we need to delete the last one
		logger.info('start dropping last backuppoint')
		shutil.rmtree(dirs[-1]) # actually remove the folder
		dirs.remove(dirs[-1]) # remove the folder from dirlist
		logger.info('done dropping last backuppoint')

	# now move everything back by one
	logger.info('start shifting backups')
	for i in range(len(dirs)-1, -1, -1):
		src = os.path.join(dir, '{0}.{1}'.format(label, i))
		dst = os.path.join(dir, '{0}.{1}'.format(label, i+1))
		if os.path.exists(src): # if no dir, we do not need to move

			if os.path.exists(dst):
				# if we still have dst left, something is probably
				# out of system. Remove those from the standard-tree
				# save them into a separate folder with date appended
				# and give notice for the user to check
				oosdir = os.path.join(dir, 'out-of-system')
				os.mkdir(oosdir)
				now = datetime.datetime.today()
				shutil.move(dst, os.path.join(oosdir, '{0}-{1}'.format(dst, now)))
				logger.warning('WARNING: Some folders might be out of system on device, should be checked')

			logger.moreinfo('start moving ' + src)
			shutil.move(src, dst)
			logger.moreinfo('finished moving '  + src)

	logger.info('done shifting backups')

	"""
	if olddir: # if we changed directory, change back now
		os.chdir(olddir)
	"""



def backup_sync(source, backuppath, label):
	"""
	create a new backup snapshot from data into the backupdir
	on lowest stage (higher stages are done by backup_copy()
	"""

	"""
	os.chdir(backuppath)
	"""

	bup = backuppath
	add_rsync_args = [] # to store the additional args like in- and excludes

	# filter for dirs with this label
	dirs = sorted([ os.path.join(bup, d) for d in os.listdir(bup) if d.startswith(label) ])

	#print(bup)
	#print(dirs)

	# create basedir to which we want to backup now,
	# either by hardlink-copying an old one or by creating it
	fulltempdstdir = os.path.join(bup, "in_progress_{0}".format(label))
	if os.path.exists(fulltempdstdir):
		logger.info('dropping stale tempdir')
		shutil.rmtree(fulltempdstdir)
		logger.info('done dropping stale tempdir')

	if len(dirs) != 0: 
		add_rsync_args.append( '--link-dest={0}'.format(os.path.abspath(dirs[0])) )

	if len(dirs) != 0: 
		add_rsync_args.append( '--link-dest={0}'.format(os.path.abspath(dirs[0])) )

	os.makedirs(fulltempdstdir, exist_ok=True)


	# prepare excludes and includes as arguments for latter rsync-use

	# in- and excludelist are only used if they are specified
	if 'includelist' in conf['general']:
		incl_lst = conf['general']['includelist']

		if os.path.exists(incl_lst): # use only if path is valid
			add_rsync_args += ['--include-from=' + conf['general']['includelist']]

	if 'excludelist' in conf['general']:
		excl_lst = conf['general']['excludelist']

		if os.path.exists(excl_lst): # use only if path is valid
			add_rsync_args += ['--exclude-from=' + conf['general']['excludelist']]


	# now SYNC!!!
	ret_rsync = simple_sync( source, fulltempdstdir, add_args=add_rsync_args)

	if ret_rsync == 0: # only continue if rsync finished successfully


		waitingpath = os.path.join(bup, "ready_to_move_{0}".format(label))
		logger.moreinfo('moving "in_progress_{0}" to "ready_to_move_{0}"'.format(label))
		shutil.move(fulltempdstdir, waitingpath)
		logger.debug('done moving "in_progress_{0}" to "ready_to_move_{0}"'.format(label))

		#reorder backups
		backupcount = conf['labels'][label]

		# if the one we want to use is free, we do not need to reorder
		if os.path.exists(os.path.join(bup, label + '.0')):
			# if label.0 is already in use, then we have to
			reorder_backupdirs(label, backupcount, bup)

		#finally move the synced one to the start
		src = waitingpath
		dst = os.path.join(bup, '{0}.0'.format(label))
		logger.moreinfo('moving "ready_to_move_{0}" to "{0}.0"'.format(label))
		shutil.move(src, dst)
		logger.debug('done moving "ready_to_move_{0}" to "{0}.0"'.format(label))

	return ret_rsync


def backup_copy(backuppath, srclabel, dstlabel):
	"""
	create a snapshot based on other latest snapshots for
	higher stages
	"""

	bup = backuppath
	"""
	os.chdir(backuppath)
	"""

	# filter for dirs with this label for src and dst
	srcdirs = sorted([ os.path.join(bup, d) for d in os.listdir(bup) if d.startswith(srclabel) ])
	dstdirs = sorted([ os.path.join(bup, d) for d in os.listdir(bup) if d.startswith(dstlabel) ])

	if len(srcdirs) == 0: # if we have no sources, we cannot do anything
		logger.error('previous stage not existent, aborting')
		sys.exit(1)

	# get max number of dirs to store
	dstmax = conf['labels'][dstlabel]

	# reordering only necessary if label.0 is already in use
	targetpath = os.path.join(bup, '{0}.0'.format(dstlabel))
	if os.path.exists(targetpath):
		reorder_backupdirs(dstlabel, dstmax, bup) # free label.0

	# create the new backup for this stage
	#srcpath = scrdirs[-1]
	logger.info('start with cp')
	logger.debug("cp -alT {0} {1}".format(srcdirs[-1], targetpath))
	cp_ret = subprocess.call(['cp', '-alT', srcdirs[-1], targetpath])
	logger.info('done with cp')

	return cp_ret
