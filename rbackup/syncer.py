#!/usr/bin/env python3

#confdir = '/etc/newrbackup'
conffile = 'sample.conf'

import os, sys, shutil, configparser, datetime


def simple_sync(src, dst, config, add_args=None):
	"""
	simply sync two directories using the additional rsync-arguments provided
	"""

	rsync_cmd = ["rsync", "-a", "--delete", config.get('general', 'additional_rsync_args')]

	if add_args:
		rsync_cmd += add_args

	src = os.path.abspath(src) + '/'
	dst = os.path.abspath(dst)

	rsync_cmd += [src, dst]
	rsync_cmdstr = " ".join(rsync_cmd)

	#print(rsync_cmdstr)

	# sync to target
	return os.system(rsync_cmdstr)


def reorder_backupdirs(label, maxcount, directory=None):
	"""
	shifting all directories of the given label back by one
	to make space for the new backup as label.0
	includes a mechanism to delete the last one if too many directorys
	are present
	also includes a mechanism to collect backups that seem to violate
	the system to order the backups. Shouldn't have to be used, but
	one never knows
	"""
	
	olddir = None # used in case of chdir

	if directory: # then switch to directory to ease latter code
		# and save currentdir, of course, to switch back later
		olddir = os.path.abspath(os.path.curdir)
		os.chdir(directory)


	# get the directories in question to be reordered
	dirs = sorted([ d for d in os.listdir() if d.startswith(label) ])

	# handle "overgrowth"
	if len(dirs) >= maxcount: # we need to delete the last one
		shutil.rmtree(dirs[-1]) # actually remove the folder
		dirs.remove(dirs[-1]) # remove the folder from dirlist

	# now move everything back by one
	for i in range(len(dirs)-1, -1, -1):
		src = '{0}.{1}'.format(label, i)
		dst = '{0}.{1}'.format(label, i+1)
		if os.path.exists(src): # if no dir, we do not need to move

			if os.path.exists(dst):
				# if we still have dst left, something is probably
				# out of system. Remove those from the standard-tree
				# save them into a separate folder with date appended
				# and give notice for the user to check
				os.mkdir('out-of-system')
				now = datetime.datetime.today()
				shutil.move(dst, 'out-of-system/{0}-{1}'.format(dst, now))
				print('WARNING: Some folders might be out of system on device, should be checked', file=sys.stderr)

			shutil.move(src, dst)

	if olddir: # if we changed directory, change back now
		os.chdir(olddir)



def backup_sync(source, backuppath, label, config):
	"""
	create a new backup snapshot from data into the backupdir
	on lowest stage (higher stages are done by backup_copy()
	"""

	os.chdir(backuppath)

	# filter for dirs with this label
	dirs = sorted([d for d in os.listdir() if d.startswith(label)])

	if len(dirs) == 0: # we have no backups yet, therefore start from scratch
		os.makedirs("in_progress_{0}".format(label), exist_ok=True)
	else: # backups present, take one and update it (faster & saves space)
		os.system("cp -al {0} in_progress_{1}".format(dirs[0], label))


	# prepare excludes and includes as arguments for latter rsync-use
	add_rsync_args = [] # to store the additional args like in- and excludes

	# in- and excludelist are only used if they are specified
	if 'includelist' in config.options('general'):
		incl_lst = config.get('general', 'includelist')

		if os.path.exists(incl_lst): # use only if path is valid
			add_rsync_args += ['--include-from=' + config.get('general', 'includelist')]

	if 'excludelist' in config.options('general'):
		excl_lst = config.get('general', 'excludelist')

		if os.path.exists(excl_lst): # use only if path is valid
			add_rsync_args += ['--exclude-from=' + config.get('general', 'excludelist')]


	# now SYNC!!!
	ret_rsync = simple_sync( source, "in_progress_{0}".format(label), config, add_args=add_rsync_args)


	if ret_rsync == 0: # only continue if rsync finished successfully

		#reorder backups
		backupcount = int(config.get('labels', label))

		# if the one we want to use is free, we do not need to reorder
		if os.path.exists(label + '.0'): 
			# if label.0 is already in use, then we have to
			reorder_backupdirs(label, backupcount)

		#finally move the synced one to the start
		src = 'in_progress_{0}'.format(label)
		dst = '{0}.0'.format(label)
		shutil.move(src, dst)

	return ret_rsync


def backup_copy(backuppath, srclabel, dstlabel):
	"""
	create a snapshot based on other latest snapshots for
	higher stages 
	"""

	os.chdir(backuppath)

	# filter for dirs with this label for src and dst
	srcdirs = sorted([ d for d in os.listdir() if d.startswith(srclabel) ])
	dstdirs = sorted([ d for d in os.listdir() if d.startswith(dstlabel) ])

	if len(srcdirs) == 0: # if we have no sourcen, we cannot do anything
		print('previous stage not existent, aborting', file=sys.stderr)
		sys.exit(1)

	# get max number of dirs to store
	dstmax = int(config.get('labels', dstlabel))

	# reordering only necessary if label.0 is already in use
	if os.path.exists('{0}.0'.format(dstlabel)):
		reorder_backupdirs(dstlabel, dstmax) # free label.0

	# create the new backup for this stage
	cp_ret = os.system("cp -alT {0} {1}.0".format(srcdirs[-1], dstlabel))

	return cp_ret
