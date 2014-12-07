from distutils.core import setup

setup(
    name='RBackup',
    version='1.0',
    author='Jonas Große Sundrup',
    author_email='cherti@letopolis.de',
    packages=['rbackup'],
    scripts=['bin/rbackup'],
    url='https://github.com/cherti/rbackup',
    license='license.txt',
    description='rsync-based backup-tool',
    long_description=open('readme.txt').read(),
)
