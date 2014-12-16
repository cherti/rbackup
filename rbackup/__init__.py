import subprocess, threading


def run_cmd(cmd, timeout=0):

	p = subprocess.Popen(cmd, shell=True)

	# start thread that's waiting for p to terminate
	thr = threading.Thread(target=lambda: p.communicate())
	thr.start()

	if timeout <= 0:  # join until it terminates
		thr.join()
	else:  # join just for a certain timeout
		thr.join(timeout)

		if thr.isAlive():
			p.terminate()

			# wait another timeout for process to be terminated
			thr.join(timeout)

			# if it is still alive now, kill it with fire!
			if thr.isAlive():
				p.kill()

	p.communicate()

	return p.returncode
