#!/usr/bin/env python3

conffile = 'sample.conf'

import syncer, configparser, sys, os, checkconf, lockfile, time, argparse
import storer


"""
 preparations
"""


# check configuration validity
checkconf.checkconfiguration(conffile)

# parse configuration
config = configparser.ConfigParser()
config.read(conffile)

# prepare lockfile
lock = lockfile.Lockfile(config.get('general', 'lockfile'))


# now parse commandline-args

parser = argparse.ArgumentParser(description='some dummy description')
# choose Backup or Duplicate
parser.add_argument('-b', '--backup', action='store_true', default=False, dest='backup')
parser.add_argument('-d', '--duplicate', action='store_true', default=False, dest='dupl')

parser.add_argument('-s', '--store', action='store_true', default=False, dest='store') # specify whether the run shall be stored in case of disk not becoming available
parser.add_argument('--no-pending', action='store_true', default=False, dest='nopending') # specify whether the stored jobs shall NOT be run before this one

parser.add_argument('-t', '--to', action='store', default=None, dest='to') # specify targetdisk via section ('to')
parser.add_argument('-f', '--from', action='store', default=None, dest='fro') # specify sourcedisk for duplication ('from')
parser.add_argument('-l', '--label', action='store', default=None, dest='label') # specify label (to use in case of backup)

parser.add_argument('-q', '--quiet', action='store_true', default=False, dest='quiet') # no output to stderr for most errors

args = parser.parse_args(sys.argv[1:])

# check whether args are such that we can work with them
checkconf.checkargs(args, config)

if not args.nopending:
	currjob = storer.jobstring(args)
	storer.run_stored(config.get('general', 'pendingfile', skip_job=currjob)

def rbackup_exit(exitcode):
	if args.store:
		storer.store(args, config.get('general', 'pendingfile'))
	sys.exit(exitcode)


# giving status update what will be done (for user or logs)
if args.backup:
	print('making backup to label {0} on device {1}'.format(args.label, args.to))
elif args.to not in ['labels', 'general']:
	print('duplicating backup from {0} to device {1}'.format(args.fro, args.to))


if args.quiet: # if the user wanted to have a quiet run
	sys.stderr = sys.stdout # everything written to stderr goes to stdout instead


# parse configuration
def getconf(sec):
	"""
	parse configuration for given section and validate before returning
	"""

	#parsing pre
	try: pre = config.get(sec, 'pre') # returns pre if pre exists in conf
	except configparser.NoOptionError: pre = '' # else keep empty

	# now validate if we can find the potential pre-script
	if pre != '' and not os.path.exists(pre):
		print('path to pre-script for {0} is invalid, ignoring'.format(sec))
		pre = ''


	#parsing post
	try: post = config.get(sec, 'post') # returns post if post exists in conf
	except configparser.NoOptionError: post = '' # else keep empty

	# now validate if we can find the potential post-script
	if post != '' and not os.path.exists(post):
		print('path to post-script for {0} is invalid, ignoring'.format(sec))
		post = ''


	#backupdir
	#parse
	try: path = config.get(sec, 'backupdir')
	except configparser.NoOptionError:
		print('no backupdir specified', file=sys.stderr)
		rbackup_exit(3) # exit, without backupdir there is no point in continuing


	return pre, post, path


#
# everything fine, time to do some magic!
#

def prepare(prescript, path):
	"""
	prepare by using pre-script and check if everything seems ok
	"""

	preret = os.system(prescript) # make specified preparations

	if preret != 0:
		if preret == 32256: # no-permission-error
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('prescript {0} exited nonzero, exiting as well'.format(prescript), file=sys.stderr)
		rbackup_exit(6) # pre exited nonzero, so we assume not to have device, no point in continuing
	else:
		#check validity of mountpoint/backuppath
		if not os.path.exists(path):
			print('invalid backupdir', file=sys.stderr)
			rbackup_exit(4) # without valid backupdir there is no point in continuing


while lock.isValid(): # wait for other processes of this kind to terminate via block
	time.sleep(30)

# now create lock to let other processes know that we want to do a backup
lock.create()

if args.backup: # we want to create a backup
	pre, post, dst = getconf(args.to) # get configuration
	src = config.get('general', 'backupsource') # get source-directory

	prepare(pre, dst)

	# decide whether we want to sync a entirely new backup or to copy one to a later stage
	labels = config.options('labels') # get list of labels from config
	curr_label_index = labels.index(args.label) # get the index of the current label in list


	if curr_label_index == 0: # it's the first label, so sync a new backup
		rsync_ret = syncer.backup_sync(src, dst, args.label)

		if rsync_ret != 0:
			print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)

	else: # higher-order label, copy a backup into a later stage
		prev_label = labels[curr_label_index-1] # get the previous label to copy from

		cp_ret = syncer.backup_copy(dst, prev_label, args.label) # ACTION!!!

		if cp_ret != 0:
			print('cp finished with errors: exit code {0}'.format(cp_ret), file=sys.stderr)


	# tidy up devices afterwards
	postret = os.system(post)

	if postret != 0:
		if preret == 32256: # no-permission-error
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('post-script finished with errors: exit code {0}'.format(postret), file=sys.stderr)

else: # duplicate backup to another disk, args.dupl == True

	# get configuration
	srcpre, srcpost, src = getconf(args.fro)
	dstpre, dstpost, dst = getconf(args.to)

	prepare(srcpre, src)
	prepare(dstpre, dst)

	rsync_ret = syncer.simple_sync(src, dst)

	if rsync_ret != 0:
		print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)


	# tidy up afterwards

	postret = os.system(srcpost)

	if postret != 0:
		if preret == 32256: # no-permission-error
			print('no permission to execute post-script of device {0}; is it executable?'.format(args.fro), file=sys.stderr)

		print('post-script for device {0} finished with errors: exit code {1}'.format(args.fro, postret), file=sys.stderr)

	# tidy up afterwards
	postret = os.system(dstpost)

	if postret != 0:
		if preret == 32256: # no-permission-error
			print('no permission to execute post-script of device {0}; is it executable?'.format(args.to), file=sys.stderr)

		print('post-script for device {0} finished with errors: exit code {1}'.format(args.to, postret), file=sys.stderr)


lock.remove() # finally release lock when done
