
up: docker_up

build: docker_build up

clean:
	./clean.sh

docker_up:
	docker-compose up -d --remove-orphans

docker_build:
	docker-compose build

.PHONY: up build clean docker_up docker_build
