#!/usr/bin/env python3

conffile = 'sample.conf'

import syncer, configparser, sys, os, checkconf, lockfile, time

#
#
# preparations
#

conferrors = checkconf.checkconfiguration(conffile)

if conferrors:
	sys.exit(5)
	# error announcement already made within checkconf

config = configparser.ConfigParser()
config.read(conffile)

lock = lockfile.Lockfile(config.get('general', 'lockfile'))

# properly interpret cmdline-args
if len(sys.argv) > 2:
	section = sys.argv[1]
	label = sys.argv[2]
	if label not in config.options('labels'):
		print('unknown label {0}'.format(label))
		sys.exit(1)
elif len(sys.argv) > 1:
	section = sys.argv[1]
	if section == 'main':
		print('missing label for section main', file=sys.stderr)
		sys.exit(1)
else:
	print('not enough information', file=sys.stderr)
	sys.exit(1)


# print mark

if section == 'main' and label:
	print('making backup to {0} on {1}'.format(label, section))
elif section not in ['main', 'labels', 'general']:
	print('duplicating backup to {0}'.format(section))


# parse configuration
def getconf(sec):
	"""
	parse configuration for given section and validate before returning
	"""

	#pre
	try: pre = config.get(sec, 'pre')
	except configparser.NoOptionError: pre = ''

	if not os.path.exists(pre):
		print('pre-script for {0} is invalid, ignoring')
		pre = ''


	#post
	try: post = config.get(sec, 'post')
	except configparser.NoOptionError: post = ''

	if not os.path.exists(post):
		print('post-script for {0} is invalid, ignoring')
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

def prepare(prescript):
	"""
	prepare by using pre-script and check if everything seems ok
	"""

	preret = os.system(pre)

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


while lock.isValid():
	time.sleep(30)

lock.create()

if section == 'main': # system2backup
	pre, post, dst = getconf('main')
	src = config.get('general', 'backupsource')

	prepare(pre)

	rsync_ret = syncer.backup_sync(src, dst, label)

	if rsync_ret != 0:
		print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)

	postret = os.system(post)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('post-script finished with errors: exit code {0}'.format(postret), file=sys.stderr)

elif not section in ['main', 'labels', 'general']: # duplicate backup
	mainpre, mainpost, src = getconf('main')
	secpre, secpost, dst = getconf(section)

	prepare(mainpre)
	prepare(secpre)

	rsync_ret = syncer.simple_sync(src, dst)

	if rsync_ret != 0:
		print('rsync finished with errors: exit code {0}'.format(rsync_ret), file=sys.stderr)


	postret = os.system(mainpost)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('post-script for section main finished with errors: exit code {0}'.format(postret), file=sys.stderr)

	postret = os.system(secpost)

	if postret != 0:
		if preret == 32256:
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('post-script for section {0} finished with errors: exit code {1}'.format(section, postret), file=sys.stderr)


lock.remove()
