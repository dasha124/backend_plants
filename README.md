Запустите проект с помощью Docker Compose:

docker-compose up -d

При необходимости выполните миграции:

python manage.py makemigrations
docker exec -it backend python manage.py migrate


Обновление проекта/первое скачивание
Если вы вносите изменения в код (например, обновляете зависимости или изменяете Dockerfile), выполните команду для пересборки контейнеров:

docker-compose up -d --build

Запустите проект с помощью Docker Compose:

docker-compose up -d
