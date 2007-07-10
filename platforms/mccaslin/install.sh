#!/bin/bash

echo -e '\nDeleting Partition Table on /dev/hda...\n'
dd if=/dev/zero of=/dev/hda bs=512 count=2
sync

echo -e 'Creating New Partiton Table on /dev/hda...\n'
fdisk /dev/hda <<EOF
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

echo -e 'Formatting /dev/hda1 w/ ext2...\n'
mkfs.ext2 /dev/hda1
sync

echo -e 'Formatting /dev/hda2 w/ ext3...\n'
mkfs.ext3 /dev/hda2
sync

echo -e 'Mounting partitions...\n'
mkdir /tmp/install
mount /dev/sda /tmp/install

mkdir /tmp/boot
mount -o loop -t squashfs /tmp/install/bootfs.img /tmp/boot

mount /dev/hda2 /mnt
mkdir /mnt/boot
mount /dev/hda1 /mnt/boot

echo -e 'Copying system files onto hard disk drive...\n'
cp -v /tmp/install/rootfs.img /mnt/boot
cp -av /tmp/boot /mnt

/usr/sbin/grub-install --root-directory=/mnt /dev/hda

echo -e 'Unmounting partitions...\n'
umount /mnt/boot
umount /mnt
umount /tmp/boot
umount /tmp/install

echo -e '\n\n\nInstall Finished!\n\n'
echo -e 'System shutting down!\n\n'
echo -e 'Disconnect the USB-Key when shutdown is complete and\n'
echo -e 'Reboot the system from HDD...\n\n'

sleep 10
exec init 0
