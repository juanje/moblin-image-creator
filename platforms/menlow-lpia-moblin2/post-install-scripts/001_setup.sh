#!/bin/sh

#create the /etc/shadow file
/usr/sbin/pwconv

#creat the root user
/usr/bin/passwd -d root
#create moblin user
getent passwd moblin > /dev/null || useradd moblin
/usr/bin/passwd -d moblin
cat > /etc/Moblin2-Release << EOF
#Name-Kernel-Arch-Rel
Moblin-2.6.27-lpia-2
EOF

# creat the grub config file
comment="#It is created by update-grub"
args='root=/dev/sda2'
grub_config_file="/boot/grub/grub.conf"
grub_config_bak_file="/boot/grub/grub.conf.bak"

[ -e ${grub_config_file} ] && mv ${grub_config_file} ${grub_config_bak_file}

echo ${comment} > ${grub_config_file}

kerns=$(ls /boot/vmlinuz* ) > /dev/null 2>&1

for kern in ${kerns}
do
   kern=$(echo ${kern} | sed -e 's/\/boot//g')
   echo "add ${kern} to grub config file"
   initrd=$(echo ${kern} | sed -e 's/vmlinuz/initrd\.img/g')
   /sbin/grubby --add-kernel=${kern} --args=${args} -c ${grub_config_file}  --grub --title="moblin2 ${kern}"
done

