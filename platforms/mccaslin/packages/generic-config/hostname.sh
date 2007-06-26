#! /bin/sh
### BEGIN INIT INFO
# Provides:          hostname
# Required-Start:
# Required-Stop:
# Default-Start:     S
# Default-Stop:
# Short-Description: Set hostname.
# Description:
### END INIT INFO

PATH=/sbin:/bin

. /lib/init/vars.sh
. /lib/lsb/init-functions

do_start () {
	[ -f /etc/hostname ] && HOSTNAME="$(cat /etc/hostname)"

	# Keep current name if /etc/hostname is missing.
	[ -z "$HOSTNAME" ] && HOSTNAME="$(hostname)"

	# And set it to 'localhost' if no setting was found
	[ -z "$HOSTNAME" ] && HOSTNAME=localhost

	if [ -n "echo -n $HOSTNAME | sed -ne \"/^mobile-..../p\"" ]; then
		HOSTNAME=mobile-$(/usr/bin/md5sum <<EOF
`/sbin/ifconfig eth0 | /usr/bin/head -n 1`
EOF
)
		HOSTNAME=$(echo -n $HOSTNAME | /usr/bin/cut -b 1-10)
        fi
	[ "$VERBOSE" != no ] && log_action_begin_msg "Setting hostname to '$HOSTNAME'"
	hostname "$HOSTNAME"
	ES=$?
	[ "$VERBOSE" != no ] && log_action_end_msg $ES
}

case "$1" in
  start|"")
	do_start
	;;
  restart|reload|force-reload)
	echo "Error: argument '$1' not supported" >&2
	exit 3
	;;
  stop)
	# No-op
	;;
  *)
	echo "Usage: hostname.sh [start|stop]" >&2
	exit 3
	;;
esac
