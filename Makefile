.PHONY: build run clean push pull

build:
	docker build -t rainbowbot:build .
run:
	docker run --env-file .env rainbowbot:build python3 bot.py
clean:
	docker container rm -f $(shell docker container ls -aq)
push:
	docker tag rainbowbot:build ghcr.io/${USER_REPOSITORY}:latest && docker push ghcr.io/${USER_REPOSITORY}:latest
pull:
	docker pull ghcr.io/${USER_REPOSITORY}:latest && docker tag ghcr.io/${USER_REPOSITORY}:latest rainbowbot:build