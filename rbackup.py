#!/usr/bin/env python3

conffile = 'sample.conf'

import syncer, configparser, sys, os, checkconf, lockfile, time, argparse

#
# preparations
#

conferrors = checkconf.checkconfiguration(conffile)

config = configparser.ConfigParser()
config.read(conffile)

lock = lockfile.Lockfile(config.get('general', 'lockfile'))

#
# handle commandline-args
#

parser = argparse.ArgumentParser(description='some dummy description')

# choose Backup or Duplicate
parser.add_argument('-b', '--backup', action='store_true', default=False, dest='backup')
parser.add_argument('-d', '--duplicate', action='store_true', default=False, dest='dupl')

# specify whether the run shall be stored in case of disk not becoming available
parser.add_argument('-s', action='store_true', default=False, dest='store')

# specify targetdisk via section ('to')
parser.add_argument('-t', '--to', action='store', default=None, dest='to')

# specify sourcedisk for duplication ('from')
parser.add_argument('-f', '--from', action='store', default=None, dest='fro')

# specify label (to use in case of backup)
parser.add_argument('-l', '--label', action='store', default=None, dest='label')

args = parser.parse_args(sys.argv[1:])


# check whether args are such that we can work with them
checkconf.checkargs(args, config)


if args.backup:
	print('making backup to label {0} on device {1}'.format(args.label, args.to))
elif args.to not in ['labels', 'general']:
	print('duplicating backup from {0} to device {1}'.format(args.fro, args.to))


# parse configuration
def getconf(sec):
	"""
	parse configuration for given section and validate before returning
	"""

	#pre
	try: pre = config.get(sec, 'pre')
	except configparser.NoOptionError: pre = ''

	if pre != '' and not os.path.exists(pre):
		print('path to pre-script for {0} is invalid, ignoring'.format(sec))
		pre = ''


	#post
	try: post = config.get(sec, 'post')
	except configparser.NoOptionError: post = ''

	if post != '' and not os.path.exists(post):
		print('path to post-script for {0} is invalid, ignoring'.format(sec))
		post = ''


	#backupdir
	#parse
	try: path = config.get(sec, 'backupdir')
	except configparser.NoOptionError:
		print('no backupdir specified', file=sys.stderr)
		sys.exit(3)


	return pre, post, path


#
# everything fine, time to do some magic!
#

def prepare(prescript, path):
	"""
	prepare by using pre-script and check if everything seems ok
	"""

	preret = os.system(prescript)

	if preret != 0:
		if preret == 32256:
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('prescript {0} exited nonzero, exiting myself'.format(prescript), file=sys.stderr)
		sys.exit(6)
	else:
		#check validity of mountpoint/backuppath
		if not os.path.exists(path):
			print('invalid backupdir', file=sys.stderr)
			sys.exit(4)


while lock.isValid(): # wait for other processes to terminate
	time.sleep(30)

lock.create()

if args.backup: # system2backup
	pre, post, dst = getconf(args.to)
	src = config.get('general', 'backupsource')

	prepare(pre, dst)

	# decide whether we want to sync a backup or to copy one
	labels = config.options('labels')
	curr_label_index = labels.index(args.label)

	if curr_label_index == 0: # first label, sync from source
		rsync_ret = syncer.backup_sync(src, dst, args.label)

		if rsync_ret != 0:
			print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)
	else: # later label, sync from previous one

		prev_label = labels[curr_label_index-1]
		cp_ret = syncer.backup_copy(dst, prev_label, args.label)
		if cp_ret != 0:
			print('cp finished with errors: exit code {0}'.format(cp_ret), file=sys.stderr)


	# tidy up devices afterwards
	postret = os.system(post)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('post-script finished with errors: exit code {0}'.format(postret), file=sys.stderr)

else: # duplicate backup, args.d
	srcpre, srcpost, src = getconf(args.fro)
	dstpre, dstpost, dst = getconf(args.to)

	prepare(srcpre, src)
	prepare(dstpre, dst)

	print()
	rsync_ret = syncer.simple_sync(src, dst)

	if rsync_ret != 0:
		print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)


	postret = os.system(srcpost)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute post-script of device {0}; is it executable?'.format(args.fro), file=sys.stderr)

		print('post-script for device {0} finished with errors: exit code {1}'.format(args.fro, postret), file=sys.stderr)

	postret = os.system(dstpost)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute post-script of device {0}; is it executable?'.format(args.to), file=sys.stderr)

		print('post-script for device {0} finished with errors: exit code {1}'.format(args.to, postret), file=sys.stderr)


lock.remove()
