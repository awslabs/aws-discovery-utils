echo 'Stopping containers...'

docker-compose down

echo 'Looking for stuff to clean...'

if [ $(docker ps | grep -E 'aws_*' | wc -l) -ne 0 ]; then

echo '\n- Found containers to delete'

docker rm -f -v $(docker ps | grep -E 'aws_*' | awk '{print $1}')

fi

if [ $(docker images -q | awk '{print $3, $1}' | grep -E 'aws_*' | wc -l) -ne 0 ]; then

echo '\n- Found images to delete'

docker rmi -f $(docker images -q | awk '{print $3, $1}' | grep -E 'aws_*' | awk '{print $1}')

fi

if [ $(docker volume ls | awk '{print $2}' | grep 'aws_*' | wc -l) -ne 0  ]; then

echo '\n- Found volumes to delete'

docker volume rm $(docker volume ls | awk '{print $2}' | grep 'aws_*')

fi

if [ $(docker network ls | grep -E 'aws_default' | wc -l) -ne 0 ]; then

echo '\n- Found networks to delete'

docker network prune -f

fi