.PHONEY: env env-notebook docker-build

SHELL:=bash

env:
	@if [ -d "yt-env" ]; then \
		echo "yt-env directory already exists"; \
	else \
		echo "yt-env is being created"; \
		python -m venv yt-env; \
	fi
	source yt-env/bin/activate
	pip install -r requirements.txt
	pip install torch --index-url https://download.pytorch.org/whl/cpu

env-notebook: env
	python -m ipykernel install --user --name=yt-venv-jupyter

docker-build:
	docker build . \
	-t youtube-data-project:latest \
	--build-arg YOUTUBE_API_KEY \
	--build-arg SERVICE_ACCOUNT_SECRET_KEY

docker-run:
	docker run youtube-data-project:latest