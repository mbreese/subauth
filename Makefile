all: init
init:
	./install.sh
clean:
	find . -name '*.pyc' -exec rm \{\} \;
	rm -rf ./venv

