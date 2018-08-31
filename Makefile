ARGS ?= ""

up: docker_up

build: docker_build up

clean:
	./clean.sh

docker_up:
	docker-compose up -d --remove-orphans

docker_build:
	docker-compose build

bash:
	docker-compose exec master bash

convert:
	docker-compose exec master bin/spark-submit /code/convert_csv.py $(ARGS)

export:
	docker-compose exec master python /code/convert_csv.py $(ARGS)

files:
	docker-compose exec master python /code/files.py $(ARGS)


.PHONY: up build clean docker_up docker_build bash convert export files
