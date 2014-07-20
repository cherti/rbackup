#!/usr/bin/env python3

#confdir = '/etc/newrbackup'
conffile = 'test.conf'

import os, shutil, configparser

config = configparser.ConfigParser()
config.read(conffile)

def sync(source, backuppath, label):
	os.chdir(backuppath)

	# filter for dirs with this label
	dirs = [ d for d in os.listdir() if d.startswith(label) ]

	if len(dirs) == 0: # no backups yet, start from scratch
		os.mkdir("in_progress_{0}".format(label))
	else: # backups present, go updating
		os.system("cp -al {0}.0 in_progress_{0}".format(label))


	#os.system("rsync -a --delete --exclude-from excludelist / {0}".format(targetpath))
	rsync_cmd = ["rsync", "-a", "--delete"]

	# think of a way of implementing the exclude-list (either separate file or within config)

	rsync_cmd += [source, "in_progress_{0}".format(label)]

	# sync to target
	rsync_cmdstr = " ".join(rsync_cmd)

	ret_rsync = os.system(rsync_cmdstr)

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
