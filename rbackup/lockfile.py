
"""
can create and remove lockfiles

"""

import os, sys, subprocess

class Lockfile(object):

	def __init__(self, path):
		self.path = path


	def create(self):
		with open(self.path, "w") as f:
			print(sys.argv[0], os.getpid(), file=f)


	def remove(self):
		if os.path.exists(self.path):
			os.remove(self.path)


	def isValid(self):
		if os.path.exists(self.path):
			with open(self.path, "r") as f:
				procname, pid = f.read().strip().split()


			locked_pids = subprocess.getoutput('pgrep {0}'.format(procname)).split('\n')

			if pid in locked_pids:  # the process setting the pidfile is still running
				return True
			else:
				print('removing stale lockfile')
				self.remove()
				return False
		else:
			return False


	def is_owned(self):
		"""
		check if the lockfile set is ours
		to avoid race-condition-fails if
		two processes of this kind run
		"""
		if os.path.exists(self.path):
			with open(self.path, "r") as f:
				procname, pid = f.read().strip().split()

			if procname == sys.argv[0] and pid == str(os.getpid()):
				return True
			else:
				return False
		else:
			return False
