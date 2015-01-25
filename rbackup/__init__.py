import subprocess, threading, sys
from rbackup import logger


def run_cmd(cmd, timeout=0):

	logger.debug("Running command '" + cmd + '"')
	cmd = cmd.split()
	p = subprocess.Popen(cmd)

	# start thread that's waiting for p to terminate
	thr = threading.Thread(target=lambda: p.communicate())
	thr.start()

	if timeout <= 0:  # join until it terminates
		thr.join()
	else:  # join just for a certain timeout
		thr.join(timeout)

		if thr.isAlive():
			if verbosity > 1: print('terminating subprocess')
			p.terminate()

			# wait another timeout for process to be terminated
			thr.join(timeout)

			# if it is still alive now, kill it with fire!
			if thr.isAlive():
				if verbosity > 1: print('killing subprocess')
				p.kill()

	p.communicate()

	return p.returncode


def prepare(prescript, preto, path):
	"""
	prepare device by using pre-script and check if everything seems ok
	if we can't get the device up and running, exit here as there is no
	point in continuing without one of the necessary devices.
	The job is stored in the specified pendingfile if specified so when
	calling rbackup
	"""

	preret = run_cmd(prescript, preto) # make specified preparations

	if preret != 0:
		if preret == 32256: # no-permission-error
			print('no permission to execute pre-script; is it executable?', file=sys.stderr)

		print('prescript {0} exited nonzero, exiting as well'.format(prescript), file=sys.stderr)

		if config['args'].store:
			storer.store(config['args'], config['general']['pendingfile'])
		sys.exit(1)
