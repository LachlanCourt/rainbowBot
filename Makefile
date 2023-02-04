.PHONY: build run clean push pull

build:
	docker build -t rainbowbot:build .
run:
	docker run --env-file .env rainbowbot:build python3 bot.py
clean:
	docker container rm -f $(shell docker container ls -aq)
push:
	docker tag ghcr.io/${USER_REPOSITORY}/rainbowbot:latest rainbowbot:build && docker push ghcr.io/${USER_REPOSITORY}/rainbowbot:latest
pull:
	docker pull ghcr.io/${USER_REPOSITORY}/rainbowbot:latest && docker tag ghcr.io/${USER_REPOSITORY}/rainbowbot:latest rainbowbot:build