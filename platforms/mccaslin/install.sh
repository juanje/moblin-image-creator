#!/bin/bash

echo -e '\nDeleting Partition Table on /dev/sda...\n'
dd if=/dev/zero of=/dev/sda bs=512 count=2
sync

echo -e 'Creating New Partiton Table on /dev/sda...\n'
fdisk /dev/sda <<EOF
n
p
1
1
+1024M
n
p
2


a
1
w
EOF

sync

echo -e 'Formatting /dev/sda1 w/ ext2...\n'
mkfs.ext2 /dev/sda1
sync

echo -e 'Formatting /dev/sda2 w/ ext3...\n'
mkfs.ext3 /dev/sda2
sync

echo -e 'Mounting partitions...\n'
mkdir /tmp/boot
mount -o loop -t squashfs /container/bootfs.img /tmp/boot

mount /dev/sda2 /mnt
mkdir /mnt/boot
mount /dev/sda1 /mnt/boot

echo -e 'Copying system files onto hard disk drive...\n'
cp -v /container/rootfs.img /mnt/boot
cp -av /tmp/boot /mnt

/usr/sbin/grub-install --root-directory=/mnt /dev/sda

echo -e 'Unmounting partitions...\n'
umount /mnt/boot
umount /mnt
umount /tmp/boot

echo "Installation complete.  Unplug the USB key and repower the device."
while true; do
	sleep 100
done

