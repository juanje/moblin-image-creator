#!/bin/sh

#Networking
echo "NETWORKING=yes" >> /etc/sysconfig/network

mkdir -p /etc/sysconfig/network-scripts
cat >> /etc/sysconfig/network-scripts/ifcfg-eth0 << EOF
DEVICE=eth0
BOOTPROTO=dhcp
ONBOOT=yes
TYPE=Ethernet
EOF

