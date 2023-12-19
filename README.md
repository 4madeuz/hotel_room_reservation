# Приложение для бронирование комнат
## Стэк технологий

-**Django Rest Framework** - основное Api, логика вывода комнат, фильтрация, управление бронями. Комнаты, доступны всем пользователям - создаются суперюзером через админку, количество гостей высчитывают сигналы в зависимости от типа кровати(делаем допущение что для комнат в хостелах, например, один тип кровати и одна кровать на комнату), в информации о комнате также отдельным полем отдаём список забронированных дат, пожалеем фронтендеров, чтоб лишнего не программировали. 


Бронь, создание доступно только зарегистрированным, просмотр, удаление(смена статуса) и изменение только для созданных. Можно забронировать только незабронированную дату.


-**Django_admin** - функционал добавления комнат, редактирования всего


-**Postgres**


-**Nginx** - poxy, дополнительно раздаёт статику, но в данном случае только для админки и OpenApi


-**Celery** - для автоматической смены статуса в зависимости от даты, пример - дата резервации совпадает с сегодняшней датой, то меняем статус заявки с Забронированной на Активный, предпологается что такс будет выполняться ежедневно


-**Redis** - как брокер для selery


-**Django Unit testing** - для упрощенния проверки, постарался пройтись по всем поставленным задачам


-**OpenApi** документация(swagger и redoc) - http://127.0.0.1:8000/swagger/


- **Автоформатеры** isort и oitnb, в качестве основного линтера flake8, но не везде следил за этим(


- **Автроризация** по jwt токену, использовал djoser, пользователей и авторизацию не менял


- **Compose** для запуска, для корректного запуска без compose нужно поменять POSTGRES_HOST в .env и CELERY_RESULT_BACKEND, CELERY_BROKER_URL в файле app/components/celery.py на localhost


# Инструкции по запуску


example_env -> .env


## запуск с compose

docker-compose up -d --build
docker-compose up

### Основные команды
Запуск тестов - docker-compose exec rooms_app  python manage.py test

Запуск тестов - docker-compose exec rooms_app  python manage.py createsuperuser