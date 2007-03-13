all:

install:
	@mkdir -p /usr/share/esdk/lib
	@cp *.py  /usr/share/esdk/lib
	@mkdir -p /usr/share/esdk/platforms
	@cp -a donley /usr/share/esdk/platforms/
	@cp project_builder /usr/sbin/

clean:
	rm -f *.pyc
	find -name \*~ -exec rm -f {} \;
