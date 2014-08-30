#!/usr/bin/env python3

#confdir = '/etc/newrbackup'
conffile = 'sample.conf'

import os, sys, shutil, configparser, datetime

config = configparser.ConfigParser()
config.read(conffile)

def simple_sync(src, dst, add_args=None):
	"""
	sync two directories
	"""

	rsync_cmd = ["rsync", "-a", "--delete", config.get('general', 'additional_rsync_args')]

	if add_args:
		rsync_cmd += add_args

	src = os.path.abspath(src) + '/'
	dst = os.path.abspath(dst)

	rsync_cmd += [src, dst]
	print(rsync_cmd)
	rsync_cmdstr = " ".join(rsync_cmd)

	#print(rsync_cmdstr)

	# sync to target
	return os.system(rsync_cmdstr)


def reorder_backupdirs(label, maxcount, directory=None):
	"""
	shifting all directories of the given label back by one
	to make space for the new backup as label.0
	includes mechanism to delete the last one if too many directorys
	are present
	"""
	
	olddir = None

	if directory: # then switch to directory to ease latter code
		# and save currentdir, of course
		olddir = os.path.abspath(os.path.curdir)
		os.chdir(directory)


	dirs = sorted([ d for d in os.listdir() if d.startswith(label) ])

	if len(dirs) >= maxcount: # we need to delete the last one
		shutil.rmtree(dirs[-1])
		dirs.remove(dirs[-1])

	# now move everything by one
	for i in range(len(dirs)-1, -1, -1):
		src = '{0}.{1}'.format(label, i)
		dst = '{0}.{1}'.format(label, i+1)
		if os.path.exists(src): # if no dir, we do not need to move

			if os.path.exists(dst):
				# if we still have dst left, something is probably
				# out of system. Remove those from the standard-tree
				# and give notice for the user to check
				os.mkdir('out-of-system')
				now = datetime.datetime.today()
				shutil.move(dst, 'out-of-system/{0}-{1}'.format(dst, now))
				print('WARNING: Some folders might be out of system on device, should be checked', file=sys.stderr)

			shutil.move(src, dst)

	if olddir: # if we changed, change back now
		os.chdir(olddir)



def backup_sync(source, backuppath, label):
	"""
	create a new backup snapshot from data into the backupdir
	"""

	os.chdir(backuppath)

	# filter for dirs with this label
	dirs = [ d for d in os.listdir() if d.startswith(label) ]

	if len(dirs) == 0: # no backups yet, start from scratch
		os.mkdir("in_progress_{0}".format(label))
	else: # backups present, go updating
		os.system("cp -al {0}.0 in_progress_{0}".format(label))


	# prepare excludes and includes as arguments for latter rsync-use
	add_rsync_args = []

	if 'includelist' in config.options('general'):
		incl_lst = config.get('general', 'includelist')

		if os.path.exists(incl_lst):
			add_rsync_args += ['--include-from=' + config.get('general', 'includelist')]

	if 'excludelist' in config.options('general'):
		excl_lst = config.get('general', 'excludelist')

		if os.path.exists(excl_lst):
			add_rsync_args += ['--exclude-from=' + config.get('general', 'excludelist')]


	# now SYNC!!!
	ret_rsync = simple_sync( source, "in_progress_{0}".format(label), add_args=add_rsync_args)


	if ret_rsync == 0: # only continue if rsync finished successfully

		#reorder backups
		backupcount = int(config.get('labels', label))

		if os.path.exists(label + '.0'):
			reorder_backupdirs(label, backupcount)

		#finally move the synced one to the start
		src = 'in_progress_{0}'.format(label)
		dst = '{0}.0'.format(label)
		shutil.move(src, dst)

	return ret_rsync


def backup_copy(backuppath, srclabel, dstlabel):
	"""
	create a snapshot based on other latest snapshots
	"""

	os.chdir(backuppath)

	# filter for dirs with this label for src and dst
	srcdirs = [ d for d in os.listdir() if d.startswith(srclabel) ]
	dstdirs = [ d for d in os.listdir() if d.startswith(dstlabel) ]

	if len(srcdirs) == 0:
		print('previous stage not existent, aborting', file=sys.stderr)
		sys.exit(1)

	# get max number of dirs to store
	dstmax = int(config.get('labels', dstlabel))

	reorder_backupdirs(dstlabel, dstmax)

	print("cp -alT {0} {1}.0".format(srcdirs[-1], dstlabel))
	cp_ret = os.system("cp -alT {0} {1}.0".format(srcdirs[-1], dstlabel))

	return cp_ret
