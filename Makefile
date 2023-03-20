botfile := $(bot_name).yaml

replace_botconfig:
	cp src/personas/$(botfile) src/bot.yaml
	cp src/bot_envs/$(bot_name).env src/.env

docker_build: replace_botconfig
	docker build -t $(bot_name)-bot .

docker_run:
	docker run --name $(bot_name) $(bot_name)-bot

docker_stop:
	docker stop $(bot_name)-bot

docker_kill:
	docker kill $(bot_name)
	docker_prune

docker_prune:	
	docker container prune

docker_login:
	docker login $(registry_domain)

docker_push: docker_build
	docker tag $(bot_name)-bot $(image_repo):$(bot_name)-latest
	docker push $(image_repo):$(bot_name)-latest