#!/bin/sh

set -x
intltoolize --force || exit 1
aclocal -I m4 || exit 1
autoconf || exit 1
automake --add-missing --foreign || exit 1
./configure --prefix=/usr --sysconfdir=/etc --localstatedir=/var || exit 1
