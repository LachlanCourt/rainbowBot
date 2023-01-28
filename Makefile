build:
	docker build -t rainbowbot:generic .
run:
	docker run --env-file .env rainbowbot:generic python3 bot.py
clean:
	docker container rm -f $(shell docker container ls -aq)
push:
	docker tag ghcr.io/lachlancourt/rainbowbot:latest rainbowbot:generic && docker push ghcr.io/lachlancourt/rainbowbot:latest
pull:
	docker pull ghcr.io/lachlancourt/rainbowbot:latest && docker tag ghcr.io/lachlancourt/rainbowbot:latest rainbowbot:generic