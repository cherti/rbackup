#!/usr/bin/env python3

#confdir = '/etc/newrbackup'
conffile = 'sample.conf'

import os, shutil, configparser

config = configparser.ConfigParser()
config.read(conffile)

def simple_sync(src, dst, add_args=None):

	rsync_cmd = ["rsync", "-a", "--delete", config.get('general', 'additional_rsync_args')]

	if add_args:
		rsync_cmd += [add_args]

	rsync_cmd += [src, dst]
	rsync_cmdstr = " ".join(rsync_cmd)

	# sync to target
	return os.system(rsync_cmdstr)



def backup_sync(source, backuppath, label):
	os.chdir(backuppath)

	# filter for dirs with this label
	dirs = [ d for d in os.listdir() if d.startswith(label) ]

	if len(dirs) == 0: # no backups yet, start from scratch
		os.mkdir("in_progress_{0}".format(label))
	else: # backups present, go updating
		os.system("cp -al {0}.0 in_progress_{0}".format(label))


	# prepare excludes and includes
	add_rsync_args = []

	if 'includelist' in config.options('general'):
		incl_lst = config.get('general', 'includelist')

		if os.path.exists(incl_lst):
			add_rsync_args += ['--include-from=' + config.get('general', 'includelist')]

	if 'excludelist' in config.options('general'):
		excl_lst = config.get('general', 'includelist')

		if os.path.exists(excl_lst):
			add_rsync_args += ['--exclude-from=' + config.get('general', 'excludelist')]


	# now SYNC!!!
	ret_rsync = simple_sync( source, "in_progress_{0}".format(label), add_args=add_rsync_args)


	if ret_rsync == 0: # only reorder if rsync finished successfully

		#reorder backups
		backupcount = int(config.get('labels', label))

		if len(dirs) >= backupcount: # we need to delete the last one
			dirname = '{0}.{1}'.format(label, backupcount-1)
			shutil.rmtree(dirname)
			dirs.remove(dirname)

		# now move everything by one
		for i in range(len(dirs)-1, -1, -1):
			src = '{0}.{1}'.format(label, i)
			dst = '{0}.{1}'.format(label, i+1)
			shutil.move(src, dst)

		#finally move the synced one to the start
		src = 'in_progress_{0}'.format(label)
		dst = '{0}.0'.format(label)
		shutil.move(src, dst)

	return ret_rsync
