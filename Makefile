VENV ?= .venv

install:
	pip install .

$(VENV):
	virtualenv $(VENV)

start-env: $(VENV)
	. .venv/bin/activate

run: start-env
	@echo "please open http://localhost:8081/"
	cd demo && PYTHONPATH=..:. twistd \
	-n web --resource-script=server.rpy -p tcp:8081

uninstall:
	-pip uninstall txBrowserID
	rm -rf ./build
