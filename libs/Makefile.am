python_scriptdir = ${pkgdatadir}/lib
python_script_SCRIPTS = \
	InstallImage.py \
	Mkinitrd.py \
	Platform.py \
	Project.py \
	SDK.py \
	fsets.py \
	mic_cfg.py \
	paths.py \
	pdk_utils.py

python_script_DATA = \
	moblin_apt.py \
	moblin_pkg.py \
	moblin_pkgbase.py \
	moblin_yum.py

install-data-hook:
	sed -i "s|@PATH_PREFIX@|${prefix}|g" $(DESTDIR)$(datadir)/pdk/lib/paths.py
	sed -i "s|@PATH_PKGDATADIR@|${pkgdatadir}|g" $(DESTDIR)$(datadir)/pdk/lib/paths.py
	sed -i "s|@PATH_SYSCONFDIR@|${sysconfdir}|g" $(DESTDIR)$(datadir)/pdk/lib/paths.py
	sed -i "s|@PATH_LOCALSTATEDIR@|${localstatedir}|g" $(DESTDIR)$(datadir)/pdk/lib/paths.py

