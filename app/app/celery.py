# celery.py
from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

# Установка переменной окружения "DJANGO_SETTINGS_MODULE" для Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

# Создание объекта Celery и настройка
app = Celery('app')

# Использование файла настроек Django для конфигурации Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Загрузка задач из всех приложений Django
app.autodiscover_tasks()
