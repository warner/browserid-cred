VENV ?= .venv
CERTS ?= ./certs

install:
	pip install .

$(VENV):
	virtualenv $(VENV)

start-env: $(VENV)
	. .venv/bin/activate

$(CERTS):
	mkdir -p $(CERTS)
	openssl genrsa > $(CERTS)/privkey.pem
	openssl req -new -x509 -days 1095 \
	-key $(CERTS)/privkey.pem -out $(CERTS)/cacert.pem


run: start-env $(CERTS)
	@echo "please open http://localhost:8081/"
	cd demo && PYTHONPATH=..:. twistd \
	-n web --resource-script=server.rpy -p tcp:8081

clean:
	find {browserid,demo} -name "*.pyc" -exec rm {} \;
	rm -rf ./build $(CERTS)

uninstall: clean
	-pip uninstall txBrowserID
