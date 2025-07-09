install:
	./bin/dev/docker-exec.sh poetry install

remove:
	./bin/dev/docker-remove.sh

build:
	./bin/dev/docker-build.sh

build-m1:
	./bin/dev/docker-build-m1.sh

start:
	./bin/dev/docker-start.sh

ssh:
	./bin/dev/docker-ssh.sh

stop:
	./bin/dev/docker-stop.sh

notebook:
	./bin/dev/notebook-start.sh

ipython:
	./bin/dev/ipython-start.sh

server:
	./bin/dev/docker-exec.sh ./bin/dev/webserver-start.sh

dagster:
	./bin/dev/dagster-start.sh


curl:
	./bin/dev/curl.sh

lint:
	./bin/dev/docker-exec.sh poetry run black src &&\
	./bin/dev/docker-exec.sh poetry run flake8 --max-line-length=90 src &&\
	./bin/dev/docker-exec.sh poetry run pydocstyle --convention=google &&\
	./bin/dev/docker-exec.sh poetry run mypy --follow-imports=skip --ignore-missing-imports --disallow-untyped-defs

test:
	./bin/dev/docker-exec.sh poetry run pytest -s

streamlit_uc:
	./bin/dev/docker-exec.sh ./bin/dev/streamlit-start.sh src/unit_commitment_01/streamlit_app.py

streamlit_vpp:
	./bin/dev/docker-exec.sh ./bin/dev/streamlit-start.sh src/vpp_example_01/streamlit_app.py


streamlit_kill:
	@if docker exec electric-grid-balancing ps aux | grep streamlit | grep -v grep > /dev/null; then \
		docker exec electric-grid-balancing bash -c "ps aux | grep streamlit | grep -v grep | awk '{print \$$2}' | xargs kill -9"; \
		echo "Streamlit processes killed inside container"; \
	else \
		echo "No streamlit processes found in container"; \
	fi

clean_pycache:
	find . -type d -name "__pycache__" -exec rm -rf {} \;
