PNAME = netbook-lpia-moblin2

fsetsdir = ${pkgdatadir}/platforms/${PNAME}/fsets
fsets_DATA = \
	fsets/base.fset

bindir = ${pkgdatadir}/platforms/${PNAME}/post-install-scripts
bin_SCRIPTS = \
	post-install-scripts/001_setup.sh \
	post-install-scripts/005_network.sh \
	post-install-scripts/010_desktop.sh 

yumreposdir = ${pkgdatadir}/platforms/${PNAME}/yum.repos.d
yumrepos_DATA = \
	yum.repos.d/Moblin.repo

platformdir = ${pkgdatadir}/platforms/${PNAME}
platform_DATA = \
	../common-yum/exclude \
	../common-yum/install.sh \
	../common-yum/nand.sh\
	fstab

initramfsdir = ${pkgdatadir}/platforms/${PNAME}/initramfs
initramfs_SCRIPTS = \
	../common-yum/initramfs/disk \
	../common-yum/initramfs/init \
	../common-yum/initramfs/init.1 \
	../common-yum/initramfs/nand \
	../common-yum/initramfs/usb
