
"""
can create and remove lockfiles

"""

import os, sys

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

			if procname == sys.argv[0].strip() and pid == str(os.getpid()):
				return True
			else:
				print('removing stale lockfile')
				self.remove()
				return False
		else:
			return False
