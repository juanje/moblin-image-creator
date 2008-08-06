PNAME = mccaslin-lpia-fedora

fsetsdir = ${pkgdatadir}/platforms/${PNAME}/fsets
fsets_DATA = \
	fsets/base.fset

yumreposdir = ${pkgdatadir}/platforms/${PNAME}/yum.repos.d
yumrepos_DATA = \
	yum.repos.d/fedora-development.repo \
	yum.repos.d/fedora-updates-testing.repo \
	yum.repos.d/fedora-updates.repo \
	yum.repos.d/fedora.repo

platformdir = ${pkgdatadir}/platforms/${PNAME}
platform_DATA = \
	../common-yum/exclude \
	../common-yum/install.sh \
	../common-yum/nand.sh

initramfsdir = ${pkgdatadir}/platforms/${PNAME}/initramfs
initramfs_SCRIPTS = \
	../common-yum/initramfs/disk \
	../common-yum/initramfs/init \
	../common-yum/initramfs/init.1 \
	../common-yum/initramfs/nand \
	../common-yum/initramfs/usb
