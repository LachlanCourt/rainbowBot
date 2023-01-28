build:
	docker build -t rainbowbot:generic .
run:
	docker run --env-file .env rainbowbot:generic python3 bot.py
