
run:
	@echo "please open http://localhost:8081/"
	cd demo && PYTHONPATH=..:. twistd -n web --resource-script=server.rpy -p tcp:8081
