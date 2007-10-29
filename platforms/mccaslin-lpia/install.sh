#!/bin/bash

# I want us to error out if we use an undefined variable, so we will catch errors.
set -u

# Read in our config file, if it exists
if [ -f /install.cfg ]
then
    echo "Sourcing ./install.cfg"
    . /install.cfg
else
    echo "ERROR: ./install.cfg not found!"
    sleep 10
    halt
fi

#################### usplash functions start ####################################
SPLASHWRITE=0
# Determine if we have usplash_write available
type usplash_write > /dev/null 2>&1 && SPLASHWRITE=1

# Disable usplash, since we want text mode
SPLASHWRITE=0

# show the progress at status bar.
# $1 = 0-100
splash_progress(){
    splash_write "PROGRESS $1"
    return 0
}
# display the text no matter whether verbose is set or not
splash_display(){
    echo "$@"
    splash_write "TEXT-URGENT $@"
    return 0
}
# set the splash delay time
splash_delay(){
    splash_write "TIMEOUT $1"
    return 0
}
# call the usplash_write command, if enabled
splash_write(){
    if [ "${SPLASHWRITE}" -eq 1 ]
    then
        usplash_write "$@"
    fi
}
####################### usplash functions end ###############################

splash_delay 200
splash_display 'INSTALL..........'

pre_scsi_disk_number=$( ls /sys/class/scsi_disk | wc -l)
found=no
#find install disk
while true; do
      for driver in 'hda' 'hdb' 'sda' 'sdb'; do
        echo "checking driver $driver for installation target"
        if [ -e /sys/block/$driver/removable ]; then
           if [ "$(cat /sys/block/$driver/removable)" = "0" ]; then
              splash_display "found harddisk at $driver"
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

blocks=`fdisk -s /dev/${driver}`
cylinders=$((blocks*2/63/255))

splash_display "Deleting Partition Table on /dev/$driver..."
splash_delay 200
dd if=/dev/zero of=/dev/$driver bs=512 count=2
sync
splash_progress 5
splash_delay 10

splash_display "Creating New Partiton Table on /dev/$driver ..."
splash_delay 200
fdisk /dev/$driver <<EOF
n
p
1

$((boot_partition_size*1000/8192))
n
p
2

$((cylinders-(swap_partition_size*1000/8192)))
n
p
3


a
1
w
EOF

sync
splash_progress 10
splash_delay 10

splash_display "Formatting /dev/${driver}1 w/ ext2..."
splash_delay 200
mkfs.ext2 /dev/${driver}1
sync
splash_progress 20
splash_delay 10

splash_display "Formatting /dev/${driver}2 w/ ext3..."
splash_delay 200
mkfs.ext3 /dev/${driver}2
sync
splash_progress 60
splash_delay 10

splash_display "Formatting /dev/${driver}3 w/ swap..."
splash_delay 1000
mkswap /dev/${driver}3
sync
splash_progress 65
splash_delay 10

splash_display 'Mounting partitions...'
splash_delay 200
mkdir /tmp/boot
mount -o loop -t squashfs /tmp/install/bootfs.img /tmp/boot

mount /dev/${driver}2 /mnt
mkdir /mnt/boot
mount /dev/${driver}1 /mnt/boot
splash_progress 70
splash_delay 10

splash_display 'Copying system files onto hard disk drive...'
splash_delay 200
cp -v /tmp/install/rootfs.img /mnt/boot
cp -av /tmp/boot /mnt

/usr/sbin/grub-install --root-directory=/mnt /dev/${driver}
splash_progress 90
splash_delay 10

splash_display 'Unmounting partitions...'
splash_delay 200

umount /mnt/boot
umount /mnt
umount /tmp/boot
umount /tmp/install

splash_progress 95
splash_delay 10
sleep 1
splash_delay 6000
splash_display "Install Successfully"
splash_display "Unplug USB Key, System Will Reboot Automatically"

#need to call reboot --help and let file system cache hold it, since we will unplug USB disk soon, and after that, reboot command will not be accessable
#the reason why reboot still work without this is the whole "rootfs.img" is cached when it is copied to HD. But when rootfs.img become bigger and bigger the whole "rootfs.img" will not be able to fully cached (we have found this issue when creating big installation)
reboot --help > /dev/null 2>&1

while [ $pre_scsi_disk_number = $(ls /sys/class/scsi_disk | wc -l) ]
do
    sleep 1
done

splash_progress 100
splash_delay 1

reboot -f
