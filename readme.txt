This tool is ment to provide an automatizable backup helper.

The way it works is by distributing copies of a root folder
onto several backup devices.
To do so there are two things that must be specified:
first, the backup-devices. These are specified by a name by
which these devices can be adressed on invocation.
Each device has three properties:
- a directory to backup to (backupdir)
- a pre-script (pre)
- a post-script (post)

The backupdir specifies where the backup is stored.
The pre- and post-script are run before and after the backup
started.
They are ment to mount or umount the backup-devices properly
and have to be executable.
The job of the scripts are to do everything that needs to be
done to make the backup-device available at the point
specified, success is specified via return value.

Therefore a pre-script has to mount a device and run all
checks to ensure that everything is the way it has to be
to start a backup.
If this is the case, the script shall return 0, otherwise
the script shall return nonzero.
The backup is only started if the pre-script returns 0.

pre- and post-scripts can be specified or left out, if no
scripts are specified everything will be assumed to be fine.


The second thing to be specified is the list of labels:

Backups are organized in labels. In the backup-directory,
there are folders like

  label.0 label.1 label.2

where label.0 is the newest backup. Upon backup, all folders
are shifted backwards by one number:

  label.1 label.2 label.3

and a new backup is created as "label.0".
If the number of backupfolders exceeds the number specified
for that label in the "labels"-section in the configuration,
the oldest folder is removed.
The newest backup is synced from the backupsource for the
upmost label, each lower label in the list recruits its new
backups from the oldest one of the label above it.


rbackup can be run using two ways:
Backup and Duplicate.
The backupmode performs the backup-logic described above,
the duplicationmode duplicates a backupdir of one device
to the backupdir of another device.


Backups that fail, e.g. because the pre-script exits non-
zero, e.g. because the device is not present, can be stored
to be rerun later. Unless specified otherwise, rbackup
checks for stored runs before running the actual triggered
job and tries to run them beforehand.

The provided PKGBUILD is intended for building by cloning
and calling makepkg in this very directory.


This software is licensed under the GNU General Public License v3.
