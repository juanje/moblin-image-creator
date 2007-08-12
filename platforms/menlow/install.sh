#!/bin/bash


#find install disk
while true; do
      for driver in 'hda' 'hdb' 'sda' 'sdb'; do
        echo "checking driver $driver"
        if [ -e /sys/block/$driver/removable ]; then
           if [ "$(cat /sys/block/$driver/removable)" = "0" ]; then
              echo "found harddisk at $driver"
              found="yes"
              break
           fi
         fi
      done
      if [ "$found" = "yes" ]; then
        break;
      fi
      /bin/sleep 5
done
echo "will install to $driver"


echo -e "\nDeleting Partition Table on /dev/$driver...\n"
dd if=/dev/zero of=/dev/$driver bs=512 count=2
sync

echo -e "Creating New Partiton Table on /dev/$driver ...\n"
fdisk /dev/$driver <<EOF
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

echo -e "Formatting /dev/${driver}1 w/ ext2...\n"
mkfs.ext2 /dev/${driver}1
sync

echo -e "Formatting /dev/${driver}2 w/ ext3...\n"
mkfs.ext3 /dev/${driver}2
sync

echo -e 'Mounting partitions...\n'
mkdir /tmp/boot
mount -o loop -t squashfs /tmp/install/bootfs.img /tmp/boot

mount /dev/${driver}2 /mnt
mkdir /mnt/boot
mount /dev/${driver}1 /mnt/boot

echo -e 'Copying system files onto hard disk drive...\n'
cp -v /tmp/install/rootfs.img /mnt/boot
cp -av /tmp/boot /mnt

/usr/sbin/grub-install --root-directory=/mnt /dev/${driver}

echo -e 'Unmounting partitions...\n'
umount /mnt/boot
umount /mnt
umount /tmp/boot
umount /tmp/install

echo -e '\n\n\nInstall Finished!\n\n'
echo -e 'Disconnect the USB-Key and power cycle the device\n'

while true; do
    sleep 100
done


